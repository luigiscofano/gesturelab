"""Geometria e traços da escrita no ar, sem dependências de visão ou webcam.

Uma pose pode começar vários traços. Traço não é sinônimo de letra: por exemplo,
um H pode ter três traços. O motor não segmenta caracteres nem reconhece texto.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

Point = tuple[float, float]

_HAND_LANDMARK_COUNT = 21
_FINGER_BASES = (5, 9, 13, 17)
_GEOMETRY_EPSILON = 1e-8
_MIN_PALM_WIDTH = 1e-6
_MIN_POINT_SPACING_PX = 1.0


@dataclass(frozen=True)
class _FingerShape:
    pip_angle_deg: float
    dip_angle_deg: float
    reach_ratio: float

    def is_extended(self) -> bool:
        return self.pip_angle_deg >= 155 and self.dip_angle_deg >= 150 and self.reach_ratio >= 0.85

    def is_folded(self) -> bool:
        return (self.pip_angle_deg <= 140 or self.dip_angle_deg <= 140) and self.reach_ratio <= 0.82


def _joint_angle_degrees(start: Point, joint: Point, end: Point) -> float | None:
    incoming = (start[0] - joint[0], start[1] - joint[1])
    outgoing = (end[0] - joint[0], end[1] - joint[1])
    denominator = math.hypot(*incoming) * math.hypot(*outgoing)
    if denominator < _GEOMETRY_EPSILON:
        return None
    cosine = (incoming[0] * outgoing[0] + incoming[1] * outgoing[1]) / denominator
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def _finger_shape(points: Sequence[Point], base_index: int) -> _FingerShape | None:
    mcp, pip, dip, tip = points[base_index : base_index + 4]
    pip_angle = _joint_angle_degrees(mcp, pip, dip)
    dip_angle = _joint_angle_degrees(pip, dip, tip)
    length = sum(math.dist(start, end) for start, end in ((mcp, pip), (pip, dip), (dip, tip)))
    if pip_angle is None or dip_angle is None or length < _GEOMETRY_EPSILON:
        return None
    return _FingerShape(pip_angle, dip_angle, math.dist(mcp, tip) / length)


def writing_pose(points: Sequence[Point]) -> bool:
    """Indicador estendido e demais três dedos recolhidos; polegar ignorado.

    Os pontos precisam estar em unidades coerentes, por exemplo pixels. Ângulos
    e razões evitam depender de 'ponta acima da articulação'. Esta é uma regra
    2D didática: perspectiva, oclusões e estimativas ruins ainda podem fazê-la falhar.
    """
    if len(points) != _HAND_LANDMARK_COUNT:
        return False
    if any(not math.isfinite(coordinate) for point in points for coordinate in point):
        return False
    if math.dist(points[5], points[17]) < _MIN_PALM_WIDTH:
        return False

    fingers = []
    for base_index in _FINGER_BASES:
        shape = _finger_shape(points, base_index)
        if shape is None:
            return False
        fingers.append(shape)
    index_finger, *other_fingers = fingers
    return index_finger.is_extended() and all(finger.is_folded() for finger in other_fingers)


@dataclass(frozen=True)
class StrokePoint:
    x: float
    y: float
    t_ms: int


class AirWriter:
    """Máquina de estados de caneta, com confirmação de entrada e saída imediata.

    Coordenadas são pixels da visualização; somente a exibição pode ser espelhada.
    Timestamps são crescentes e relativos ao início da captura. Salto, intervalo
    longo ou mudança de lateralidade encerram o traço, sem unir mãos por índice.
    """

    def __init__(
        self,
        width: int,
        height: int,
        *,
        smooth_ms: float = 45.0,
        confirm_ms: int = 100,
        max_gap_ms: int = 250,
        max_jump_ratio: float = 0.18,
        mirrored: bool = True,
    ) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("O canvas precisa ter dimensões positivas.")
        if not math.isfinite(smooth_ms) or smooth_ms < 0:
            raise ValueError("smooth_ms deve ser finito e não negativo.")
        if confirm_ms < 0 or max_gap_ms <= 0 or not 0 < max_jump_ratio <= 1:
            raise ValueError("Parâmetros de confirmação e continuidade inválidos.")
        self.width = width
        self.height = height
        self.mirrored = mirrored
        self.smooth_ms = smooth_ms
        self.confirm_ms = confirm_ms
        self.max_gap_ms = max_gap_ms
        self.max_jump_px = math.hypot(width, height) * max_jump_ratio
        self.enabled = True
        self.completed: list[list[StrokePoint]] = []
        self.current: list[StrokePoint] | None = None
        self.status = "CANETA LEVANTADA"
        self._candidate_since_ms: int | None = None
        self._last_timestamp_ms: int | None = None
        self._last_raw_point: Point | None = None
        self._last_hand_tag: str | None = None
        self._filtered_point: Point | None = None
        self._filtered_timestamp_ms: int | None = None

    @property
    def writing(self) -> bool:
        return self.current is not None

    @property
    def strokes(self) -> list[list[StrokePoint]]:
        return self.completed + ([self.current] if self.current is not None else [])

    def lift(self, status: str = "CANETA LEVANTADA") -> None:
        """Fecha o traço e remove todo histórico espacial e de confirmação."""
        if self.current:
            self.completed.append(self.current)
        self.current = None
        self._candidate_since_ms = None
        self._last_raw_point = None
        self._last_hand_tag = None
        self._filtered_point = None
        self._filtered_timestamp_ms = None
        self.status = status if self.enabled else "PAUSADO"

    def toggle_pause(self) -> None:
        self.enabled = not self.enabled
        self.lift()

    def clear(self) -> None:
        self.lift()
        self.completed.clear()

    def undo(self) -> None:
        self.lift()
        if self.completed:
            self.completed.pop()

    def update(
        self,
        point: Point | None,
        pose_active: bool,
        timestamp_ms: int,
        *,
        hand_tag: str | None = None,
        unavailable: str = "CANETA LEVANTADA",
    ) -> None:
        previous_timestamp_ms = self._last_timestamp_ms
        if timestamp_ms < 0 or (
            previous_timestamp_ms is not None and timestamp_ms <= previous_timestamp_ms
        ):
            raise ValueError("Os timestamps da caneta devem crescer em milissegundos.")
        self._last_timestamp_ms = timestamp_ms
        if not self.enabled:
            self.lift("PAUSADO")
            return
        if not pose_active or point is None or not self._point_is_visible(point):
            self.lift(unavailable)
            return

        if self._has_discontinuity(point, timestamp_ms, previous_timestamp_ms, hand_tag):
            self.lift("REPOSICIONE A CANETA")
        self._last_raw_point = point
        self._last_hand_tag = hand_tag
        if self._candidate_since_ms is None:
            self._candidate_since_ms = timestamp_ms
        if not self.writing:
            if timestamp_ms - self._candidate_since_ms < self.confirm_ms:
                self.status = "CONFIRMANDO POSE"
                return
            self._start_stroke(point, timestamp_ms)
        else:
            self._extend_stroke(point, timestamp_ms)
        self.status = "ESCREVENDO"

    def _point_is_visible(self, point: Point) -> bool:
        return (
            all(math.isfinite(coordinate) for coordinate in point)
            and 0 <= point[0] < self.width
            and 0 <= point[1] < self.height
        )

    def _has_discontinuity(
        self,
        point: Point,
        timestamp_ms: int,
        previous_timestamp_ms: int | None,
        hand_tag: str | None,
    ) -> bool:
        frame_gap = (
            previous_timestamp_ms is not None
            and timestamp_ms - previous_timestamp_ms > self.max_gap_ms
        )
        if self._last_raw_point is None:
            return frame_gap
        position_jump = math.dist(point, self._last_raw_point) > self.max_jump_px
        hand_changed = self._last_hand_tag != hand_tag
        return frame_gap or position_jump or hand_changed

    def _start_stroke(self, point: Point, timestamp_ms: int) -> None:
        self.current = [StrokePoint(*point, timestamp_ms)]
        self._filtered_point = point
        self._filtered_timestamp_ms = timestamp_ms

    def _extend_stroke(self, point: Point, timestamp_ms: int) -> None:
        elapsed_ms = timestamp_ms - self._filtered_timestamp_ms
        alpha = 1.0 if self.smooth_ms == 0 else -math.expm1(-elapsed_ms / self.smooth_ms)
        previous_x, previous_y = self._filtered_point
        filtered = (
            previous_x + alpha * (point[0] - previous_x),
            previous_y + alpha * (point[1] - previous_y),
        )
        self._filtered_point = filtered
        self._filtered_timestamp_ms = timestamp_ms

        # O filtro recebe todos os frames, mas o traço descarta deslocamentos subpixel.
        last_point = self.current[-1]
        if math.dist(filtered, (last_point.x, last_point.y)) >= _MIN_POINT_SPACING_PX:
            self.current.append(StrokePoint(*filtered, timestamp_ms))

    def snapshot(self) -> dict[str, object]:
        """Serializa somente desenho e contexto; não armazena imagem da webcam."""
        return {
            "schema_version": 1,
            "coordinate_space": "display_pixels",
            "frame_size": {"width": self.width, "height": self.height},
            "mirrored": self.mirrored,
            "point_processing": "ema_smoothed" if self.smooth_ms else "raw",
            "smooth_ms": self.smooth_ms,
            "confirm_ms": self.confirm_ms,
            "timestamp_origin": "capture_start_ms",
            "stroke_semantics": "pen_down_segments_not_characters",
            "strokes": [
                {"points": [{"x": point.x, "y": point.y, "t_ms": point.t_ms} for point in stroke]}
                for stroke in self.strokes
            ],
        }
