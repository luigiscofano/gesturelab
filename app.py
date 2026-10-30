"""GestureLab: mãos, escrita no ar e busca de imagens por pose corporal.

Exemplos:
    python app.py --mode hands
    python app.py --mode gestures
    python app.py --mode airwrite
    python app.py --mode posematch
    python app.py --mode hands --image foto.jpg --output resultado.jpg
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

from hand_app import run_hand_mode
from pose_match_app import run_posematch
from vision_runtime import MODEL_NAMES, load_dependencies

ROOT = Path(__file__).resolve().parent


def probability(value: str) -> float:
    """Converte uma opção do terminal em um valor entre zero e um."""
    number = float(value)
    if not 0.0 <= number <= 1.0:
        raise argparse.ArgumentTypeError("Use um número entre 0 e 1.")
    return number


def positive_int(value: str) -> int:
    """Aceita apenas contagens positivas, como o limite de frames."""
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("Use um inteiro positivo.")
    return number


def nonnegative_float(value: str) -> float:
    """Valida medidas que podem ser zero, mas não negativas nem infinitas."""
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise argparse.ArgumentTypeError("Use um número finito maior ou igual a zero.")
    return number


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Lê as opções do terminal, aplica padrões e rejeita combinações incompatíveis."""
    parser = argparse.ArgumentParser(description=__doc__)
    # Opções gerais escolhem o modo, a câmera e a apresentação dos resultados.
    parser.add_argument("--mode", choices=MODEL_NAMES, default="hands")
    parser.add_argument("--camera", type=int, default=0, help="Índice da webcam, normalmente 0.")
    parser.add_argument(
        "--num-hands", type=positive_int, default=2, help="Quantidade máxima nos modos de mãos."
    )
    parser.add_argument(
        "--threshold",
        type=probability,
        default=0.65,
        help="Limiar do score de gesto; 0.65 é só ponto de partida.",
    )
    parser.add_argument(
        "--mirror",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Espelha a visualização, nunca o input do modelo.",
    )
    parser.add_argument("--show-indices", action="store_true", help="Mostra os índices 0 a 20.")
    parser.add_argument("--model", type=Path, help="Substitui o arquivo .task do modo escolhido.")
    # Uma foto é processada uma vez; a webcam precisa de um ciclo de captura.
    parser.add_argument("--image", type=Path, help="Processa uma foto sem abrir a webcam/janela.")
    parser.add_argument("--output", type=Path, help="Salva a foto anotada; exige --image.")
    parser.add_argument(
        "--headless", action="store_true", help="Webcam sem janela; exige --max-frames."
    )
    parser.add_argument(
        "--max-frames", type=positive_int, help="Encerra após este número de frames."
    )
    # Controles da caneta: fundo, suavização do movimento e espessura do traço.
    parser.add_argument(
        "--canvas",
        action="store_true",
        help="Em airwrite, inicia com fundo branco em vez da webcam.",
    )
    parser.add_argument(
        "--smooth-ms",
        type=nonnegative_float,
        default=45.0,
        help="Em airwrite, constante de suavização EMA em ms; 0 desliga.",
    )
    parser.add_argument(
        "--pen-width",
        type=positive_int,
        default=5,
        help="Em airwrite, espessura do traço em pixels.",
    )
    # A busca corporal escolhe uma galeria e um limite de distância entre poses.
    parser.add_argument(
        "--gallery", type=Path, help="Em posematch, catálogo JSON de imagens e poses."
    )
    parser.add_argument(
        "--match-threshold",
        type=nonnegative_float,
        help="Em posematch, distância máxima aceita; padrão experimental: 0.8.",
    )
    args = parser.parse_args(argv)
    # Estas verificações acontecem antes de carregar modelos ou abrir a câmera.
    if args.output and not args.image:
        parser.error("--output só é permitido junto com --image.")
    if args.headless and not args.image and not args.max_frames:
        parser.error("--headless com webcam exige --max-frames.")
    if args.mode == "airwrite" and args.image:
        parser.error("airwrite precisa de uma sequência da webcam; --image não é compatível.")
    if args.canvas and args.mode != "airwrite":
        parser.error("--canvas só está disponível em --mode airwrite.")
    if args.mode != "posematch" and (args.gallery is not None or args.match_threshold is not None):
        parser.error("--gallery e --match-threshold só estão disponíveis em --mode posematch.")
    if args.gallery is None:
        args.gallery = ROOT / "pose_gallery" / "catalog.json"
    if args.match_threshold is None:
        args.match_threshold = 0.8
    return args


def main(argv: list[str] | None = None) -> int:
    """Inicia o modo escolhido e devolve ao terminal zero para sucesso ou um para erro."""
    args = parse_args(argv)
    try:
        dependencies = load_dependencies()
        if args.mode == "posematch":
            run_posematch(args, dependencies)
        else:
            run_hand_mode(args, dependencies)
    except KeyboardInterrupt:
        return 0
    except (RuntimeError, OSError, ValueError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    # Importar este módulo não inicia a câmera; executar o arquivo chama main().
    raise SystemExit(main())
