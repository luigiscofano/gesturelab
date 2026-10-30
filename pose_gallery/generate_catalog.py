"""Gera o catálogo ilustrado original; precisa de OpenCV e NumPy instalados.

Os pontos são a geometria dos desenhos, não resultados de inferência sobre fotos.
Execute da raiz: python pose_gallery/generate_catalog.py
"""

from __future__ import annotations

import json
import math
from html import escape
from pathlib import Path

type Point = tuple[int, int]
type Color = tuple[int, int, int]
type PosePoints = dict[int, Point]

WIDTH, HEIGHT = 480, 640
ROOT = Path(__file__).resolve().parent
BODY = [11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]
LIMB_CONNECTIONS = (
    (11, 13),
    (13, 15),
    (12, 14),
    (14, 16),
    (23, 25),
    (25, 27),
    (24, 26),
    (26, 28),
)
HAND_AND_FOOT_JOINTS = {15, 16, 27, 28}
SKIN_COLOR = (245, 207, 147)
BASE = {
    11: (285, 200),
    12: (195, 200),
    13: (305, 280),
    14: (175, 280),
    15: (315, 365),
    16: (165, 365),
    23: (270, 350),
    24: (210, 350),
    25: (275, 455),
    26: (205, 455),
    27: (280, 560),
    28: (200, 560),
}
POSES = [
    ("arms-down", "Braços ao lado", {}),
    (
        "arms-wide",
        "Braços abertos",
        {13: (360, 200), 14: (120, 200), 15: (430, 200), 16: (50, 200)},
    ),
    ("arms-up", "Braços para cima", {13: (310, 120), 14: (170, 120), 15: (325, 40), 16: (155, 40)}),
    ("one-arm-up", "Um braço levantado", {13: (310, 120), 15: (325, 40)}),
    (
        "hands-on-hips",
        "Mãos na cintura",
        {13: (340, 270), 14: (140, 270), 15: (275, 330), 16: (205, 330)},
    ),
    (
        "elbows-bent",
        "Cotovelos dobrados",
        {13: (355, 220), 14: (125, 220), 15: (355, 125), 16: (125, 125)},
    ),
    ("low-v", "Braços em V baixo", {13: (350, 285), 14: (130, 285), 15: (415, 370), 16: (65, 370)}),
    (
        "wide-squat",
        "Agachamento aberto",
        {
            11: (285, 230),
            12: (195, 230),
            13: (350, 250),
            14: (130, 250),
            15: (380, 170),
            16: (100, 170),
            23: (280, 390),
            24: (200, 390),
            25: (360, 430),
            26: (120, 430),
            27: (360, 555),
            28: (120, 555),
        },
    ),
    (
        "side-step",
        "Passo lateral",
        {
            13: (350, 200),
            14: (130, 200),
            15: (420, 200),
            16: (60, 200),
            25: (350, 440),
            26: (190, 455),
            27: (420, 555),
            28: (155, 560),
        },
    ),
    (
        "raised-knee",
        "Um joelho elevado",
        {
            13: (340, 220),
            14: (140, 220),
            15: (370, 140),
            16: (110, 140),
            25: (355, 350),
            27: (360, 455),
        },
    ),
    (
        "wide-lunge",
        "Avanço com braços abertos",
        {
            13: (360, 200),
            14: (120, 200),
            15: (430, 200),
            16: (50, 200),
            25: (350, 430),
            26: (120, 370),
            27: (430, 510),
            28: (120, 510),
        },
    ),
    (
        "side-bend",
        "Inclinação lateral",
        {
            11: (230, 205),
            12: (140, 250),
            13: (250, 125),
            14: (130, 335),
            15: (185, 60),
            16: (145, 415),
        },
    ),
]
COLORS = [
    (61, 122, 183),
    (34, 138, 112),
    (135, 91, 177),
    (191, 116, 47),
    (179, 80, 102),
    (46, 135, 155),
    (107, 133, 57),
    (114, 94, 176),
    (185, 91, 56),
    (56, 118, 165),
    (51, 141, 129),
    (171, 94, 133),
]


def normalized_landmarks(points: PosePoints) -> list[dict[str, float]]:
    # Landmarks não usados na busca têm posições ilustrativas junto à cabeça/mãos/pés.
    landmarks = [{"x": 0.5, "y": 0.17, "visibility": 1.0, "presence": 1.0} for _ in range(33)]
    for index, (x, y) in points.items():
        landmarks[index] = {"x": x / WIDTH, "y": y / HEIGHT, "visibility": 1.0, "presence": 1.0}
    for target, source in (
        (17, 15),
        (19, 15),
        (21, 15),
        (18, 16),
        (20, 16),
        (22, 16),
        (29, 27),
        (31, 27),
        (30, 28),
        (32, 28),
    ):
        landmarks[target] = dict(landmarks[source])
    return landmarks


def render(points: PosePoints, color: Color, title: str) -> tuple[str, bytes]:
    import cv2
    import numpy as np

    ink = (37, 49, 68)
    background = (246, 248, 252)
    image = np.full((HEIGHT, WIDTH, 3), background[::-1], dtype=np.uint8)
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}"><title>{escape(title)}</title>',
        '<rect width="480" height="640" rx="20" fill="#f6f8fc"/>',
    ]

    def circle(
        point: Point,
        radius: int,
        fill: Color,
        stroke: Color | None = None,
        thickness: int = 0,
    ) -> None:
        cv2.circle(image, point, radius, fill[::-1], -1, cv2.LINE_AA)
        if stroke:
            cv2.circle(image, point, radius, stroke[::-1], thickness, cv2.LINE_AA)
        style = f' fill="rgb{fill}"'
        if stroke:
            style += f' stroke="rgb{stroke}" stroke-width="{thickness}"'
        svg.append(f'<circle cx="{point[0]}" cy="{point[1]}" r="{radius}"{style}/>')

    def line(start: Point, end: Point, fill: Color, thickness: int) -> None:
        cv2.line(image, start, end, fill[::-1], thickness, cv2.LINE_AA)
        circle(start, thickness // 2, fill)
        circle(end, thickness // 2, fill)
        svg.append(
            f'<path d="M {start[0]} {start[1]} L {end[0]} {end[1]}" '
            f'fill="none" stroke="rgb{fill}" stroke-width="{thickness}" '
            'stroke-linecap="round"/>'
        )

    shoulder_center = tuple(round((points[11][axis] + points[12][axis]) / 2) for axis in (0, 1))
    hip_center = tuple(round((points[23][axis] + points[24][axis]) / 2) for axis in (0, 1))
    torso_length = math.dist(shoulder_center, hip_center)
    head = tuple(
        round(
            shoulder_center[axis] + 90 * (shoulder_center[axis] - hip_center[axis]) / torso_length
        )
        for axis in (0, 1)
    )
    ground = max(points[27][1], points[28][1]) + 24
    cv2.ellipse(image, (240, ground), (175, 10), 0, 0, 360, (222, 228, 237), -1)
    svg.append(f'<ellipse cx="240" cy="{ground}" rx="175" ry="10" fill="#ede4de"/>')
    for start_index, end_index in LIMB_CONNECTIONS:
        line(points[start_index], points[end_index], ink, 30)
        line(points[start_index], points[end_index], color, 20)
    torso = [points[index] for index in (12, 11, 23, 24)]
    torso_polygon = np.array(torso, dtype=np.int32)
    cv2.fillPoly(image, [torso_polygon], color[::-1], cv2.LINE_AA)
    cv2.polylines(image, [torso_polygon], True, ink[::-1], 5, cv2.LINE_AA)
    torso_coordinates = " ".join(f"{x},{y}" for x, y in torso)
    svg.append(
        f'<polygon points="{torso_coordinates}" '
        f'fill="rgb{color}" stroke="rgb{ink}" stroke-width="5" stroke-linejoin="round"/>'
    )
    line(shoulder_center, head, ink, 18)
    circle(head, 37, SKIN_COLOR, ink, 5)
    for x in (head[0] - 12, head[0] + 12):
        circle((x, head[1] - 3), 4, ink)
    line((head[0] - 8, head[1] + 14), (head[0] + 8, head[1] + 14), ink, 3)
    for index in BODY:
        radius = 13 if index in HAND_AND_FOOT_JOINTS else 8
        circle(points[index], radius, SKIN_COLOR, ink, 3)
    # O título e os créditos ficam na interface, pois a referência pode ser espelhada.
    svg.append("</svg>")
    encoded_ok, encoded = cv2.imencode(".png", image)
    if not encoded_ok:
        raise RuntimeError("Falha ao gerar PNG do catálogo.")
    return "\n".join(svg), encoded.tobytes()


def generate_catalog(output_directory: Path) -> int:
    images = output_directory / "images"
    images.mkdir(parents=True, exist_ok=True)
    references = []
    for (name, title, overrides), color in zip(POSES, COLORS, strict=True):
        points = BASE | overrides
        svg, png = render(points, color, title)
        (images / f"{name}.svg").write_text(svg, encoding="utf-8")
        (images / f"{name}.png").write_bytes(png)
        references.append(
            {
                "id": name,
                "title": title,
                "image": f"images/{name}.png",
                "source": "Ilustração original do GestureLab; geometria gerada pelo código",
                "license": "MIT",
                "credit": "GestureLab, com assistência de IA",
                "width": WIDTH,
                "height": HEIGHT,
                "landmarks": normalized_landmarks(points),
            }
        )
    catalog = {
        "schema_version": 1,
        "description": "Catálogo ilustrado original; não são fotografias",
        "landmark_origin": "exact_drawing_geometry",
        "references": references,
    }
    (output_directory / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return len(references)


def main() -> None:
    count = generate_catalog(ROOT)
    print(f"{count} ilustrações e catálogo gerados em {ROOT}")


if __name__ == "__main__":
    main()
