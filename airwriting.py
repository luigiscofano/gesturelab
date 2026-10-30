"""Geometria e traços da escrita no ar, sem dependências de visão ou webcam.

Uma pose pode começar vários traços. Traço não é sinônimo de letra: por exemplo,
um H pode ter três traços. O motor não segmenta caracteres nem reconhece texto.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

Point = tuple[float, float]


def _angle(a: Point, b: Point, c: Point) -> float | None:
    u = (a[0] - b[0], a[1] - b[1])
    v = (c[0] - b[0], c[1] - b[1])
    denominator = math.hypot(*u) * math.hypot(*v)
    if denominator < 1e-8:
        return None
    cosine = (u[0] * v[0] + u[1] * v[1]) / denominator
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def _finger_shape(points: Sequence[Point], start: int) -> tuple[float, float, float] | None:
    mcp, pip, dip, tip = points[start:start + 4]
    pip_angle = _angle(mcp, pip, dip)
    dip_angle = _angle(pip, dip, tip)
    length = sum(math.dist(a, b) for a, b in ((mcp, pip), (pip, dip), (dip, tip)))
    if pip_angle is None or dip_angle is None or length < 1e-8:
        return None
    return pip_angle, dip_angle, math.dist(mcp, tip) / length


def writing_pose(points: Sequence[Point]) -> bool:
    """Indicador estendido e demais três dedos recolhidos; polegar ignorado.

    Os pontos precisam estar em unidades coerentes, por exemplo pixels. Ângulos
    e razões evitam depender de 'ponta acima da articulação'. Esta é uma regra
    2D didática: perspectiva, oclusões e estimativas ruins ainda podem fazê-la falhar.
    """
    if len(points) != 21 or any(not math.isfinite(v) for point in points for v in point):
        return False
    if math.dist(points[5], points[17]) < 1e-6:
        return False
    shapes = [_finger_shape(points, start) for start in (5, 9, 13, 17)]
    if any(shape is None for shape in shapes):
        return False
    index = shapes[0]
    if not (index[0] >= 155 and index[1] >= 150 and index[2] >= 0.85):
        return False
    return all((pip <= 140 or dip <= 140) and reach <= 0.82
               for pip, dip, reach in shapes[1:])


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

    def __init__(self, width: int, height: int, *, smooth_ms: float = 45.0,
                 confirm_ms: int = 100, max_gap_ms: int = 250,
                 max_jump_ratio: float = 0.18, mirrored: bool = True):
        if width <= 0 or height <= 0:
            raise ValueError("O canvas precisa ter dimensões positivas.")
        if not math.isfinite(smooth_ms) or smooth_ms < 0:
            raise ValueError("smooth_ms deve ser finito e não negativo.")
        if confirm_ms < 0 or max_gap_ms <= 0 or not 0 < max_jump_ratio <= 1:
            raise ValueError("Parâmetros de confirmação e continuidade inválidos.")
        self.width, self.height = width, height
        self.mirrored = mirrored
        self.smooth_ms = smooth_ms
        self.confirm_ms = confirm_ms
        self.max_gap_ms = max_gap_ms
        self.max_jump_px = math.hypot(width, height) * max_jump_ratio
        self.enabled = True
        self.completed: list[list[StrokePoint]] = []
        self.current: list[StrokePoint] | None = None
        self.status = "CANETA LEVANTADA"
        self._candidate_since: int | None = None
        self._last_t: int | None = None
        self._last_raw: Point | None = None
        self._last_hand: str | None = None
        self._filtered: Point | None = None
        self._filtered_t: int | None = None

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
        self._candidate_since = None
        self._last_raw = None
        self._last_hand = None
        self._filtered = None
        self._filtered_t = None
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

    def update(self, point: Point | None, pose_active: bool, timestamp_ms: int,
               *, hand_tag: str | None = None, unavailable: str = "CANETA LEVANTADA") -> None:
        if timestamp_ms < 0 or (self._last_t is not None and timestamp_ms <= self._last_t):
            raise ValueError("Os timestamps da caneta devem crescer em milissegundos.")
        previous_t = self._last_t
        self._last_t = timestamp_ms
        if not self.enabled:
            self.lift("PAUSADO")
            return
        valid = (point is not None and all(math.isfinite(v) for v in point)
                 and 0 <= point[0] < self.width and 0 <= point[1] < self.height)
        if not pose_active or not valid:
            self.lift(unavailable)
            return

        discontinuity = (
            previous_t is not None and timestamp_ms - previous_t > self.max_gap_ms
            or self._last_raw is not None and math.dist(point, self._last_raw) > self.max_jump_px
            or self._last_raw is not None and self._last_hand != hand_tag
        )
        if discontinuity:
            self.lift("REPOSICIONE A CANETA")
        self._last_raw = point
        self._last_hand = hand_tag
        if self._candidate_since is None:
            self._candidate_since = timestamp_ms
        if not self.writing:
            if timestamp_ms - self._candidate_since < self.confirm_ms:
                self.status = "CONFIRMANDO POSE"
                return
            self.current = [StrokePoint(*point, timestamp_ms)]
            self._filtered = point
            self._filtered_t = timestamp_ms
        else:
            dt = timestamp_ms - self._filtered_t
            alpha = 1.0 if self.smooth_ms == 0 else -math.expm1(-dt / self.smooth_ms)
            filtered = tuple(old + alpha * (new - old)
                             for old, new in zip(self._filtered, point))
            self._filtered = filtered
            self._filtered_t = timestamp_ms
            # Reduz pontos redundantes; o filtro continua recebendo todos os frames.
            if math.dist(filtered, (self.current[-1].x, self.current[-1].y)) >= 1.0:
                self.current.append(StrokePoint(*filtered, timestamp_ms))
        self.status = "ESCREVENDO"

    def snapshot(self) -> dict:
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
            "strokes": [{"points": [{"x": p.x, "y": p.y, "t_ms": p.t_ms} for p in stroke]}
                        for stroke in self.strokes],
        }
