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
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(name: str, directory: Path) -> None:
    filename, url, expected = MODELS[name]
    target = directory / filename
    if target.exists():
        if sha256(target) != expected:
            raise ValueError(f"Hash inesperado em {target}; mova esse arquivo antes de tentar novamente.")
        print(f"OK (já existe): {filename}")
        return
    temporary = directory / (filename + ".part")
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "GestureLab/0.1"})
        with urllib.request.urlopen(request, timeout=60) as response, temporary.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
        actual = sha256(temporary)
        if actual != expected:
            raise ValueError(f"SHA-256 não confere para {filename}: {actual}")
        temporary.replace(target)
        print(f"OK: {filename} ({target.stat().st_size} bytes)\nSHA-256: {actual}")
    finally:
        temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", choices=MODELS, help="Baixa só o modelo escolhido.")
    parser.add_argument("--directory", type=Path, default=DEFAULT_DIRECTORY)
    args = parser.parse_args(argv)
    args.directory.mkdir(parents=True, exist_ok=True)
    try:
        for name in ([args.only] if args.only else MODELS):
            download(name, args.directory)
    except (OSError, ValueError, urllib.error.URLError) as exc:
        print(f"Falha no download: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
