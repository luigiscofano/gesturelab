"""Execução de mãos, gestos e escrita no ar com câmera ou fotografia."""

from __future__ import annotations

import json
import math
import time
import uuid
from datetime import datetime
from pathlib import Path

from airwriting import AirWriter, writing_pose
from core import HAND_CONNECTIONS, FrameClock, gesture_label, handedness_label, pixel_point
from file_io import write_new_files
from vision_runtime import (
    MODEL_NAMES,
    QUIT_KEYS,
    VisionDependencies,
    camera_session,
    read_camera_frame,
    read_image,
    to_mediapipe_image,
    write_image,
)

ROOT = Path(__file__).resolve().parent
WINDOW = "GestureLab"
# Cores no OpenCV seguem a ordem azul, verde e vermelho (BGR).
INK_COLOR = (220, 60, 25)


def create_task(args, python, vision):
    """Configura o modelo de pontos da mão ou de gestos para foto ou sequência."""
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


def process_frame(task, frame, mode, timestamp_ms, dependencies: VisionDependencies):
    """Envia um quadro ao modelo; timestamps permitem acompanhar uma sequência."""
    image = to_mediapipe_image(frame, dependencies)
    if timestamp_ms is None:
        return task.detect(image) if mode in {"hands", "airwrite"} else task.recognize(image)
    if mode in {"hands", "airwrite"}:
        return task.detect_for_video(image, timestamp_ms)
    return task.recognize_for_video(image, timestamp_ms)


def result_summary(result, args) -> dict:
    """Organiza pontos, lateralidade e gestos em dados que podem ser exportados como JSON."""
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
            # Escolhe a categoria mais pontuada; gesture_label ainda aplica a rejeição.
            category = max(candidates, key=lambda item: item.score) if candidates else None
            score = category.score if category else 0.0
            name = category.category_name if category else None
            hand.update(
                {
                    "gesture_raw": name,
                    "gesture_score": score,
                    "label": gesture_label(name, score, args.threshold),
                }
            )
        hands.append(hand)
    return {"mode": args.mode, "hand_count": len(hands), "hands": hands}


def draw_result(frame, result, args, cv2, fps: float | None = None):
    """Desenha as conexões da mão e os rótulos sobre uma cópia da captura."""
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
                cv2.putText(
                    canvas,
                    str(landmark_id),
                    (point[0] + 4, point[1] - 4),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.35,
                    (20, 230, 230),
                    1,
                    cv2.LINE_AA,
                )
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
    """Escreve um rótulo com fundo para manter o contraste sobre a imagem."""
    # Fundo escuro e escala adaptativa mantêm rótulos legíveis em fotos pequenas.
    font = cv2.FONT_HERSHEY_SIMPLEX
    base_width = cv2.getTextSize(text, font, 1.0, 1)[0][0]
    scale = min(0.55, max(0.1, (canvas.shape[1] - point[0] - 10) / max(base_width, 1)))
    (text_width, text_height), baseline = cv2.getTextSize(text, font, scale, 1)
    cv2.rectangle(
        canvas,
        (point[0] - 4, point[1] - text_height - 5),
        (point[0] + text_width + 4, point[1] + baseline + 3),
        (20, 25, 20),
        -1,
    )
    cv2.putText(canvas, text, point, font, scale, (245, 245, 245), 1, cv2.LINE_AA)


def run_image(task, args, dependencies: VisionDependencies):
    """Processa uma foto, imprime seus dados e salva a versão anotada quando solicitado."""
    cv2, np = dependencies.cv2, dependencies.numpy
    frame = read_image(args.image, cv2, np, invalid_message="Formato de imagem não suportado")
    started = time.perf_counter()
    result = process_frame(task, frame, args.mode, None, dependencies)
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
        write_image(
            args.output,
            canvas,
            cv2,
            encode_error="Não foi possível codificar a imagem anotada.",
        )
        summary["output"] = str(args.output)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def update_airwriter(writer, result, timestamp_ms):
    """Conecta resultados de visão ao motor sem usar índice como identidade."""
    # A escrita usa uma mão por vez para não misturar posições de pessoas ou mãos diferentes.
    count = len(result.hand_landmarks)
    if count != 1:
        reason = "SEM MAO DETECTADA" if count == 0 else "DEIXE APENAS UMA MAO VISIVEL"
        writer.update(None, False, timestamp_ms, unavailable=reason)
        return None
    landmarks = result.hand_landmarks[0]
    points = [(p.x * (writer.width - 1), p.y * (writer.height - 1)) for p in landmarks]
    # O ponto 8 é a ponta do indicador, usada como posição da caneta.
    tip = points[8]
    if writer.mirrored:
        tip = (writer.width - 1 - tip[0], tip[1])
    categories = result.handedness[0] if result.handedness else []
    hand_tag = categories[0].category_name if categories else None
    writer.update(tip, writing_pose(points), timestamp_ms, hand_tag=hand_tag)
    return tip


def draw_strokes(canvas, strokes, cv2, pen_width):
    """Desenha cada traço de modo independente; nunca une o fim de dois traços."""
    for stroke in strokes:
        if not stroke:
            continue
        if len(stroke) == 1:
            cv2.circle(
                canvas,
                (round(stroke[0].x), round(stroke[0].y)),
                max(1, pen_width // 2),
                INK_COLOR,
                -1,
                cv2.LINE_AA,
            )
        for start, end in zip(stroke, stroke[1:], strict=False):
            cv2.line(
                canvas,
                (round(start.x), round(start.y)),
                (round(end.x), round(end.y)),
                INK_COLOR,
                pen_width,
                cv2.LINE_AA,
            )


def draw_airwriting(frame, writer, tip, args, cv2, np, fps, white_background):
    """Combina os traços, o cursor e as instruções sobre vídeo ou fundo branco."""
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
    put_text(
        canvas,
        f"Tracos: {len(writer.strokes)} | Indicador estendido; demais dedos recolhidos",
        (12, 56),
        cv2,
    )
    put_text(
        canvas,
        "Espaco: pausa | C: limpar | Z: desfazer | B: fundo | S: salvar | Q/Esc: sair",
        (12, writer.height - 14),
        cv2,
    )
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
    # Data e identificador diferenciam as exportações feitas na mesma sessão.
    stem = f"airwrite_{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:8]}"
    png_path, json_path = folder / f"{stem}.png", folder / f"{stem}.json"
    data = writer.snapshot()
    data["pen_width_px"] = args.pen_width
    # Serializa antes de criar arquivos e evita deixar um par parcial em falhas comuns.
    json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    write_new_files({png_path: encoded.tobytes(), json_path: json_bytes})
    print(f"Desenho salvo: {png_path}\nTrajetórias salvas: {json_path}")
    return png_path, json_path


def handle_airwriting_key(key, writer, args, dependencies, white_background):
    """Aplica o atalho pressionado e devolve a preferência atual de fundo."""
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
        save_airwriting(writer, args, dependencies.cv2, dependencies.numpy)
    return white_background


def prepare_airwriter(writer, frame, args):
    """Cria a caneta no primeiro quadro e confere se a resolução continua compatível."""
    height, width = frame.shape[:2]
    if writer is None:
        return AirWriter(width, height, smooth_ms=args.smooth_ms, mirrored=args.mirror)
    if (writer.width, writer.height) != (width, height):
        # Traços existentes pertencem à resolução em que foram capturados.
        raise RuntimeError("A resolução da câmera mudou durante a escrita. Reinicie o modo.")
    return writer


def run_camera(task, args, dependencies: VisionDependencies):
    """Repete captura, inferência e desenho até um comando de saída ou limite de quadros."""
    cv2, np = dependencies.cv2, dependencies.numpy
    with camera_session(cv2, args.camera, headless=args.headless) as capture:
        started = time.perf_counter()
        clock = FrameClock()
        fps = None
        frames = 0
        writer = None
        white_background = args.canvas
        while True:
            loop_start = time.perf_counter()
            frame = read_camera_frame(capture)
            # O relógio produz tempos crescentes, exigidos pelo modo VIDEO do MediaPipe.
            timestamp = clock.tick(time.perf_counter() - started)
            result = process_frame(task, frame, args.mode, timestamp, dependencies)
            if args.mode == "airwrite":
                writer = prepare_airwriter(writer, frame, args)
                tip = update_airwriter(writer, result, timestamp)
                canvas = draw_airwriting(frame, writer, tip, args, cv2, np, fps, white_background)
            else:
                canvas, _ = draw_result(frame, result, args, cv2, fps)
            frames += 1
            if not args.headless:
                # A janela e os atalhos só existem na execução com interface.
                cv2.imshow(WINDOW, canvas)
                key = cv2.waitKey(1) & 0xFF
                if key in QUIT_KEYS:
                    break
                if writer is not None:
                    white_background = handle_airwriting_key(
                        key,
                        writer,
                        args,
                        dependencies,
                        white_background,
                    )
                if cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1:
                    break
            elapsed = time.perf_counter() - loop_start
            current_fps = 1.0 / max(elapsed, 1e-9)
            # Suaviza o indicador de FPS para reduzir a oscilação entre quadros.
            fps = current_fps if fps is None else 0.9 * fps + 0.1 * current_fps
            if args.max_frames and frames >= args.max_frames:
                break
        print(f"Encerrado após {frames} frames. Nenhum vídeo foi gravado.")


def run_hand_mode(args, dependencies: VisionDependencies) -> None:
    """Abre a tarefa de visão e escolhe entre uma foto e a captura contínua."""
    with create_task(args, dependencies.tasks, dependencies.vision) as task:
        if args.image:
            run_image(task, args, dependencies)
        else:
            run_camera(task, args, dependencies)
