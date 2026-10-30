"""Indexa fotos locais com Pose Landmarker em uma pasta nova e portátil.

Não pesquisa a internet nem baixa pesos. Use somente imagens que você pode usar.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from file_io import write_new_files
from pose_matching import extract_pose

ROOT = Path(__file__).resolve().parents[1]
EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Pasta das fotos; não recursiva.")
    parser.add_argument("--output", required=True, type=Path, help="Pasta nova para imagens e catálogo.")
    parser.add_argument("--model", type=Path, default=ROOT / "models" / "pose_landmarker_lite.task")
    parser.add_argument("--source", default="Imagem fornecida pelo usuário",
                        help="Origem das fotos; use uma fonte verificável ao publicar.")
    parser.add_argument("--license", default="Não informada; verificar antes de redistribuir",
                        help="Licença ou condição de uso das fotos.")
    return parser.parse_args(argv)


def reference_from_result(result, *, name, width, height, source, license_name):
    """Aceita uma pessoa com pontos suficientes; não escolhe uma pessoa ao acaso."""
    if len(result.pose_landmarks) != 1:
        return None
    landmarks = result.pose_landmarks[0]
    if extract_pose(landmarks, width, height) is None:
        return None
    return {
        "id": name, "title": name, "image": f"images/{name}.png",
        "source": source, "license": license_name, "width": width, "height": height,
        "landmarks": [{"x": float(p.x), "y": float(p.y),
                       "visibility": float(1 if p.visibility is None else p.visibility),
                       "presence": float(1 if p.presence is None else p.presence)}
                      for p in landmarks],
    }


def write_catalog(output_dir, references, images):
    """Publica arquivos em uma pasta exclusiva; não sobrescreve dados existentes."""
    if not references:
        raise ValueError("Nenhuma imagem com uma pessoa e pontos suficientes foi aceita.")
    output_dir.mkdir(parents=True, exist_ok=False)
    image_dir = output_dir / "images"
    try:
        image_dir.mkdir()
        data = {"schema_version": 1, "landmark_origin": "mediapipe_pose_landmarker",
                "references": references}
        payloads = {image_dir / name: content for name, content in images.items()}
        payloads[output_dir / "catalog.json"] = (
            json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        ).encode("utf-8")
        write_new_files(payloads)
    except BaseException:
        for directory in (image_dir, output_dir):
            try:
                directory.rmdir()
            except OSError:
                pass
        raise
    return output_dir / "catalog.json"


def load_dependencies():
    import cv2
    import mediapipe as mp
    import numpy as np
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    return cv2, mp, np, python, vision


def read_frame(path, cv2, np):
    """Decodifica e limita o tamanho sem produzir uma dimensão igual a zero."""
    frame = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("imagem ilegível")
    height, width = frame.shape[:2]
    scale = min(1.0, 960 / max(width, height))
    if scale < 1:
        size = (max(1, round(width * scale)), max(1, round(height * scale)))
        frame = cv2.resize(frame, size, interpolation=cv2.INTER_AREA)
    return frame


def build_catalog(args):
    if not args.input.is_dir():
        raise ValueError(f"Pasta de entrada não encontrada: {args.input}")
    if args.output.exists():
        raise FileExistsError(f"A saída já existe; escolha uma pasta nova: {args.output}")
    if not args.model.is_file():
        raise FileNotFoundError("Modelo ausente. Execute: python scripts/download_models.py --only poses")
    paths = sorted(p for p in args.input.iterdir() if p.is_file() and p.suffix.lower() in EXTENSIONS)
    if not paths:
        raise ValueError("A pasta não contém PNG, JPG, JPEG ou WEBP.")

    cv2, mp, np, python, vision = load_dependencies()

    options = vision.PoseLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=str(args.model)),
        running_mode=vision.RunningMode.IMAGE, num_poses=2,
    )
    references, images = [], {}
    with vision.PoseLandmarker.create_from_options(options) as task:
        for index, path in enumerate(paths, 1):
            try:
                frame = read_frame(path, cv2, np)
                height, width = frame.shape[:2]
                rgb = np.ascontiguousarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                result = task.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))
                name = f"pose-{index:03d}"
                reference = reference_from_result(
                    result, name=name, width=width, height=height,
                    source=args.source, license_name=args.license,
                )
                if reference is None:
                    print(f"Ignorada {path.name}: precisa de uma pessoa com torso e membros visíveis.")
                    continue
                reference["title"] = path.stem
                ok, encoded = cv2.imencode(".png", frame)
                if not ok:
                    raise ValueError("falha na codificação PNG")
                images[f"{name}.png"] = encoded.tobytes()
                references.append(reference)
                print(f"Aceita: {path.name}")
            except (OSError, ValueError, cv2.error) as exc:
                print(f"Ignorada {path.name}: {exc}")
    return write_catalog(args.output, references, images)


def main(argv=None):
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
