"""Indexa fotos locais com Pose Landmarker em uma pasta nova e portátil.

Não pesquisa a internet nem baixa pesos. Use somente imagens que você pode usar.
"""

from __future__ import annotations

import argparse
import json
import sys
from contextlib import suppress
from pathlib import Path

# A execução direta precisa localizar os módulos que ficam na raiz do projeto.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from file_io import write_new_files
from pose_matching import extract_pose
from vision_runtime import VisionDependencies, load_dependencies, to_mediapipe_image

ROOT = Path(__file__).resolve().parents[1]
EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
MAX_IMAGE_SIDE = 960


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Lê as pastas, o modelo e os créditos que acompanharão as imagens."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Pasta das fotos; não recursiva.")
    parser.add_argument(
        "--output", required=True, type=Path, help="Pasta nova para imagens e catálogo."
    )
    parser.add_argument("--model", type=Path, default=ROOT / "models" / "pose_landmarker_lite.task")
    parser.add_argument(
        "--source",
        default="Imagem fornecida pelo usuário",
        help="Origem das fotos; use uma fonte verificável ao publicar.",
    )
    parser.add_argument(
        "--license",
        default="Não informada; verificar antes de redistribuir",
        help="Licença ou condição de uso das fotos.",
    )
    return parser.parse_args(argv)


def reference_from_result(
    result,
    *,
    name: str,
    width: int,
    height: int,
    source: str,
    license_name: str,
) -> dict[str, object] | None:
    """Aceita uma pessoa com pontos suficientes; não escolhe uma pessoa ao acaso."""
    if len(result.pose_landmarks) != 1:
        return None
    landmarks = result.pose_landmarks[0]
    if extract_pose(landmarks, width, height) is None:
        return None
    # Guarda os pontos e a proporção da foto para comparações futuras.
    return {
        "id": name,
        "title": name,
        "image": f"images/{name}.png",
        "source": source,
        "license": license_name,
        "width": width,
        "height": height,
        "landmarks": [
            {
                "x": float(point.x),
                "y": float(point.y),
                "visibility": float(1 if point.visibility is None else point.visibility),
                "presence": float(1 if point.presence is None else point.presence),
            }
            for point in landmarks
        ],
    }


def write_catalog(
    output_dir: Path,
    references: list[dict[str, object]],
    images: dict[str, bytes],
) -> Path:
    """Publica arquivos em uma pasta exclusiva; não sobrescreve dados existentes."""
    if not references:
        raise ValueError("Nenhuma imagem com uma pessoa e pontos suficientes foi aceita.")
    output_dir.mkdir(parents=True, exist_ok=False)
    image_dir = output_dir / "images"
    try:
        image_dir.mkdir()
        data = {
            "schema_version": 1,
            "landmark_origin": "mediapipe_pose_landmarker",
            "references": references,
        }
        # Prepara imagens e metadados antes de iniciar a gravação exclusiva.
        payloads = {image_dir / name: content for name, content in images.items()}
        payloads[output_dir / "catalog.json"] = (
            json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        ).encode("utf-8")
        write_new_files(payloads)
    except BaseException:
        for directory in (image_dir, output_dir):
            # rmdir só remove pastas vazias; arquivos alheios permanecem intactos.
            with suppress(OSError):
                directory.rmdir()
        raise
    return output_dir / "catalog.json"


def read_frame(path: Path, cv2, np):
    """Decodifica e limita o tamanho sem produzir uma dimensão igual a zero."""
    frame = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("imagem ilegível")
    height, width = frame.shape[:2]
    # Usa a mesma escala nos dois eixos para preservar a proporção do corpo.
    scale = min(1.0, MAX_IMAGE_SIDE / max(width, height))
    if scale < 1:
        size = (max(1, round(width * scale)), max(1, round(height * scale)))
        frame = cv2.resize(frame, size, interpolation=cv2.INTER_AREA)
    return frame


def _input_images(args: argparse.Namespace) -> list[Path]:
    """Valida os caminhos e lista as imagens da pasta em ordem estável."""
    if not args.input.is_dir():
        raise ValueError(f"Pasta de entrada não encontrada: {args.input}")
    if args.output.exists():
        raise FileExistsError(f"A saída já existe; escolha uma pasta nova: {args.output}")
    if not args.model.is_file():
        raise FileNotFoundError(
            "Modelo ausente. Execute: python scripts/download_models.py --only poses"
        )
    paths = sorted(
        path
        for path in args.input.iterdir()
        if path.is_file() and path.suffix.lower() in EXTENSIONS
    )
    if not paths:
        raise ValueError("A pasta não contém PNG, JPG, JPEG ou WEBP.")
    return paths


def _index_image(
    path: Path,
    name: str,
    args: argparse.Namespace,
    task,
    dependencies: VisionDependencies,
) -> tuple[dict[str, object], bytes] | None:
    """Extrai uma pose utilizável e prepara a imagem em PNG para o catálogo."""
    frame = read_frame(path, dependencies.cv2, dependencies.numpy)
    height, width = frame.shape[:2]
    result = task.detect(to_mediapipe_image(frame, dependencies))
    reference = reference_from_result(
        result,
        name=name,
        width=width,
        height=height,
        source=args.source,
        license_name=args.license,
    )
    if reference is None:
        return None
    reference["title"] = path.stem
    encoded_ok, encoded = dependencies.cv2.imencode(".png", frame)
    if not encoded_ok:
        raise ValueError("falha na codificação PNG")
    return reference, encoded.tobytes()


def build_catalog(args: argparse.Namespace) -> Path:
    """Analisa as fotos e grava um catálogo com as referências aceitas."""
    paths = _input_images(args)
    dependencies = load_dependencies()
    vision = dependencies.vision
    options = vision.PoseLandmarkerOptions(
        base_options=dependencies.tasks.BaseOptions(model_asset_path=str(args.model)),
        running_mode=vision.RunningMode.IMAGE,
        # Detectar duas pessoas permite rejeitar a cena em vez de escolher uma.
        num_poses=2,
    )
    references = []
    images = {}
    # Reutiliza o modelo nas fotos e libera seus recursos ao terminar.
    with vision.PoseLandmarker.create_from_options(options) as task:
        for index, path in enumerate(paths, 1):
            name = f"pose-{index:03d}"
            try:
                indexed_image = _index_image(path, name, args, task, dependencies)
                if indexed_image is None:
                    print(
                        f"Ignorada {path.name}: precisa de uma pessoa com torso e membros visíveis."
                    )
                    continue
                reference, image_bytes = indexed_image
                images[f"{name}.png"] = image_bytes
                references.append(reference)
                print(f"Aceita: {path.name}")
            except (OSError, ValueError, dependencies.cv2.error) as exc:
                # Uma imagem inválida não impede a análise das demais.
                print(f"Ignorada {path.name}: {exc}")
    return write_catalog(args.output, references, images)


def main(argv: list[str] | None = None) -> int:
    """Executa a indexação e apresenta o destino criado ou a falha encontrada."""
    args = parse_args(argv)
    try:
        path = build_catalog(args)
    except (OSError, ValueError, ImportError, RuntimeError) as exc:
        print(f"Não foi possível criar o catálogo: {exc}", file=sys.stderr)
        return 1
    print(f"Catálogo criado: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
