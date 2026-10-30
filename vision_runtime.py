"""Dependências e operações de visão compartilhadas pelos modos do aplicativo."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from file_io import write_new_files

# Cada modo reutiliza o modelo adequado à tarefa, carregado a partir de um arquivo .task.
MODEL_NAMES = {
    "hands": "hand_landmarker.task",
    "gestures": "gesture_recognizer.task",
    "airwrite": "hand_landmarker.task",
    "posematch": "pose_landmarker_lite.task",
}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
# A câmera pode entregar outra resolução; os modos consultam o tamanho real de cada frame.
CAMERA_WIDTH = 960
CAMERA_HEIGHT = 540
QUIT_KEYS = {ord("q"), ord("Q"), 27}


@dataclass(frozen=True)
class VisionDependencies:
    """Reúne as bibliotecas carregadas e permite substituí-las por objetos de teste."""

    cv2: ModuleType
    mediapipe: ModuleType
    numpy: ModuleType
    tasks: ModuleType
    vision: ModuleType


def load_dependencies() -> VisionDependencies:
    """Carrega a visão só ao executar um modo; ajuda e testes puros dispensam as libs."""
    try:
        import cv2
        import mediapipe
        import numpy
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision
    except ImportError as exc:
        raise RuntimeError(
            "Instale as dependências no ambiente virtual: python -m pip install -r requirements.txt"
        ) from exc
    return VisionDependencies(
        cv2=cv2,
        mediapipe=mediapipe,
        numpy=numpy,
        tasks=python,
        vision=vision,
    )


def to_mediapipe_image(frame, dependencies: VisionDependencies):
    """Mantém a imagem original; o espelhamento pertence apenas à apresentação."""
    # OpenCV usa a ordem de cores BGR; o MediaPipe recebe RGB.
    rgb = dependencies.cv2.cvtColor(frame, dependencies.cv2.COLOR_BGR2RGB)
    # Garante que os pixels estejam em um bloco contínuo de memória para o modelo.
    rgb = dependencies.numpy.ascontiguousarray(rgb)
    return dependencies.mediapipe.Image(
        image_format=dependencies.mediapipe.ImageFormat.SRGB,
        data=rgb,
    )


def read_image(path: Path, cv2, np, *, invalid_message="Imagem inválida ou formato não suportado"):
    """Lê uma fotografia do disco e informa quando ela não pode ser decodificada."""
    # Leitura por bytes também aceita caminhos com acentos no Windows.
    try:
        image = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"Não foi possível ler a imagem: {path}") from exc
    if image is None:
        raise RuntimeError(f"{invalid_message}: {path}")
    return image


def write_image(path: Path, image, cv2, *, encode_error: str) -> None:
    """Codifica a imagem no formato escolhido e grava uma saída sem sobrescrita."""
    extension = path.suffix.lower()
    if extension not in IMAGE_EXTENSIONS:
        raise ValueError("--output deve terminar em .png, .jpg, .jpeg ou .webp.")
    encoded_ok, encoded = cv2.imencode(extension, image)
    if not encoded_ok:
        raise RuntimeError(encode_error)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_new_files({path: encoded.tobytes()})


@contextmanager
def camera_session(cv2, camera_index: int, *, headless: bool):
    """Libera a captura mesmo quando a abertura, a leitura ou a inferência falha."""
    capture = cv2.VideoCapture(camera_index)
    try:
        if not capture.isOpened():
            raise RuntimeError(
                f"Webcam {camera_index} indisponível. Feche outros apps, permita a câmera "
                "no sistema e tente --camera 1."
            )
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        # O bloco with usa a câmera aqui; ao terminar, o finally libera os recursos.
        yield capture
    finally:
        capture.release()
        if not headless:
            cv2.destroyAllWindows()


def read_camera_frame(capture):
    """Obtém o próximo quadro da câmera e interrompe a execução se a captura falhar."""
    frame_ok, frame = capture.read()
    if not frame_ok or frame is None:
        raise RuntimeError("A webcam abriu, mas não entregou um frame válido.")
    return frame
