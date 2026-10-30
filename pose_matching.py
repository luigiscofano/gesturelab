"""Busca geométrica de poses humanas em um catálogo local de imagens.

O descritor usa 12 articulações em pixels, centradas no quadril e divididas pelo
tamanho do tronco. A distância é a raiz da média ponderada dos erros quadráticos
(RMS), não probabilidade de acerto. Testes e leitura do catálogo usam somente a
biblioteca padrão, sem carregar bibliotecas de visão.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

# Pares de ombros, cotovelos, punhos, quadris, joelhos e tornozelos.
BODY_JOINTS = (11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28)
TORSO_JOINTS = (11, 12, 23, 24)
POSE_CONNECTIONS = (
    (11, 12),
    (11, 13),
    (13, 15),
    (12, 14),
    (14, 16),
    (11, 23),
    (12, 24),
    (23, 24),
    (23, 25),
    (25, 27),
    (24, 26),
    (26, 28),
)
MIN_JOINTS = 8
DEFAULT_MAX_DISTANCE = 0.8
POSE_LANDMARK_COUNT = 33
_MIN_TORSO_SCALE_PX = 1.0
_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
# BODY_JOINTS alterna esquerda/direita em cada par anatômico.
_MIRRORED_JOINT_ORDER = (1, 0, 3, 2, 5, 4, 7, 6, 9, 8, 11, 10)
Point = tuple[float, float]


@dataclass(frozen=True)
class PoseVector:
    """Pontos na ordem de BODY_JOINTS; None indica uma articulação descartada."""

    points: tuple[Point | None, ...]
    # A confiança determina o peso de cada articulação na comparação.
    weights: tuple[float, ...]

    @property
    def joint_count(self) -> int:
        """Conta somente os pontos que passaram pela validação."""
        return sum(point is not None for point in self.points)


@dataclass(frozen=True)
class PoseReference:
    """Reúne uma imagem do catálogo, sua pose e os metadados de origem."""

    id: str
    title: str
    image_path: Path
    pose: PoseVector
    source: str = ""
    license: str = ""
    credit: str = ""


@dataclass(frozen=True)
class PoseMatch:
    """Guarda uma correspondência, sua distância e a orientação escolhida."""

    reference: PoseReference
    distance: float
    mirrored: bool
    joint_count: int


def _landmark_field(landmark: object, key: str, default: object = None) -> object:
    """Lê um campo de ponto, seja ele um dicionário JSON ou um objeto MediaPipe."""
    if isinstance(landmark, Mapping):
        return landmark.get(key, default)
    return getattr(landmark, key, default)


def _finite_number(value: object) -> float | None:
    """Descarta booleanos e números indefinidos ou infinitos."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(value) else None


def _read_joint(
    landmark: object,
    width: int,
    height: int,
    min_visibility: float,
) -> tuple[Point, float] | None:
    """Valida o ponto e retorna sua posição em pixels com o peso de confiança."""
    x = _finite_number(_landmark_field(landmark, "x"))
    y = _finite_number(_landmark_field(landmark, "y"))
    visibility = _landmark_field(landmark, "visibility", 1.0)
    presence = _landmark_field(landmark, "presence", 1.0)
    visibility = _finite_number(1.0 if visibility is None else visibility)
    presence = _finite_number(1.0 if presence is None else presence)
    if (
        x is None
        or y is None
        or visibility is None
        or presence is None
        or not 0 <= x <= 1
        or not 0 <= y <= 1
        or not 0 <= visibility <= 1
        or not 0 <= presence <= 1
    ):
        return None
    # Os dois indicadores precisam atingir o mínimo para o ponto ser aproveitado.
    weight = min(visibility, presence)
    if weight <= 0 or weight < min_visibility:
        return None
    return (x * width, y * height), weight


def _midpoint(first: Point, second: Point) -> Point:
    """Encontra o centro entre duas articulações."""
    return (first[0] + second[0]) / 2, (first[1] + second[1]) / 2


def _torso_frame(points: Mapping[int, Point]) -> tuple[Point, float]:
    """Obtém a origem no quadril e a medida usada para ajustar a escala."""
    left_shoulder, right_shoulder = points[11], points[12]
    left_hip, right_hip = points[23], points[24]
    pelvis = _midpoint(left_hip, right_hip)
    shoulders = _midpoint(left_shoulder, right_shoulder)

    # Os comprimentos laterais evitam escala nula quando os centros se aproximam
    # na projeção. Um tronco inteiramente degenerado continua rejeitado.
    scale = max(
        math.dist(pelvis, shoulders),
        (math.dist(left_shoulder, left_hip) + math.dist(right_shoulder, right_hip)) / 2,
        math.dist(left_shoulder, right_shoulder) / 2,
        math.dist(left_hip, right_hip) / 2,
    )
    return pelvis, scale


def extract_pose(
    landmarks: Sequence[object], width: int, height: int, *, min_visibility: float = 0.5
) -> PoseVector | None:
    """Normaliza 33 landmarks MediaPipe; retorna None para enquadramento insuficiente.

    x/y devem estar normalizados na imagem original. width/height corrigem a
    proporção da imagem antes de calcular distâncias. Não remove rotação do corpo.
    Ombros e quadris devem estar visíveis, além de pelo menos oito articulações.
    Pontos fora da imagem, não finitos ou com baixa visibility/presence são omitidos.
    """
    if type(width) is not int or type(height) is not int or width <= 0 or height <= 0:
        raise ValueError("As dimensões da imagem devem ser inteiros positivos.")
    if _finite_number(min_visibility) is None or not 0 <= min_visibility <= 1:
        raise ValueError("min_visibility deve estar entre 0 e 1.")
    if len(landmarks) != POSE_LANDMARK_COUNT:
        return None

    points: dict[int, Point] = {}
    weights: dict[int, float] = {}
    for index in BODY_JOINTS:
        joint = _read_joint(landmarks[index], width, height, min_visibility)
        if joint is not None:
            points[index], weights[index] = joint
    if len(points) < MIN_JOINTS or any(index not in points for index in TORSO_JOINTS):
        return None

    pelvis, scale = _torso_frame(points)
    if scale < _MIN_TORSO_SCALE_PX:
        return None
    # Centralizar e ajustar a escala reduz diferenças de posição e tamanho entre fotos.
    # A ordem dos pontos é fixa; articulações ausentes continuam representadas por None.
    normalized = tuple(
        ((points[index][0] - pelvis[0]) / scale, (points[index][1] - pelvis[1]) / scale)
        if index in points
        else None
        for index in BODY_JOINTS
    )
    return PoseVector(normalized, tuple(weights.get(index, 0.0) for index in BODY_JOINTS))


def mirror_pose(pose: PoseVector) -> PoseVector:
    """Espelha x e troca os lados anatômicos; pares adjacentes são esquerda/direita."""
    points = []
    weights = []
    for opposite_index in _MIRRORED_JOINT_ORDER:
        point = pose.points[opposite_index]
        points.append((-point[0], point[1]) if point is not None else None)
        weights.append(pose.weights[opposite_index])
    return PoseVector(tuple(points), tuple(weights))


def _pose_distance(query: PoseVector, reference: PoseVector) -> tuple[float, int] | None:
    """Calcula a distância usando articulações presentes nas duas poses."""
    shared_indices = [
        index
        for index in range(len(BODY_JOINTS))
        if query.points[index] is not None and reference.points[index] is not None
    ]
    if len(shared_indices) < MIN_JOINTS:
        return None
    weighted_squared_error = 0.0
    total_weight = 0.0
    for index in shared_indices:
        # Um ponto pouco confiável em qualquer imagem contribui menos para a distância.
        weight = min(query.weights[index], reference.weights[index])
        weighted_squared_error += (
            weight * math.dist(query.points[index], reference.points[index]) ** 2
        )
        total_weight += weight
    if total_weight <= 0:
        return None
    return math.sqrt(weighted_squared_error / total_weight), len(shared_indices)


def _best_orientation(
    query: PoseVector,
    reference: PoseReference,
    allow_mirror: bool,
) -> PoseMatch | None:
    """Testa as orientações permitidas e conserva a de menor distância."""
    orientations = [(False, reference.pose)]
    if allow_mirror:
        orientations.append((True, mirror_pose(reference.pose)))
    best_match = None
    for mirrored, pose in orientations:
        measurement = _pose_distance(query, pose)
        if measurement is None:
            continue
        distance, joint_count = measurement
        # Em empate, conserva a orientação original da imagem.
        if best_match is None or distance < best_match.distance:
            best_match = PoseMatch(reference, distance, mirrored, joint_count)
    return best_match


def rank_matches(
    query: PoseVector | None,
    references: Sequence[PoseReference],
    *,
    top_k: int = 3,
    max_distance: float = DEFAULT_MAX_DISTANCE,
    allow_mirror: bool = True,
) -> list[PoseMatch]:
    """Ordena as referências próximas; uma lista vazia significa sem boa candidata.

    max_distance é um limiar experimental em unidades do tronco. A comparação usa
    somente articulações confiáveis compartilhadas; joint_count informa a cobertura.
    mirrored=True indica que a imagem de referência deve ser exibida espelhada.
    """
    if type(top_k) is not int or top_k <= 0:
        raise ValueError("top_k deve ser um inteiro positivo.")
    if _finite_number(max_distance) is None or max_distance < 0:
        raise ValueError("max_distance deve ser finita e maior ou igual a zero.")
    if query is None:
        return []
    matches: list[PoseMatch] = []
    for reference in references:
        match = _best_orientation(query, reference, allow_mirror)
        if match is not None and match.distance <= max_distance:
            matches.append(match)
    # O identificador desempata distâncias iguais, mantendo a ordenação reproduzível.
    return sorted(matches, key=lambda match: (match.distance, match.reference.id))[:top_k]


def _catalog_text(data: Mapping, key: str, *, required: bool = False) -> str:
    """Lê um metadado textual e verifica se campos obrigatórios estão preenchidos."""
    value = data.get(key, "")
    if not isinstance(value, str) or (required and not value.strip()):
        qualifier = " não vazio" if required else ""
        raise ValueError(f"Campo {key!r} deve ser um texto{qualifier}.")
    return value.strip()


def _resolve_image_path(image: str, directory: Path, identifier: str) -> Path:
    """Confere o formato e limita as referências à pasta do catálogo."""
    relative = PurePosixPath(image)
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or "\\" in image
        or ":" in image
        or relative.suffix.lower() not in _IMAGE_EXTENSIONS
    ):
        raise ValueError(f"Referência {identifier}: use um caminho relativo PNG/JPG/WebP sem '..'.")
    directory = Path(directory).resolve()
    # Links simbólicos também precisam apontar para dentro da pasta permitida.
    image_path = (directory / relative).resolve()
    if not image_path.is_relative_to(directory):
        raise ValueError(f"Referência {identifier}: a imagem escapa da pasta do catálogo.")
    if not image_path.is_file():
        raise FileNotFoundError(f"Imagem de referência ausente: {image_path}")
    return image_path


def reference_from_dict(data: Mapping, directory: Path) -> PoseReference:
    """Valida uma entrada e resolve somente imagens contidas na pasta do catálogo."""
    if not isinstance(data, Mapping):
        raise ValueError("Cada referência precisa ser um objeto JSON.")
    identifier = _catalog_text(data, "id", required=True)
    title = _catalog_text(data, "title", required=True)
    image = _catalog_text(data, "image", required=True)
    image_path = _resolve_image_path(image, directory, identifier)
    landmarks = data.get("landmarks")
    if (
        not isinstance(landmarks, list)
        or len(landmarks) != POSE_LANDMARK_COUNT
        or any(not isinstance(point, Mapping) for point in landmarks)
    ):
        raise ValueError(f"Referência {identifier}: esperado um array com 33 landmarks.")
    pose = extract_pose(landmarks, data.get("width"), data.get("height"))
    if pose is None:
        raise ValueError(f"Referência {identifier}: pose sem tronco e articulações confiáveis.")
    return PoseReference(
        id=identifier,
        title=title,
        image_path=image_path,
        pose=pose,
        source=_catalog_text(data, "source"),
        license=_catalog_text(data, "license"),
        credit=_catalog_text(data, "credit"),
    )


def load_catalog(path: str | Path) -> list[PoseReference]:
    """Lê schema_version=1 e valida identificadores, caminhos e poses do catálogo."""
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(data, Mapping)
        or type(data.get("schema_version")) is not int
        or data["schema_version"] != 1
    ):
        raise ValueError("Catálogo precisa declarar schema_version: 1.")
    entries = data.get("references")
    if not isinstance(entries, list) or not entries:
        raise ValueError("Catálogo precisa conter ao menos uma referência.")
    references = [reference_from_dict(entry, path.parent) for entry in entries]
    # Identificadores únicos permitem distinguir referências durante a busca e a exibição.
    ids = [reference.id for reference in references]
    if len(ids) != len(set(ids)):
        raise ValueError("Os identificadores das referências precisam ser únicos.")
    return references
