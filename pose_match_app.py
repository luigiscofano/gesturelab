"""Busca corporal, confirmação temporal e interface do modo posematch."""

from __future__ import annotations

import json
import math
import time
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core import FrameClock, pixel_point
from pose_matching import (
    BODY_JOINTS,
    POSE_CONNECTIONS,
    PoseMatch,
    PoseReference,
    extract_pose,
    load_catalog,
    rank_matches,
)
from vision_runtime import (
    MODEL_NAMES,
    QUIT_KEYS,
    VisionDependencies,
    camera_session,
    read_camera_frame,
    read_image,
    to_mediapipe_image,
    write_image,
)

ROOT = Path(__file__).resolve().parent
WINDOW = "GestureLab | Pose parecida"
CAMERA_PANEL_WIDTH = 640
REFERENCE_PANEL_WIDTH = 440
PANEL_HEIGHT = 400
PANEL_GAP = 16
PANEL_TOP = 76
PANEL_BOTTOM = 136
REFERENCE_X = CAMERA_PANEL_WIDTH + 2 * PANEL_GAP


@dataclass(frozen=True)
class PoseSearch:
    pose_count: int
    status: str
    candidates: tuple[PoseMatch, ...] = ()
    landmarks: Sequence[Any] | None = None


def search_result(
    result, width: int, height: int, references: Sequence[PoseReference], threshold: float
) -> PoseSearch:
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
            raise ValueError(
                "Confirmação não negativa e intervalo máximo positivo são necessários."
            )
        self.confirm_ms = confirm_ms
        self.max_gap_ms = max_gap_ms
        self._candidate_key: tuple[str, bool] | None = None
        self._candidate_since_ms = 0
        self._previous_timestamp_ms: int | None = None

    def update(self, candidate: PoseMatch | None, timestamp_ms: int) -> PoseMatch | None:
        if self._previous_timestamp_ms is not None and timestamp_ms <= self._previous_timestamp_ms:
            raise ValueError("Timestamps da confirmação devem ser crescentes.")
        tracking_gap = (
            self._previous_timestamp_ms is not None
            and timestamp_ms - self._previous_timestamp_ms > self.max_gap_ms
        )
        self._previous_timestamp_ms = timestamp_ms
        if candidate is None:
            self._candidate_key = None
            return None
        key = (candidate.reference.id, candidate.mirrored)
        if tracking_gap or key != self._candidate_key:
            self._candidate_key = key
            self._candidate_since_ms = timestamp_ms
        return candidate if timestamp_ms - self._candidate_since_ms >= self.confirm_ms else None


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
    model = args.model or ROOT / "models" / MODEL_NAMES["posematch"]
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


def process_pose_frame(task, frame, timestamp_ms, dependencies: VisionDependencies):
    image = to_mediapipe_image(frame, dependencies)
    return (
        task.detect(image) if timestamp_ms is None else task.detect_for_video(image, timestamp_ms)
    )


class ReferenceImageCache:
    """Mantém somente a imagem atual em memória, inclusive em galerias grandes."""

    def __init__(self, cv2, np) -> None:
        self.cv2 = cv2
        self.np = np
        self._path: Path | None = None
        self._image = None

    def get(self, match: PoseMatch | None):
        if match is None:
            return None
        path = match.reference.image_path
        if path != self._path:
            image = read_image(path, self.cv2, self.np)
            self._path = path
            self._image = image
        return self._image


def draw_panel_text(canvas, text, point, cv2, color=(230, 235, 242), max_width=None):
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
    resized = cv2.resize(
        image, size, interpolation=cv2.INTER_AREA if ratio < 1 else cv2.INTER_LINEAR
    )
    x, y = (width - size[0]) // 2, (height - size[1]) // 2
    box[y : y + size[1], x : x + size[0]] = resized
    return box


def draw_body_landmarks(frame, landmarks, mirror: bool, cv2):
    camera = cv2.flip(frame, 1) if mirror else frame.copy()
    if landmarks is None:
        return camera
    height, width = camera.shape[:2]
    points = {}
    for index in BODY_JOINTS:
        if index >= len(landmarks):
            continue
        landmark = landmarks[index]
        visibility = getattr(landmark, "visibility", 1.0)
        presence = getattr(landmark, "presence", 1.0)
        visibility = 1.0 if visibility is None else visibility
        presence = 1.0 if presence is None else presence
        if not all(math.isfinite(value) for value in (visibility, presence)):
            continue
        if min(visibility, presence) < 0.5:
            continue
        if not all(math.isfinite(value) for value in (landmark.x, landmark.y)):
            continue
        if not (0 <= landmark.x <= 1 and 0 <= landmark.y <= 1):
            continue
        points[index] = pixel_point(landmark.x, landmark.y, width, height, mirror)
    for first, second in POSE_CONNECTIONS:
        if first in points and second in points:
            cv2.line(camera, points[first], points[second], (110, 230, 190), 3, cv2.LINE_AA)
    for point in points.values():
        cv2.circle(camera, point, 4, (245, 240, 240), -1, cv2.LINE_AA)
    return camera


def draw_reference_panel(canvas, selected, reference_image, mirror: bool, cv2, np) -> None:
    if selected is None or reference_image is None:
        draw_panel_text(
            canvas,
            "Aguardando pose com correspondencia",
            (REFERENCE_X + 16, PANEL_TOP + 180),
            cv2,
            max_width=REFERENCE_PANEL_WIDTH - 32,
        )
        draw_panel_text(
            canvas,
            "Mostre o corpo e mantenha a posicao",
            (REFERENCE_X + 16, PANEL_TOP + 207),
            cv2,
            max_width=REFERENCE_PANEL_WIDTH - 32,
        )
        return

    flipped = bool(mirror) != selected.mirrored
    reference_image = cv2.flip(reference_image, 1) if flipped else reference_image
    canvas[
        PANEL_TOP : PANEL_TOP + PANEL_HEIGHT, REFERENCE_X : REFERENCE_X + REFERENCE_PANEL_WIDTH
    ] = fit_image(reference_image, REFERENCE_PANEL_WIDTH, PANEL_HEIGHT, cv2, np)
    orientation = " | imagem espelhada" if flipped else ""
    credit = getattr(selected.reference, "credit", "")
    details = (
        selected.reference.title,
        f"Distancia: {selected.distance:.3f} | menor = mais proxima",
        f"{selected.joint_count} pontos comparados{orientation}",
        f"Fonte: {selected.reference.source}",
        f"{credit} | {selected.reference.license}".strip(" |"),
    )
    for index, text in enumerate(details):
        point = (REFERENCE_X, PANEL_TOP + PANEL_HEIGHT + 25 + 23 * index)
        draw_panel_text(canvas, text, point, cv2, max_width=REFERENCE_PANEL_WIDTH)


def draw_pose_match(frame, search, selected, args, cv2, np, reference_image=None):
    camera = draw_body_landmarks(frame, search.landmarks, args.mirror, cv2)
    canvas = np.full(
        (
            PANEL_TOP + PANEL_HEIGHT + PANEL_BOTTOM,
            REFERENCE_X + REFERENCE_PANEL_WIDTH + PANEL_GAP,
            3,
        ),
        (18, 23, 31),
        dtype=np.uint8,
    )
    canvas[PANEL_TOP : PANEL_TOP + PANEL_HEIGHT, PANEL_GAP : PANEL_GAP + CAMERA_PANEL_WIDTH] = (
        fit_image(camera, CAMERA_PANEL_WIDTH, PANEL_HEIGHT, cv2, np)
    )
    draw_panel_text(
        canvas, "GestureLab | POSE PARECIDA", (PANEL_GAP, 27), cv2, color=(110, 230, 190)
    )
    draw_panel_text(canvas, "Sua pose", (PANEL_GAP, 58), cv2)
    draw_panel_text(
        canvas,
        "Imagem mais proxima no catalogo",
        (REFERENCE_X, 58),
        cv2,
        max_width=REFERENCE_PANEL_WIDTH,
    )
    draw_reference_panel(canvas, selected, reference_image, args.mirror, cv2, np)

    summary = match_summary(search, selected, args.mirror)
    instructions = (
        summary["status"],
        "Uma pessoa; enquadre ombros, quadris, bracos e pernas",
        "Busca local por geometria; distancia nao e probabilidade",
        "Q ou Esc: sair" if not args.image else "Modo foto; sem captura da webcam",
    )
    for index, text in enumerate(instructions):
        point = (PANEL_GAP, PANEL_TOP + PANEL_HEIGHT + 25 + 23 * index)
        draw_panel_text(canvas, text, point, cv2, max_width=CAMERA_PANEL_WIDTH)
    return canvas, summary


def run_pose_image(task, args, dependencies: VisionDependencies, references):
    cv2, np = dependencies.cv2, dependencies.numpy
    if args.output and args.output.resolve() == args.image.resolve():
        raise ValueError("Escolha --output diferente da imagem original.")
    frame = read_image(args.image, cv2, np)
    result = process_pose_frame(task, frame, None, dependencies)
    search = search_result(result, frame.shape[1], frame.shape[0], references, args.match_threshold)
    selected = search.candidates[0] if search.candidates else None
    reference = ReferenceImageCache(cv2, np).get(selected)
    canvas, summary = draw_pose_match(frame, search, selected, args, cv2, np, reference)
    if args.output:
        write_image(
            args.output,
            canvas,
            cv2,
            encode_error="Não foi possível codificar a comparação de poses.",
        )
        summary["output"] = str(args.output)
        summary["output_contains_input_image"] = True
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def run_pose_camera(task, args, dependencies: VisionDependencies, references):
    cv2, np = dependencies.cv2, dependencies.numpy
    frames = 0
    summary = None
    with camera_session(cv2, args.camera, headless=args.headless) as capture:
        clock = FrameClock()
        started = time.perf_counter()
        confirmation = MatchConfirmation()
        images = ReferenceImageCache(cv2, np)
        while True:
            frame = read_camera_frame(capture)
            timestamp = clock.tick(time.perf_counter() - started)
            result = process_pose_frame(task, frame, timestamp, dependencies)
            search = search_result(
                result,
                frame.shape[1],
                frame.shape[0],
                references,
                args.match_threshold,
            )
            candidate = search.candidates[0] if search.candidates else None
            selected = confirmation.update(candidate, timestamp)
            summary = match_summary(search, selected, args.mirror)
            frames += 1
            if not args.headless:
                canvas, summary = draw_pose_match(
                    frame,
                    search,
                    selected,
                    args,
                    cv2,
                    np,
                    images.get(selected),
                )
                cv2.imshow(WINDOW, canvas)
                key = cv2.waitKey(1) & 0xFF
                if key in QUIT_KEYS:
                    break
                if cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1:
                    break
            if args.max_frames and frames >= args.max_frames:
                break
    summary.update({"processed_frames": frames, "webcam_saved": False})
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def run_posematch(args, dependencies: VisionDependencies):
    """Carrega o catálogo e usa somente o modelo corporal."""
    references = load_catalog(args.gallery)
    with create_pose_task(args, dependencies.tasks, dependencies.vision) as task:
        if args.image:
            return run_pose_image(task, args, dependencies, references)
        return run_pose_camera(task, args, dependencies, references)
