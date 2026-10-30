"""Verifica o ambiente do GestureLab sem abrir câmera ou baixar arquivos.

Por padrão, lê apenas a versão do Python e os metadados dos pacotes instalados.
Use --imports para carregar bibliotecas e --models para conferir os pesos.
"""

from __future__ import annotations

import argparse
import importlib
from importlib import metadata
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__:
    from .download_models import DEFAULT_DIRECTORY, MODELS, sha256
else:
    from download_models import DEFAULT_DIRECTORY, MODELS, sha256

ROOT = Path(__file__).resolve().parents[1]
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
    return [
        Check("Python", sys.version_info[:2] == (3, 12),
              f"{version}; ambiente de referência: Python 3.12"),
        Check("Arquitetura", sys.maxsize > 2**32, "Python precisa ser de 64 bits"),
    ]


def read_requirements(path: Path) -> dict[str, str]:
    requirements = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.partition("#")[0].strip()
        if not line:
            continue
        name, separator, version = line.partition("==")
        if not separator or not name or not version or any(char.isspace() for char in line):
            raise ValueError(f"{path.name}, linha {number}: esperado nome==versão")
        requirements[name] = version
    return requirements


def check_dependencies(requirements: dict[str, str]) -> list[Check]:
    checks = []
    for name, expected in requirements.items():
        try:
            actual = metadata.version(name)
        except metadata.PackageNotFoundError:
            checks.append(Check(name, False, f"ausente; esperado {expected}"))
        else:
            checks.append(Check(name, actual == expected,
                                f"instalado {actual}; esperado {expected}"))

    installed_opencv = []
    for name in OPENCV_DISTRIBUTIONS:
        try:
            metadata.version(name)
        except metadata.PackageNotFoundError:
            continue
        installed_opencv.append(name)
    if len(installed_opencv) > 1:
        checks.append(Check("OpenCV", False,
                            "distribuições conflitantes: " + ", ".join(installed_opencv)))
    return checks


def check_imports() -> list[Check]:
    checks = []
    for name in ("numpy", "cv2", "mediapipe.tasks.python.vision"):
        try:
            importlib.import_module(name)
        except Exception as exc:
            # ImportError e OSError cobrem pacotes ausentes e várias falhas de DLL;
            # outras exceções de inicialização também devem virar diagnóstico.
            checks.append(Check(f"Import {name}", False, f"{type(exc).__name__}: {exc}"))
        else:
            checks.append(Check(f"Import {name}", True, "biblioteca carregada"))
    return checks


def check_models(selection: str, directory: Path) -> list[Check]:
    checks = []
    for name in (MODELS if selection == "all" else [selection]):
        filename, _, expected = MODELS[name]
        path = directory / filename
        if not path.is_file():
            checks.append(Check(filename, False, f"arquivo ausente: {path}"))
            continue
        try:
            actual = sha256(path)
        except OSError as exc:
            checks.append(Check(filename, False, f"não foi possível ler: {exc}"))
        else:
            message = "SHA-256 confere" if actual == expected else "SHA-256 diferente do oficial"
            checks.append(Check(filename, actual == expected, message))
    return checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--imports", action="store_true",
                        help="Carrega bibliotecas; pode revelar dependências nativas ausentes.")
    parser.add_argument("--models", choices=[*MODELS, "all"],
                        help="Verifica existência e SHA-256 dos modelos selecionados.")
    parser.add_argument("--directory", type=Path, default=DEFAULT_DIRECTORY,
                        help="Pasta dos modelos; padrão: models na raiz do projeto.")
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
