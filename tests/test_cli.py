import pytest

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
