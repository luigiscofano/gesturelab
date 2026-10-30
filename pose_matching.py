"""Busca geométrica de poses humanas em um catálogo local de imagens.

O descritor usa 12 articulações em pixels, centradas no quadril e divididas pelo
tamanho do tronco. A distância é RMS ponderada, não probabilidade de acerto.
Somente a biblioteca padrão é usada: testes e leitura do catálogo não carregam CV.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

BODY_JOINTS = (11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28)
TORSO_JOINTS = (11, 12, 23, 24)
POSE_CONNECTIONS = (
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
    (11, 23), (12, 24), (23, 24), (23, 25), (25, 27), (24, 26), (26, 28),
)
MIN_JOINTS = 8
DEFAULT_MAX_DISTANCE = 0.8
Point = tuple[float, float]


@dataclass(frozen=True)
class PoseVector:
    # A ordem corresponde a BODY_JOINTS; articulações pouco confiáveis são None.
    points: tuple[Point | None, ...]
    weights: tuple[float, ...]

    @property
    def joint_count(self) -> int:
        return sum(point is not None for point in self.points)


@dataclass(frozen=True)
class PoseReference:
    id: str
    title: str
    image_path: Path
    pose: PoseVector
    source: str = ""
    license: str = ""
    credit: str = ""


@dataclass(frozen=True)
class PoseMatch:
    reference: PoseReference
    distance: float
    mirrored: bool
    joint_count: int


def _field(landmark, key: str, default=None):
    return landmark.get(key, default) if isinstance(landmark, Mapping) else getattr(
        landmark, key, default
    )


def _number(value) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(value) else None


def extract_pose(landmarks: Sequence, width: int, height: int, *,
                 min_visibility: float = 0.5) -> PoseVector | None:
    """Normaliza 33 landmarks MediaPipe; retorna None para enquadramento insuficiente.

    x/y devem estar normalizados na imagem original. width/height corrigem a
    proporção da imagem antes de calcular distâncias. Não remove rotação do corpo.
    Ombros e quadris devem estar visíveis, além de pelo menos oito articulações.
    Pontos fora da imagem, não finitos ou com baixa visibility/presence são omitidos.
    """
    if (type(width) is not int or type(height) is not int or width <= 0 or height <= 0):
        raise ValueError("As dimensões da imagem devem ser inteiros positivos.")
    if (_number(min_visibility) is None or not 0 <= min_visibility <= 1):
        raise ValueError("min_visibility deve estar entre 0 e 1.")
    if len(landmarks) != 33:
        return None
    points: dict[int, Point] = {}
    confidence: dict[int, float] = {}
    for index in BODY_JOINTS:
        landmark = landmarks[index]
        x, y = _number(_field(landmark, "x")), _number(_field(landmark, "y"))
        visibility = _field(landmark, "visibility", 1.0)
        presence = _field(landmark, "presence", 1.0)
        visibility = _number(1.0 if visibility is None else visibility)
        presence = _number(1.0 if presence is None else presence)
        if (x is None or y is None or visibility is None or presence is None
                or not 0 <= x <= 1 or not 0 <= y <= 1
                or not 0 <= visibility <= 1 or not 0 <= presence <= 1):
            continue
        weight = min(visibility, presence)
        if weight <= 0 or weight < min_visibility:
            continue
        points[index] = (x * width, y * height)
        confidence[index] = weight
    if len(points) < MIN_JOINTS or any(index not in points for index in TORSO_JOINTS):
        return None

    pelvis = tuple((points[23][axis] + points[24][axis]) / 2 for axis in (0, 1))
    shoulders = tuple((points[11][axis] + points[12][axis]) / 2 for axis in (0, 1))
    # Comprimentos laterais evitam escala nula quando o centro dos ombros e o
    # quadril se aproximam na projeção. Um tronco degenerado continua rejeitado.
    scale = max(
        math.dist(pelvis, shoulders),
        (math.dist(points[11], points[23]) + math.dist(points[12], points[24])) / 2,
        math.dist(points[11], points[12]) / 2,
        math.dist(points[23], points[24]) / 2,
    )
    if scale < 1.0:
        return None
    normalized = tuple(
        ((points[index][0] - pelvis[0]) / scale, (points[index][1] - pelvis[1]) / scale)
        if index in points else None
        for index in BODY_JOINTS
    )
    return PoseVector(normalized, tuple(confidence.get(index, 0.0) for index in BODY_JOINTS))


def mirror_pose(pose: PoseVector) -> PoseVector:
    """Espelha x e troca os lados anatômicos; pares adjacentes são esquerda/direita."""
    indices = tuple(index ^ 1 for index in range(len(BODY_JOINTS)))
    return PoseVector(
        tuple((-pose.points[index][0], pose.points[index][1])
              if pose.points[index] is not None else None for index in indices),
        tuple(pose.weights[index] for index in indices),
    )


def _distance(query: PoseVector, reference: PoseVector) -> tuple[float, int] | None:
    shared = [index for index in range(len(BODY_JOINTS))
              if query.points[index] is not None and reference.points[index] is not None]
    if len(shared) < MIN_JOINTS:
        return None
    total, weight_sum = 0.0, 0.0
    for index in shared:
        weight = min(query.weights[index], reference.weights[index])
        total += weight * math.dist(query.points[index], reference.points[index]) ** 2
        weight_sum += weight
    if weight_sum <= 0:
        return None
    return math.sqrt(total / weight_sum), len(shared)


def rank_matches(query: PoseVector | None, references: Sequence[PoseReference], *,
                 top_k: int = 3, max_distance: float = DEFAULT_MAX_DISTANCE,
                 allow_mirror: bool = True) -> list[PoseMatch]:
    """Ordena as referências próximas; uma lista vazia significa sem boa candidata.

    max_distance é um limiar experimental em unidades do tronco. A comparação usa
    somente articulações confiáveis compartilhadas; joint_count informa a cobertura.
    mirrored=True indica que a imagem de referência deve ser exibida espelhada.
    """
    if type(top_k) is not int or top_k <= 0:
        raise ValueError("top_k deve ser um inteiro positivo.")
    if _number(max_distance) is None or max_distance < 0:
        raise ValueError("max_distance deve ser finita e maior ou igual a zero.")
    if query is None:
        return []
    matches = []
    for reference in references:
        direct = _distance(query, reference.pose)
        flipped = _distance(query, mirror_pose(reference.pose)) if allow_mirror else None
        candidates = [(distance[0], mirrored, distance[1])
                      for distance, mirrored in ((direct, False), (flipped, True))
                      if distance is not None]
        if not candidates:
            continue
        distance, mirrored, count = min(candidates)
        if distance <= max_distance:
            matches.append(PoseMatch(reference, distance, mirrored, count))
    return sorted(matches, key=lambda match: (match.distance, match.reference.id))[:top_k]


def _text(data: Mapping, key: str, *, required: bool = False) -> str:
    value = data.get(key, "")
    if not isinstance(value, str) or (required and not value.strip()):
        raise ValueError(f"Campo {key!r} deve ser um texto" + (" não vazio." if required else "."))
    return value.strip()


def reference_from_dict(data: Mapping, directory: Path) -> PoseReference:
    """Valida uma entrada e resolve somente imagens contidas na pasta do catálogo."""
    if not isinstance(data, Mapping):
        raise ValueError("Cada referência precisa ser um objeto JSON.")
    identifier, title = _text(data, "id", required=True), _text(data, "title", required=True)
    image = _text(data, "image", required=True)
    relative = PurePosixPath(image)
    if (relative.is_absolute() or ".." in relative.parts or "\\" in image
            or ":" in image or relative.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}):
        raise ValueError(f"Referência {identifier}: use um caminho relativo PNG/JPG/WebP sem '..'.")
    directory = Path(directory).resolve()
    image_path = (directory / relative).resolve()
    if not image_path.is_relative_to(directory):
        raise ValueError(f"Referência {identifier}: a imagem escapa da pasta do catálogo.")
    if not image_path.is_file():
        raise FileNotFoundError(f"Imagem de referência ausente: {image_path}")
    landmarks = data.get("landmarks")
    if (not isinstance(landmarks, list) or len(landmarks) != 33
            or any(not isinstance(point, Mapping) for point in landmarks)):
        raise ValueError(f"Referência {identifier}: esperado um array com 33 landmarks.")
    pose = extract_pose(landmarks, data.get("width"), data.get("height"))
    if pose is None:
        raise ValueError(f"Referência {identifier}: pose sem tronco e articulações confiáveis.")
    return PoseReference(identifier, title, image_path, pose,
                         _text(data, "source"), _text(data, "license"), _text(data, "credit"))


def load_catalog(path: str | Path) -> list[PoseReference]:
    """Lê schema_version=1 e valida identificadores, caminhos e poses do catálogo."""
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(data, Mapping) or type(data.get("schema_version")) is not int
            or data["schema_version"] != 1):
        raise ValueError("Catálogo precisa declarar schema_version: 1.")
    entries = data.get("references")
    if not isinstance(entries, list) or not entries:
        raise ValueError("Catálogo precisa conter ao menos uma referência.")
    references = [reference_from_dict(entry, path.parent) for entry in entries]
    ids = [reference.id for reference in references]
    if len(ids) != len(set(ids)):
        raise ValueError("Os identificadores das referências precisam ser únicos.")
    return references
