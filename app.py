"""GestureLab: landmarks e gestos de mão com OpenCV + MediaPipe Tasks.

Exemplos:
    python app.py --mode hands
    python app.py --mode gestures
    python app.py --mode airwrite
    python app.py --mode hands --image foto.jpg --output resultado.jpg
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

from airwriting import AirWriter, writing_pose
from core import (
    HAND_CONNECTIONS,
    FrameClock,
    gesture_label,
    handedness_label,
    pixel_point,
)

ROOT = Path(__file__).resolve().parent
MODEL_NAMES = {
    "hands": "hand_landmarker.task",
    "gestures": "gesture_recognizer.task",
    "airwrite": "hand_landmarker.task",
}


def probability(value: str) -> float:
    number = float(value)
    if not 0.0 <= number <= 1.0:
        raise argparse.ArgumentTypeError("Use um número entre 0 e 1.")
    return number


def positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("Use um inteiro positivo.")
    return number


def nonnegative_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise argparse.ArgumentTypeError("Use um número finito maior ou igual a zero.")
    return number


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=MODEL_NAMES, default="hands")
    parser.add_argument("--camera", type=int, default=0, help="Índice da webcam, normalmente 0.")
    parser.add_argument("--num-hands", type=positive_int, default=2)
    parser.add_argument("--threshold", type=probability, default=0.65,
                        help="Limiar do score de gesto; 0.65 é só ponto de partida.")
    parser.add_argument("--mirror", action=argparse.BooleanOptionalAction, default=True,
                        help="Espelha a visualização, nunca o input do modelo.")
    parser.add_argument("--show-indices", action="store_true", help="Mostra os índices 0 a 20.")
    parser.add_argument("--model", type=Path, help="Substitui o arquivo .task do modo escolhido.")
    parser.add_argument("--image", type=Path, help="Processa uma foto sem abrir a webcam/janela.")
    parser.add_argument("--output", type=Path, help="Salva a foto anotada; exige --image.")
    parser.add_argument("--headless", action="store_true", help="Webcam sem janela; exige --max-frames.")
    parser.add_argument("--max-frames", type=positive_int, help="Encerra após este número de frames.")
    parser.add_argument("--canvas", action="store_true",
                        help="Em airwrite, inicia com fundo branco em vez da webcam.")
    parser.add_argument("--smooth-ms", type=nonnegative_float, default=45.0,
                        help="Em airwrite, constante de suavização EMA em ms; 0 desliga.")
    parser.add_argument("--pen-width", type=positive_int, default=5,
                        help="Em airwrite, espessura do traço em pixels.")
    args = parser.parse_args(argv)
    if args.output and not args.image:
        parser.error("--output só é permitido junto com --image.")
    if args.headless and not args.image and not args.max_frames:
        parser.error("--headless com webcam exige --max-frames.")
    if args.mode == "airwrite" and args.image:
        parser.error("airwrite precisa de uma sequência da webcam; --image não é compatível.")
    if args.canvas and args.mode != "airwrite":
        parser.error("--canvas só está disponível em --mode airwrite.")
    return args


def load_dependencies():
    # Import tardio: --help e testes das funções puras não exigem as bibliotecas de visão.
    try:
        import cv2
        import mediapipe as mp
        import numpy as np
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision
    except ImportError as exc:
        raise RuntimeError(
            "Instale as dependências no ambiente virtual: python -m pip install -r requirements.txt"
        ) from exc
    return cv2, mp, np, python, vision


def create_task(args, python, vision):
    model_path = args.model or ROOT / "models" / MODEL_NAMES[args.mode]
    if not model_path.is_file():
        raise FileNotFoundError(
            f"Modelo não encontrado: {model_path}\n"
            "Baixe os modelos com: python scripts/download_models.py"
        )
    running_mode = vision.RunningMode.IMAGE if args.image else vision.RunningMode.VIDEO
    base = python.BaseOptions(model_asset_path=str(model_path))
    common = {
        "base_options": base,
        "running_mode": running_mode,
        # Detectar pelo menos duas permite interromper a caneta quando ambas aparecem.
        "num_hands": max(2, args.num_hands) if args.mode == "airwrite" else args.num_hands,
        "min_hand_detection_confidence": 0.5,
        "min_hand_presence_confidence": 0.5,
        "min_tracking_confidence": 0.5,
    }
    if args.mode in {"hands", "airwrite"}:
        return vision.HandLandmarker.create_from_options(vision.HandLandmarkerOptions(**common))
    return vision.GestureRecognizer.create_from_options(vision.GestureRecognizerOptions(**common))


def process_frame(task, frame, mode, timestamp_ms, dependencies):
    cv2, mp, np, _, _ = dependencies
    # OpenCV lê BGR. O modelo exige RGB contíguo, sem flip horizontal.
    rgb = np.ascontiguousarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    if timestamp_ms is None:
        return task.detect(image) if mode in {"hands", "airwrite"} else task.recognize(image)
    if mode in {"hands", "airwrite"}:
        return task.detect_for_video(image, timestamp_ms)
    return task.recognize_for_video(image, timestamp_ms)


def result_summary(result, args) -> dict:
    hands = []
    for index, landmarks in enumerate(result.hand_landmarks):
        handedness = result.handedness[index][0] if result.handedness[index] else None
        hand = {
            "handedness": handedness.category_name if handedness else None,
            "handedness_score": handedness.score if handedness else None,
            "landmark_count": len(landmarks),
            "landmarks": [{"x": p.x, "y": p.y, "z": p.z} for p in landmarks],
        }
        if args.mode == "gestures":
            candidates = result.gestures[index] if index < len(result.gestures) else []
            category = max(candidates, key=lambda item: item.score) if candidates else None
            score = category.score if category else 0.0
            name = category.category_name if category else None
            hand.update({"gesture_raw": name, "gesture_score": score,
                         "label": gesture_label(name, score, args.threshold)})
        hands.append(hand)
    return {"mode": args.mode, "hand_count": len(hands), "hands": hands}


def draw_result(frame, result, args, cv2, fps: float | None = None):
    # O resultado é calculado na imagem original; só agora espelhamos o canvas.
    canvas = cv2.flip(frame, 1) if args.mirror else frame.copy()
    height, width = canvas.shape[:2]
    summary = result_summary(result, args)
    for index, landmarks in enumerate(result.hand_landmarks):
        points = [pixel_point(p.x, p.y, width, height, args.mirror) for p in landmarks]
        for start, end in HAND_CONNECTIONS:
            cv2.line(canvas, points[start], points[end], (245, 245, 245), 2, cv2.LINE_AA)
        for landmark_id, point in enumerate(points):
            cv2.circle(canvas, point, 4, (50, 70, 245), -1, cv2.LINE_AA)
            if args.show_indices:
                cv2.putText(canvas, str(landmark_id), (point[0] + 4, point[1] - 4),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.35, (20, 230, 230), 1, cv2.LINE_AA)
        hand = summary["hands"][index]
        label = handedness_label(hand["handedness"])
        if args.mode == "gestures":
            label += f" | {hand['label']} | score {hand['gesture_score']:.2f}"
        # Rótulos fixos no canto evitam sobreposição quando as mãos se cruzam.
        put_text(canvas, label, (12, 58 + 26 * index), cv2)

    status = f"GestureLab | {args.mode} | maos: {summary['hand_count']}"
    if fps is not None:
        status += f" | FPS loop: {fps:.1f}"
    put_text(canvas, status, (12, 28), cv2)
    if not result.hand_landmarks:
        put_text(canvas, "SEM MAO DETECTADA", (12, 58), cv2)
    if not args.image:
        put_text(canvas, "Q ou Esc: sair", (12, height - 14), cv2)
    return canvas, summary


def put_text(canvas, text, point, cv2):
    # Fundo escuro e escala adaptativa mantêm rótulos legíveis em fotos pequenas.
    font = cv2.FONT_HERSHEY_SIMPLEX
    base_width = cv2.getTextSize(text, font, 1.0, 1)[0][0]
    scale = min(0.55, max(0.1, (canvas.shape[1] - point[0] - 10) / max(base_width, 1)))
    (text_width, text_height), baseline = cv2.getTextSize(text, font, scale, 1)
    cv2.rectangle(canvas, (point[0] - 4, point[1] - text_height - 5),
                  (point[0] + text_width + 4, point[1] + baseline + 3), (20, 25, 20), -1)
    cv2.putText(canvas, text, point, font, scale, (245, 245, 245), 1, cv2.LINE_AA)


def run_image(task, args, deps):
    cv2, _, np, _, _ = deps
    # imdecode/tofile funcionam também com caminhos Windows que contêm acentos.
    try:
        frame = cv2.imdecode(np.fromfile(args.image, dtype=np.uint8), cv2.IMREAD_COLOR)
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"Não foi possível ler a imagem: {args.image}") from exc
    if frame is None:
        raise RuntimeError(f"Formato de imagem não suportado: {args.image}")
    started = time.perf_counter()
    result = process_frame(task, frame, args.mode, None, deps)
    inference_ms = (time.perf_counter() - started) * 1000
    canvas, summary = draw_result(frame, result, args, cv2)
    summary["inference_ms_single_image"] = round(inference_ms, 2)
    summary["input_shape"] = list(frame.shape)
    summary["display_mirrored"] = args.mirror
    if args.output:
        if args.output.resolve() == args.image.resolve():
            raise ValueError("Escolha --output diferente da imagem original.")
        if args.output.exists():
            raise FileExistsError(f"Saída já existe; escolha outro nome: {args.output}")
        extension = args.output.suffix.lower()
        if extension not in {".png", ".jpg", ".jpeg", ".webp"}:
            raise ValueError("--output deve terminar em .png, .jpg, .jpeg ou .webp.")
        ok, encoded = cv2.imencode(extension, canvas)
        if not ok:
            raise RuntimeError("Não foi possível codificar a imagem anotada.")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        encoded.tofile(args.output)
        summary["output"] = str(args.output)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def update_airwriter(writer, result, timestamp_ms):
    """Conecta resultados de visão ao motor sem usar índice como identidade."""
    count = len(result.hand_landmarks)
    if count != 1:
        reason = "SEM MAO DETECTADA" if count == 0 else "DEIXE APENAS UMA MAO VISIVEL"
        writer.update(None, False, timestamp_ms, unavailable=reason)
        return None
    landmarks = result.hand_landmarks[0]
    points = [(p.x * (writer.width - 1), p.y * (writer.height - 1)) for p in landmarks]
    tip = points[8]
    if writer.mirrored:
        tip = (writer.width - 1 - tip[0], tip[1])
    categories = result.handedness[0] if result.handedness else []
    hand_tag = categories[0].category_name if categories else None
    writer.update(tip, writing_pose(points), timestamp_ms, hand_tag=hand_tag)
    return tip


def draw_strokes(canvas, strokes, cv2, pen_width):
    """Desenha cada traço de modo independente; nunca une o fim de dois traços."""
    color = (220, 60, 25)  # BGR: azul.
    for stroke in strokes:
        if not stroke:
            continue
        if len(stroke) == 1:
            cv2.circle(canvas, (round(stroke[0].x), round(stroke[0].y)),
                       max(1, pen_width // 2), color, -1, cv2.LINE_AA)
        for start, end in zip(stroke, stroke[1:]):
            cv2.line(canvas, (round(start.x), round(start.y)), (round(end.x), round(end.y)),
                     color, pen_width, cv2.LINE_AA)


def draw_airwriting(frame, writer, tip, args, cv2, np, fps, white_background):
    if white_background:
        canvas = np.full_like(frame, 255)
    else:
        canvas = cv2.flip(frame, 1) if args.mirror else frame.copy()
    draw_strokes(canvas, writer.strokes, cv2, args.pen_width)
    if tip and all(math.isfinite(v) for v in tip):
        point = (round(tip[0]), round(tip[1]))
        if 0 <= point[0] < writer.width and 0 <= point[1] < writer.height:
            marker_color = (40, 220, 60) if writer.writing else (0, 170, 245)
            cv2.circle(canvas, point, 9, marker_color, -1, cv2.LINE_AA)
    status = f"GestureLab | airwrite | {writer.status}"
    if fps is not None:
        status += f" | FPS loop: {fps:.1f}"
    put_text(canvas, status, (12, 28), cv2)
    put_text(canvas, f"Tracos: {len(writer.strokes)} | Indicador estendido; demais dedos recolhidos",
             (12, 56), cv2)
    put_text(canvas, "Espaco: pausa | C: limpar | Z: desfazer | B: fundo | S: salvar | Q/Esc: sair",
             (12, writer.height - 14), cv2)
    return canvas


def save_airwriting(writer, args, cv2, np):
    """Salva somente o canvas e trajetórias; nunca a imagem da câmera."""
    canvas = np.full((writer.height, writer.width, 3), 255, dtype=np.uint8)
    draw_strokes(canvas, writer.strokes, cv2, args.pen_width)
    ok, encoded = cv2.imencode(".png", canvas)
    if not ok:
        raise RuntimeError("Não foi possível codificar o desenho.")
    folder = ROOT / "outputs"
    folder.mkdir(parents=True, exist_ok=True)
    stem = f"airwrite_{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:8]}"
    png_path, json_path = folder / f"{stem}.png", folder / f"{stem}.json"
    data = writer.snapshot()
    data["pen_width_px"] = args.pen_width
    # Modo exclusivo evita substituir qualquer arquivo existente, mesmo em colisão de nome.
    with png_path.open("xb") as output:
        output.write(encoded.tobytes())
    with json_path.open("x", encoding="utf-8") as output:
        json.dump(data, output, ensure_ascii=False, indent=2)
    print(f"Desenho salvo: {png_path}\nTrajetórias salvas: {json_path}")
    return png_path, json_path


def run_camera(task, args, deps):
    cv2 = deps[0]
    np = deps[2]
    capture = cv2.VideoCapture(args.camera)
    try:
        if not capture.isOpened():
            raise RuntimeError(
                f"Webcam {args.camera} indisponível. Feche outros apps, permita a câmera "
                "no sistema e tente --camera 1."
            )
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 540)
        started = time.perf_counter()
        clock = FrameClock()
        fps = None
        frames = 0
        writer = None
        white_background = args.canvas
        while True:
            loop_start = time.perf_counter()
            ok, frame = capture.read()
            if not ok or frame is None:
                raise RuntimeError("A webcam abriu, mas não entregou um frame válido.")
            timestamp = clock.tick(time.perf_counter() - started)
            result = process_frame(task, frame, args.mode, timestamp, deps)
            if args.mode == "airwrite":
                height, width = frame.shape[:2]
                if writer is None:
                    writer = AirWriter(width, height, smooth_ms=args.smooth_ms, mirrored=args.mirror)
                elif (writer.width, writer.height) != (width, height):
                    # Não reinterpreta traços antigos em um novo referencial silenciosamente.
                    raise RuntimeError("A resolução da câmera mudou durante a escrita. Reinicie o modo.")
                tip = update_airwriter(writer, result, timestamp)
                canvas = draw_airwriting(frame, writer, tip, args, cv2, np, fps, white_background)
            else:
                canvas, _ = draw_result(frame, result, args, cv2, fps)
            frames += 1
            if not args.headless:
                cv2.imshow("GestureLab", canvas)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), ord("Q"), 27):
                    break
                if writer is not None:
                    if key == ord(" "):
                        writer.toggle_pause()
                    elif key in (ord("c"), ord("C")):
                        writer.clear()
                    elif key in (ord("z"), ord("Z")):
                        writer.undo()
                    elif key in (ord("b"), ord("B")):
                        white_background = not white_background
                    elif key in (ord("s"), ord("S")):
                        writer.lift()
                        save_airwriting(writer, args, cv2, np)
                if cv2.getWindowProperty("GestureLab", cv2.WND_PROP_VISIBLE) < 1:
                    break
            elapsed = time.perf_counter() - loop_start
            current_fps = 1.0 / max(elapsed, 1e-9)
            fps = current_fps if fps is None else 0.9 * fps + 0.1 * current_fps
            if args.max_frames and frames >= args.max_frames:
                break
        print(f"Encerrado após {frames} frames. Nenhum vídeo foi gravado.")
    finally:
        capture.release()
        if not args.headless:
            cv2.destroyAllWindows()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        dependencies = load_dependencies()
        with create_task(args, dependencies[3], dependencies[4]) as task:
            if args.image:
                run_image(task, args, dependencies)
            else:
                run_camera(task, args, dependencies)
    except KeyboardInterrupt:
        return 0
    except (RuntimeError, OSError, ValueError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
