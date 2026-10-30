"""Funções puras usadas pelo aplicativo; não dependem da câmera ou do MediaPipe."""

from __future__ import annotations

import math

# Índices oficiais dos 21 landmarks. Cada par descreve uma aresta da mão.
HAND_CONNECTIONS = (
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (0, 17), (17, 18), (18, 19), (19, 20),
)

# O cv2.putText usa fontes sem suporte completo a acentos.
GESTURE_NAMES = {
    "Closed_Fist": "PUNHO FECHADO",
    "Open_Palm": "MAO ABERTA",
    "Pointing_Up": "INDICADOR PARA CIMA",
    "Thumb_Down": "POLEGAR PARA BAIXO",
    "Thumb_Up": "JOIA",
    "Victory": "VITORIA",
    "ILoveYou": "I LOVE YOU",
}


def pixel_point(x: float, y: float, width: int, height: int, mirror: bool) -> tuple[int, int]:
    """Converte coordenadas normalizadas ao canvas e espelha só a visualização.

    Clamp protege o desenho quando a estimativa sai ligeiramente da imagem.
    O x espelhado é exatamente width - 1 - x_pixel, como no cv2.flip.
    """
    if width < 1 or height < 1:
        raise ValueError("A imagem deve ter largura e altura positivas.")
    if not math.isfinite(x) or not math.isfinite(y):
        raise ValueError("Coordenadas devem ser finitas.")
    px = min(width - 1, max(0, round(x * (width - 1))))
    py = min(height - 1, max(0, round(y * (height - 1))))
    return (width - 1 - px if mirror else px), py


def gesture_label(category: str | None, score: float, threshold: float) -> str:
    """Rejeita classes ausentes, desconhecidas ou com score insuficiente.

    'None' é uma mão detectada sem um dos gestos conhecidos. A ausência de mão
    é tratada separadamente no aplicativo, antes de chamar esta função.
    """
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("O limiar deve estar entre 0 e 1.")
    if not math.isfinite(score) or score < threshold:
        return "DESCONHECIDO"
    return GESTURE_NAMES.get(category or "", "DESCONHECIDO")


def handedness_label(category: str | None) -> str:
    """Nome da mão da pessoa; só é válido se a inferência recebe input original."""
    return {"Left": "Esquerda", "Right": "Direita"}.get(category or "", "Mao")


class FrameClock:
    """Produz timestamps em ms estritamente crescentes para a API VIDEO."""

    def __init__(self) -> None:
        self.last_ms = -1

    def tick(self, elapsed_seconds: float) -> int:
        value = max(self.last_ms + 1, int(elapsed_seconds * 1000))
        self.last_ms = value
        return value
