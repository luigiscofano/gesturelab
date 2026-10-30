"""Contratos compartilhados de inferência e liberação da câmera."""

from types import SimpleNamespace

import pytest

import hand_app
from vision_runtime import VisionDependencies, camera_session


@pytest.mark.parametrize(
    "mode,timestamp,expected_method",
    [
        ("hands", None, "detect"),
        ("hands", 42, "detect_for_video"),
        ("airwrite", None, "detect"),
        ("airwrite", 42, "detect_for_video"),
        ("gestures", None, "recognize"),
        ("gestures", 42, "recognize_for_video"),
    ],
)
def test_hand_modes_use_their_image_or_video_task(mode, timestamp, expected_method, monkeypatch):
    image = object()
    result = object()
    calls = []

    def record(method, *args):
        calls.append((method, args))
        return result

    task = SimpleNamespace(
        detect=lambda *args: record("detect", *args),
        detect_for_video=lambda *args: record("detect_for_video", *args),
        recognize=lambda *args: record("recognize", *args),
        recognize_for_video=lambda *args: record("recognize_for_video", *args),
    )
    monkeypatch.setattr(hand_app, "to_mediapipe_image", lambda *args: image)
    dependencies = VisionDependencies(
        cv2=None,
        mediapipe=None,
        numpy=None,
        tasks=None,
        vision=None,
    )

    assert hand_app.process_frame(task, object(), mode, timestamp, dependencies) is result
    expected_args = (image,) if timestamp is None else (image, timestamp)
    assert calls == [(expected_method, expected_args)]


@pytest.mark.parametrize("headless", [False, True])
def test_camera_is_released_when_processing_fails(headless):
    released = []
    closed_windows = []
    capture = SimpleNamespace(
        isOpened=lambda: True,
        set=lambda *args: None,
        release=lambda: released.append(True),
    )
    cv2 = SimpleNamespace(
        VideoCapture=lambda index: capture,
        CAP_PROP_FRAME_WIDTH=1,
        CAP_PROP_FRAME_HEIGHT=2,
        destroyAllWindows=lambda: closed_windows.append(True),
    )

    with (
        pytest.raises(RuntimeError, match="inference failed"),
        camera_session(cv2, 0, headless=headless) as opened_capture,
    ):
        assert opened_capture is capture
        raise RuntimeError("inference failed")

    assert released == [True]
    assert closed_windows == ([] if headless else [True])
