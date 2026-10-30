"""Verifica o ambiente do GestureLab sem abrir câmera ou baixar arquivos.

Por padrão, lê apenas a versão do Python e os metadados dos pacotes instalados.
Use --imports para carregar bibliotecas e --models para conferir os pesos.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path

if __package__:
    from .download_models import DEFAULT_DIRECTORY, MODELS, sha256
else:
    from download_models import DEFAULT_DIRECTORY, MODELS, sha256

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PYTHON = (3, 12)
OPENCV_DISTRIBUTIONS = (
    "opencv-python",
    "opencv-contrib-python",
    "opencv-python-headless",
    "opencv-contrib-python-headless",
)


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    message: str


def check_python() -> list[Check]:
    version = ".".join(map(str, sys.version_info[:3]))
    reference_version = ".".join(map(str, REFERENCE_PYTHON))
    return [
        Check(
            "Python",
            sys.version_info[:2] == REFERENCE_PYTHON,
            f"{version}; ambiente de referência: Python {reference_version}",
        ),
        Check("Arquitetura", sys.maxsize > 2**32, "Python precisa ser de 64 bits"),
    ]


def read_requirements(path: Path) -> dict[str, str]:
    requirements = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.partition("#")[0].strip()
        if not line:
            continue
        name, separator, version = line.partition("==")
        if not separator or not name or not version or any(char.isspace() for char in line):
            raise ValueError(f"{path.name}, linha {line_number}: esperado nome==versão")
        requirements[name] = version
    return requirements


def _installed_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def check_dependencies(requirements: dict[str, str]) -> list[Check]:
    checks = []
    for name, expected_version in requirements.items():
        installed_version = _installed_version(name)
        if installed_version is None:
            checks.append(Check(name, False, f"ausente; esperado {expected_version}"))
        else:
            checks.append(
                Check(
                    name,
                    installed_version == expected_version,
                    f"instalado {installed_version}; esperado {expected_version}",
                )
            )

    installed_opencv = [
        name for name in OPENCV_DISTRIBUTIONS if _installed_version(name) is not None
    ]
    if len(installed_opencv) > 1:
        checks.append(
            Check("OpenCV", False, "distribuições conflitantes: " + ", ".join(installed_opencv))
        )
    return checks


def check_imports() -> list[Check]:
    checks = []
    for name in ("numpy", "cv2", "mediapipe.tasks.python.vision"):
        try:
            importlib.import_module(name)
        except Exception as exc:
            # Bibliotecas nativas podem falhar com exceções além de ImportError.
            checks.append(Check(f"Import {name}", False, f"{type(exc).__name__}: {exc}"))
        else:
            checks.append(Check(f"Import {name}", True, "biblioteca carregada"))
    return checks


def check_models(selection: str, directory: Path) -> list[Check]:
    checks = []
    selected_models = MODELS if selection == "all" else [selection]
    for name in selected_models:
        filename, _, expected_hash = MODELS[name]
        path = directory / filename
        if not path.is_file():
            checks.append(Check(filename, False, f"arquivo ausente: {path}"))
            continue
        try:
            actual_hash = sha256(path)
        except OSError as exc:
            checks.append(Check(filename, False, f"não foi possível ler: {exc}"))
        else:
            matches = actual_hash == expected_hash
            message = "SHA-256 confere" if matches else "SHA-256 diferente do oficial"
            checks.append(Check(filename, matches, message))
    return checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--imports",
        action="store_true",
        help="Carrega bibliotecas; pode revelar dependências nativas ausentes.",
    )
    parser.add_argument(
        "--models",
        choices=[*MODELS, "all"],
        help="Verifica existência e SHA-256 dos modelos selecionados.",
    )
    parser.add_argument(
        "--directory",
        type=Path,
        default=DEFAULT_DIRECTORY,
        help="Pasta dos modelos; padrão: models na raiz do projeto.",
    )
    args = parser.parse_args(argv)

    checks = check_python()
    try:
        requirements = read_requirements(ROOT / "requirements.txt")
    except (OSError, ValueError) as exc:
        checks.append(Check("requirements.txt", False, str(exc)))
    else:
        checks.extend(check_dependencies(requirements))
    if args.imports:
        checks.extend(check_imports())
    if args.models:
        checks.extend(check_models(args.models, args.directory))

    print(f"Executável: {sys.executable}")
    for check in checks:
        print(f"[{'OK' if check.passed else 'FALHA'}] {check.name}: {check.message}")
    failures = sum(not check.passed for check in checks)
    if failures:
        print(f"\n{failures} verificação(ões) falharam. Consulte scripts/README.md.")
    else:
        print("\nTodas as verificações solicitadas passaram.")
    print("A câmera, a janela e a qualidade das detecções ainda precisam de teste manual.")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
