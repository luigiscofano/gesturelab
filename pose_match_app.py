"""Busca uma imagem pela geometria corporal; câmera e renderização do modo posematch.

As bibliotecas de visão chegam por injeção, mantendo a importação deste módulo e
seus testes independentes de câmera, interface gráfica e modelos baixados.
"""

from __future__ import annotations

import json
import math
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core import FrameClock, pixel_point
from file_io import write_new_files
from pose_matching import (
    BODY_JOINTS,
    POSE_CONNECTIONS,
    PoseMatch,
    extract_pose,
    load_catalog,
    rank_matches,
)

ROOT = Path(__file__).resolve().parent
WINDOW = "GestureLab | Pose parecida"


@dataclass(frozen=True)
class PoseSearch:
    pose_count: int
    status: str
    candidates: tuple[PoseMatch, ...] = ()
    landmarks: Any = None


def search_result(result, width: int, height: int, references, threshold: float) -> PoseSearch:
    """Rejeita ausência, ambiguidade e pouca visibilidade antes de buscar."""
    poses = result.pose_landmarks
    if not poses:
        return PoseSearch(0, "SEM PESSOA DETECTADA")
    if len(poses) != 1:
        return PoseSearch(len(poses), "DEIXE APENAS UMA PESSOA VISIVEL")
    landmarks = poses[0]
    query = extract_pose(landmarks, width, height)
    if query is None:
        return PoseSearch(1, "MOSTRE O CORPO: OMBROS, QUADRIS E MEMBROS", landmarks=landmarks)
    candidates = tuple(rank_matches(query, references, top_k=3, max_distance=threshold))
    if not candidates:
        return PoseSearch(1, "SEM IMAGEM SUFICIENTEMENTE PARECIDA", landmarks=landmarks)
    return PoseSearch(1, "IMAGEM ENCONTRADA", candidates, landmarks)


class MatchConfirmation:
    """Exige consistência breve; nunca conserva uma imagem sem correspondência atual."""

    def __init__(self, confirm_ms: int = 180, max_gap_ms: int = 750) -> None:
        if confirm_ms < 0 or max_gap_ms <= 0:
            raise ValueError("Confirmação não negativa e intervalo máximo positivo são necessários.")
        self.confirm_ms = confirm_ms
        self.max_gap_ms = max_gap_ms
        self.key = None
        self.since_ms = 0
        self.last_ms: int | None = None

    def update(self, candidate: PoseMatch | None, timestamp_ms: int) -> PoseMatch | None:
        if self.last_ms is not None and timestamp_ms <= self.last_ms:
            raise ValueError("Timestamps da confirmação devem ser crescentes.")
        gap = self.last_ms is not None and timestamp_ms - self.last_ms > self.max_gap_ms
        self.last_ms = timestamp_ms
        if candidate is None:
            self.key = None
            return None
        key = (candidate.reference.id, candidate.mirrored)
        if gap or key != self.key:
            self.key = key
            self.since_ms = timestamp_ms
        return candidate if timestamp_ms - self.since_ms >= self.confirm_ms else None


def match_summary(search: PoseSearch, selected: PoseMatch | None, mirror: bool) -> dict:
    """A distância é geométrica, não probabilidade ou garantia de semelhança."""
    def describe(match):
        return {
            "id": match.reference.id,
            "title": match.reference.title,
            "image": str(match.reference.image_path),
            "source": match.reference.source,
            "license": match.reference.license,
            "credit": getattr(match.reference, "credit", ""),
            "distance": round(match.distance, 6),
            "mirrored_match": match.mirrored,
            "reference_display_flipped": bool(mirror) != match.mirrored,
            "joint_count": match.joint_count,
        }

    status = search.status
    if search.candidates and selected is None:
        status = "CONFIRMANDO POSE; MANTENHA A POSICAO"
    return {
        "mode": "posematch",
        "pose_count": search.pose_count,
        "status": status,
        "distance_semantics": "normalized_pose_distance_lower_is_better_not_probability",
        "display_mirrored": mirror,
        "match": describe(selected) if selected is not None else None,
        "candidates": [describe(match) for match in search.candidates],
    }


def create_pose_task(args, python, vision):
    model = args.model or ROOT / "models" / "pose_landmarker_lite.task"
    if not model.is_file():
        raise FileNotFoundError(
            f"Modelo corporal não encontrado: {model}\n"
            "Baixe com: python scripts/download_models.py --only poses"
        )
    mode = vision.RunningMode.IMAGE if args.image else vision.RunningMode.VIDEO
    options = vision.PoseLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=str(model)),
        running_mode=mode,
        num_poses=2,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
        output_segmentation_masks=False,
    )
    return vision.PoseLandmarker.create_from_options(options)


def process_pose_frame(task, frame, timestamp_ms, deps):
    cv2, mp, np, _, _ = deps
    rgb = np.ascontiguousarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    # A inferência sempre recebe a imagem original, antes do espelhamento visual.
    return task.detect(image) if timestamp_ms is None else task.detect_for_video(image, timestamp_ms)


def read_image(path: Path, cv2, np):
    try:
        image = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"Não foi possível ler a imagem: {path}") from exc
    if image is None:
        raise RuntimeError(f"Imagem inválida ou formato não suportado: {path}")
    return image


class ReferenceImageCache:
    """Mantém somente a imagem atual em memória, inclusive em galerias grandes."""

    def __init__(self, cv2, np) -> None:
        self.cv2, self.np = cv2, np
        self.path = None
        self.image = None

    def get(self, match: PoseMatch | None):
        if match is None:
            return None
        path = match.reference.image_path
        if path != self.path:
            image = read_image(path, self.cv2, self.np)
            self.path, self.image = path, image
        return self.image


def _text(canvas, text, point, cv2, color=(230, 235, 242), max_width=None):
    # As fontes Hershey não cobrem acentos; o JSON mantém os textos originais.
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode()
    max_width = max_width or canvas.shape[1] - point[0] - 12
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.48
    while text and cv2.getTextSize(text, font, scale, 1)[0][0] > max_width:
        text = text[:-4].rstrip() + "..." if len(text) > 4 else ""
    if text:
        cv2.putText(canvas, text, point, font, scale, color, 1, cv2.LINE_AA)


def fit_image(image, width: int, height: int, cv2, np):
    """Letterbox: preserva a proporção e não recorta a pose da referência."""
    box = np.full((height, width, 3), (26, 32, 42), dtype=np.uint8)
    original_height, original_width = image.shape[:2]
    ratio = min(width / original_width, height / original_height)
    size = (max(1, round(original_width * ratio)), max(1, round(original_height * ratio)))
    resized = cv2.resize(image, size, interpolation=cv2.INTER_AREA if ratio < 1 else cv2.INTER_LINEAR)
    x, y = (width - size[0]) // 2, (height - size[1]) // 2
    box[y:y + size[1], x:x + size[0]] = resized
    return box


def draw_pose_match(frame, search, selected, args, cv2, np, reference_image=None):
    camera = cv2.flip(frame, 1) if args.mirror else frame.copy()
    height, width = camera.shape[:2]
    points = {}
    for index in BODY_JOINTS:
        if search.landmarks is None or index >= len(search.landmarks):
            continue
        landmark = search.landmarks[index]
        visibility = getattr(landmark, "visibility", 1.0)
        presence = getattr(landmark, "presence", 1.0)
        visibility = 1.0 if visibility is None else visibility
        presence = 1.0 if presence is None else presence
        if (not all(math.isfinite(value) for value in (visibility, presence))
                or min(visibility, presence) < 0.5):
            continue
        if not all(math.isfinite(value) for value in (landmark.x, landmark.y)):
            continue
        if not (0 <= landmark.x <= 1 and 0 <= landmark.y <= 1):
            continue
        points[index] = pixel_point(landmark.x, landmark.y, width, height, args.mirror)
    for first, second in POSE_CONNECTIONS:
        if first in points and second in points:
            cv2.line(camera, points[first], points[second], (110, 230, 190), 3, cv2.LINE_AA)
    for point in points.values():
        cv2.circle(camera, point, 4, (245, 240, 240), -1, cv2.LINE_AA)

    left_width, right_width, panel_height = 640, 440, 400
    gap, top, bottom = 16, 76, 136
    right_x = left_width + 2 * gap
    canvas = np.full((top + panel_height + bottom, right_x + right_width + gap, 3),
                     (18, 23, 31), dtype=np.uint8)
    canvas[top:top + panel_height, gap:gap + left_width] = fit_image(
        camera, left_width, panel_height, cv2, np
    )
    _text(canvas, "GestureLab | POSE PARECIDA", (gap, 27), cv2, color=(110, 230, 190))
    _text(canvas, "Sua pose", (gap, 58), cv2)
    _text(canvas, "Imagem mais proxima no catalogo", (right_x, 58), cv2, max_width=right_width)
    summary = match_summary(search, selected, args.mirror)
    if selected is not None and reference_image is not None:
        flipped = bool(args.mirror) != selected.mirrored
        reference = cv2.flip(reference_image, 1) if flipped else reference_image
        canvas[top:top + panel_height, right_x:right_x + right_width] = fit_image(
            reference, right_width, panel_height, cv2, np
        )
        _text(canvas, selected.reference.title, (right_x, top + panel_height + 25),
              cv2, max_width=right_width)
        _text(canvas, f"Distancia: {selected.distance:.3f} | menor = mais proxima",
              (right_x, top + panel_height + 48), cv2, max_width=right_width)
        orientation = " | imagem espelhada" if flipped else ""
        _text(canvas, f"{selected.joint_count} pontos comparados{orientation}",
              (right_x, top + panel_height + 71), cv2, max_width=right_width)
        _text(canvas, f"Fonte: {selected.reference.source}",
              (right_x, top + panel_height + 94), cv2, max_width=right_width)
        credit = getattr(selected.reference, "credit", "")
        _text(canvas, f"{credit} | {selected.reference.license}".strip(" |"),
              (right_x, top + panel_height + 117), cv2, max_width=right_width)
    else:
        _text(canvas, "Aguardando pose com correspondencia", (right_x + 16, top + 180),
              cv2, max_width=right_width - 32)
        _text(canvas, "Mostre o corpo e mantenha a posicao", (right_x + 16, top + 207),
              cv2, max_width=right_width - 32)
    _text(canvas, summary["status"], (gap, top + panel_height + 25), cv2, max_width=left_width)
    _text(canvas, "Uma pessoa; enquadre ombros, quadris, bracos e pernas",
          (gap, top + panel_height + 48), cv2, max_width=left_width)
    _text(canvas, "Busca local por geometria; distancia nao e probabilidade",
          (gap, top + panel_height + 71), cv2, max_width=left_width)
    _text(canvas, "Q ou Esc: sair" if not args.image else "Modo foto; sem captura da webcam",
          (gap, top + panel_height + 94), cv2, max_width=left_width)
    return canvas, summary


def run_pose_image(task, args, deps, references):
    cv2, _, np, _, _ = deps
    if args.output and args.output.resolve() == args.image.resolve():
        raise ValueError("Escolha --output diferente da imagem original.")
    frame = read_image(args.image, cv2, np)
    result = process_pose_frame(task, frame, None, deps)
    search = search_result(result, frame.shape[1], frame.shape[0], references, args.match_threshold)
    selected = search.candidates[0] if search.candidates else None
    reference = ReferenceImageCache(cv2, np).get(selected)
    canvas, summary = draw_pose_match(frame, search, selected, args, cv2, np, reference)
    if args.output:
        extension = args.output.suffix.lower()
        if extension not in {".png", ".jpg", ".jpeg", ".webp"}:
            raise ValueError("--output deve terminar em .png, .jpg, .jpeg ou .webp.")
        ok, encoded = cv2.imencode(extension, canvas)
        if not ok:
            raise RuntimeError("Não foi possível codificar a comparação de poses.")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        write_new_files({args.output: encoded.tobytes()})
        summary["output"] = str(args.output)
        summary["output_contains_input_image"] = True
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def run_pose_camera(task, args, deps, references):
    cv2, _, np, _, _ = deps
    capture = cv2.VideoCapture(args.camera)
    frames = 0
    summary = None
    try:
        if not capture.isOpened():
            raise RuntimeError(
                f"Webcam {args.camera} indisponível. Feche outros apps, permita a câmera "
                "no sistema e tente --camera 1."
            )
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 540)
        clock = FrameClock()
        started = time.perf_counter()
        confirmation = MatchConfirmation()
        images = ReferenceImageCache(cv2, np)
        while True:
            ok, frame = capture.read()
            if not ok or frame is None:
                raise RuntimeError("A webcam abriu, mas não entregou um frame válido.")
            timestamp = clock.tick(time.perf_counter() - started)
            result = process_pose_frame(task, frame, timestamp, deps)
            search = search_result(result, frame.shape[1], frame.shape[0],
                                   references, args.match_threshold)
            candidate = search.candidates[0] if search.candidates else None
            selected = confirmation.update(candidate, timestamp)
            summary = match_summary(search, selected, args.mirror)
            frames += 1
            if not args.headless:
                canvas, summary = draw_pose_match(frame, search, selected, args, cv2, np,
                                                  images.get(selected))
                cv2.imshow(WINDOW, canvas)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), ord("Q"), 27):
                    break
                if cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1:
                    break
            if args.max_frames and frames >= args.max_frames:
                break
    finally:
        capture.release()
        if not args.headless:
            cv2.destroyAllWindows()
    summary.update({"processed_frames": frames, "webcam_saved": False})
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def run_posematch(args, deps):
    """Entrada isolada: carrega o catálogo e usa somente o Pose Landmarker."""
    references = load_catalog(args.gallery)
    with create_pose_task(args, deps[3], deps[4]) as task:
        if args.image:
            return run_pose_image(task, args, deps, references)
        return run_pose_camera(task, args, deps, references)
