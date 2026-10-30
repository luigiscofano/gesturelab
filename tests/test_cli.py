from types import SimpleNamespace
import sys

import pytest

import app
from app import parse_args


def test_default_mode_matches_first_milestone():
    args = parse_args([])
    assert args.mode == "hands"
    assert args.camera == 0
    assert args.num_hands == 2
    assert args.mirror is True


def test_headless_camera_requires_a_stop_condition():
    with pytest.raises(SystemExit):
        parse_args(["--headless"])


def test_cannot_accidentally_save_webcam_output():
    with pytest.raises(SystemExit):
        parse_args(["--output", "foto.png"])


def test_can_process_photo_without_mirroring():
    args = parse_args(["--image", "foto.jpg", "--no-mirror", "--mode", "gestures"])
    assert args.image.name == "foto.jpg"
    assert args.mirror is False


@pytest.mark.parametrize("value", ["-0.1", "1.1", "nan"])
def test_invalid_confidence_threshold_is_rejected(value):
    with pytest.raises(SystemExit):
        parse_args(["--threshold", value])


def test_airwrite_uses_temporal_capture_and_supports_canvas_options():
    args = parse_args(["--mode", "airwrite", "--canvas", "--smooth-ms", "0", "--pen-width", "7"])
    assert args.mode == "airwrite"
    assert args.canvas is True
    assert args.smooth_ms == 0
    assert args.pen_width == 7


def test_a_single_photo_cannot_record_an_airwriting_trajectory():
    with pytest.raises(SystemExit):
        parse_args(["--mode", "airwrite", "--image", "foto.jpg"])


def test_canvas_is_only_available_for_airwrite():
    with pytest.raises(SystemExit):
        parse_args(["--mode", "hands", "--canvas"])


@pytest.mark.parametrize("value", ["-1", "nan", "inf"])
def test_invalid_smoothing_is_rejected(value):
    with pytest.raises(SystemExit):
        parse_args(["--mode", "airwrite", "--smooth-ms", value])


def test_posematch_accepts_its_own_gallery_and_a_photo():
    args = parse_args(["--mode", "posematch", "--gallery", "catalog.json",
                       "--match-threshold", "0.6", "--image", "pose.jpg"])
    assert args.gallery.name == "catalog.json"
    assert args.match_threshold == 0.6
    assert args.image.name == "pose.jpg"


@pytest.mark.parametrize("option,value", [("--gallery", "catalog.json"),
                                          ("--match-threshold", "0.5")])
def test_posematch_options_are_rejected_in_hand_modes(option, value):
    with pytest.raises(SystemExit):
        parse_args(["--mode", "hands", option, value])


@pytest.mark.parametrize("value", ["-1", "nan", "inf"])
def test_posematch_rejects_invalid_distances(value):
    with pytest.raises(SystemExit):
        parse_args(["--mode", "posematch", "--match-threshold", value])


def test_posematch_dispatch_does_not_create_a_hand_task(monkeypatch):
    calls = []
    dependencies = (None,) * 5
    monkeypatch.setattr(app, "load_dependencies", lambda: dependencies)
    monkeypatch.setattr(app, "create_task", lambda *args: pytest.fail("tarefa de mão indevida"))
    monkeypatch.setitem(sys.modules, "pose_match_app", SimpleNamespace(
        run_posematch=lambda args, deps: calls.append((args.mode, deps))
    ))
    assert app.main(["--mode", "posematch", "--image", "pose.jpg"]) == 0
    assert calls == [("posematch", dependencies)]


def test_photo_export_does_not_overwrite_a_file_created_during_encoding(tmp_path, monkeypatch):
    image = tmp_path / "input.png"
    output = tmp_path / "output.png"
    args = parse_args(["--image", str(image), "--output", str(output)])
    frame = SimpleNamespace(shape=(2, 2, 3))
    encoded = SimpleNamespace(
        tobytes=lambda: b"new annotated image",
        tofile=lambda path: path.write_bytes(b"new annotated image"),
    )

    def encode(extension, canvas):
        # Outro processo ocupa o destino após o teste de existência inicial.
        output.write_bytes(b"another process owns this file")
        return True, encoded

    cv2 = SimpleNamespace(imdecode=lambda *args: frame, IMREAD_COLOR=1, imencode=encode)
    np = SimpleNamespace(fromfile=lambda *args, **kwargs: b"input", uint8=object())
    monkeypatch.setattr(app, "process_frame", lambda *args: None)
    monkeypatch.setattr(app, "draw_result", lambda *args: (frame, {}))

    with pytest.raises(FileExistsError):
        app.run_image(None, args, (cv2, None, np, None, None))

    assert output.read_bytes() == b"another process owns this file"
