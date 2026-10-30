"""Baixa modelos oficiais versionados e verifica SHA-256.

Somente este script acessa a rede explicitamente. O aplicativo não grava vídeo.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_DIRECTORY = Path(__file__).resolve().parents[1] / "models"
CHUNK_SIZE_BYTES = 1024 * 1024
DOWNLOAD_TIMEOUT_SECONDS = 60
# Cada modelo define o nome local, a origem e o hash esperado dos seus bytes.
MODELS = {
    "hands": (
        "hand_landmarker.task",
        "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
        "fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1",
    ),
    "gestures": (
        "gesture_recognizer.task",
        "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task",
        "97952348cf6a6a4915c2ea1496b4b37ebabc50cbbf80571435643c455f2b0482",
    ),
    "poses": (
        "pose_landmarker_lite.task",
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task",
        "59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a",
    ),
}


def sha256(path: Path) -> str:
    """Calcula um resumo do arquivo para conferir sua integridade."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        # A leitura em blocos evita carregar o modelo inteiro na memória.
        for chunk in iter(lambda: stream.read(CHUNK_SIZE_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(name: str, directory: Path) -> None:
    """Reutiliza um modelo válido ou baixa e verifica uma nova cópia."""
    filename, url, expected_hash = MODELS[name]
    target = directory / filename
    if target.exists():
        if sha256(target) != expected_hash:
            raise ValueError(
                f"Hash inesperado em {target}; mova esse arquivo antes de tentar novamente."
            )
        print(f"OK (já existe): {filename}")
        return
    # O arquivo incompleto fica separado do modelo que o aplicativo pode carregar.
    temporary = directory / (filename + ".part")
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "GestureLab/0.1"})
        with (
            urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response,
            temporary.open("wb") as output,
        ):
            while chunk := response.read(CHUNK_SIZE_BYTES):
                output.write(chunk)
        actual_hash = sha256(temporary)
        if actual_hash != expected_hash:
            raise ValueError(f"SHA-256 não confere para {filename}: {actual_hash}")
        # Só publica o nome definitivo depois que o conteúdo foi conferido.
        temporary.replace(target)
        print(f"OK: {filename} ({target.stat().st_size} bytes)\nSHA-256: {actual_hash}")
    finally:
        # Remove sobras de uma transferência ou verificação interrompida.
        temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    """Lê as opções do terminal e baixa os modelos solicitados."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", choices=MODELS, help="Baixa só o modelo escolhido.")
    parser.add_argument("--directory", type=Path, default=DEFAULT_DIRECTORY)
    args = parser.parse_args(argv)
    args.directory.mkdir(parents=True, exist_ok=True)
    try:
        selected_models = [args.only] if args.only else MODELS
        for name in selected_models:
            download(name, args.directory)
    except (OSError, ValueError, urllib.error.URLError) as exc:
        print(f"Falha no download: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
