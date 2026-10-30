"""Contratos de consulta, confirmação e ciclo de câmera do modo posematch."""

from types import SimpleNamespace

import pytest

import pose_match_app as runtime


def match(identifier="pose-a", *, distance=0.15, mirrored=False):
    reference = SimpleNamespace(
        id=identifier, title="Pose de exemplo", image_path="example.png",
        source="catálogo de teste", license="teste",
    )
    return SimpleNamespace(reference=reference, distance=distance, mirrored=mirrored, joint_count=12)


@pytest.mark.parametrize("count", [0, 2])
def test_absent_or_multiple_people_do_not_reuse_a_match(count, monkeypatch):
    def unexpected(*args, **kwargs):
        raise AssertionError("Não deve escolher uma pessoa pela posição na lista.")
    monkeypatch.setattr(runtime, "extract_pose", unexpected)
    result = SimpleNamespace(pose_landmarks=[object()] * count)
    search = runtime.search_result(result, 640, 480, [], 0.8)
    assert search.pose_count == count
    assert search.candidates == ()
    assert runtime.match_summary(search, None, True)["match"] is None


def test_low_visibility_does_not_run_retrieval(monkeypatch):
    monkeypatch.setattr(runtime, "extract_pose", lambda *args: None)
    monkeypatch.setattr(runtime, "rank_matches", lambda *args, **kwargs: pytest.fail("busca indevida"))
    search = runtime.search_result(SimpleNamespace(pose_landmarks=[[1]]), 640, 480, [], 0.8)
    assert search.pose_count == 1
    assert "MOSTRE O CORPO" in search.status
    assert not search.candidates


def test_search_passes_original_aspect_and_exact_zero_threshold(monkeypatch):
    calls = []
    query, landmarks, references = object(), [object()], [object()]
    candidate = match()
    monkeypatch.setattr(runtime, "extract_pose",
                        lambda points, width, height: calls.append((points, width, height)) or query)

    def rank(actual_query, actual_refs, **kwargs):
        assert actual_query is query
        assert actual_refs is references
        assert kwargs == {"top_k": 3, "max_distance": 0}
        return [candidate]

    monkeypatch.setattr(runtime, "rank_matches", rank)
    search = runtime.search_result(SimpleNamespace(pose_landmarks=[landmarks]),
                                   1280, 720, references, 0)
    assert calls == [(landmarks, 1280, 720)]
    assert search.candidates == (candidate,)


def test_a_pose_without_close_reference_has_no_displayed_image(monkeypatch):
    monkeypatch.setattr(runtime, "extract_pose", lambda *args: object())
    monkeypatch.setattr(runtime, "rank_matches", lambda *args, **kwargs: [])
    search = runtime.search_result(SimpleNamespace(pose_landmarks=[[1]]), 640, 480, [], 0.8)
    assert search.status == "SEM IMAGEM SUFICIENTEMENTE PARECIDA"
    assert runtime.match_summary(search, None, False)["match"] is None


def test_confirmation_uses_current_distance_and_resets_on_person_loss():
    confirmation = runtime.MatchConfirmation(confirm_ms=180)
    assert confirmation.update(match(), 0) is None
    assert confirmation.update(match(), 100) is None
    current = match(distance=0.3)
    assert confirmation.update(current, 180) is current
    assert confirmation.update(None, 181) is None
    assert confirmation.update(match(), 300) is None
    assert confirmation.update(match(), 480) is not None


@pytest.mark.parametrize("candidate", [match("other"), match(mirrored=True)])
def test_changed_reference_or_orientation_clears_previous_image(candidate):
    confirmation = runtime.MatchConfirmation()
    confirmation.update(match(), 0)
    assert confirmation.update(match(), 180) is not None
    assert confirmation.update(candidate, 190) is None
    assert confirmation.update(candidate, 370) is candidate


def test_tracking_gap_requires_new_confirmation():
    confirmation = runtime.MatchConfirmation()
    confirmation.update(match(), 0)
    assert confirmation.update(match(), 180) is not None
    assert confirmation.update(match(), 1000) is None
    with pytest.raises(ValueError, match="crescentes"):
        confirmation.update(match(), 1000)


@pytest.mark.parametrize("camera_mirror,match_mirror,display_flip", [
    (False, False, False), (False, True, True), (True, False, True), (True, True, False),
])
def test_reference_orientation_tracks_display_and_match_mirroring(
    camera_mirror, match_mirror, display_flip,
):
    candidate = match(mirrored=match_mirror)
    search = runtime.PoseSearch(1, "IMAGEM ENCONTRADA", (candidate,))
    summary = runtime.match_summary(search, candidate, camera_mirror)
    assert summary["match"]["reference_display_flipped"] is display_flip
    assert summary["match"]["distance"] == 0.15
    assert "not_probability" in summary["distance_semantics"]
    assert "probability" not in summary["match"]


@pytest.mark.parametrize("image,mode", [(None, "VIDEO"), ("photo.png", "IMAGE")])
def test_body_task_detects_two_people_and_uses_correct_mode(tmp_path, image, mode):
    model = tmp_path / "pose.task"
    model.write_bytes(b"fake model; creation is substituted")
    options = []
    task = object()
    python = SimpleNamespace(BaseOptions=lambda **kwargs: kwargs)
    vision = SimpleNamespace(
        RunningMode=SimpleNamespace(IMAGE="IMAGE", VIDEO="VIDEO"),
        PoseLandmarkerOptions=lambda **kwargs: options.append(kwargs) or kwargs,
        PoseLandmarker=SimpleNamespace(create_from_options=lambda value: task),
    )
    assert runtime.create_pose_task(SimpleNamespace(model=model, image=image), python, vision) is task
    assert options[0]["running_mode"] == mode
    assert options[0]["num_poses"] == 2
    assert options[0]["output_segmentation_masks"] is False


def test_video_inference_receives_original_frame_and_timestamp():
    frame, rgb = object(), object()
    seen = []

    def convert(actual_frame, conversion):
        assert actual_frame is frame
        assert conversion == "BGR2RGB"
        return rgb

    deps = (
        SimpleNamespace(cvtColor=convert, COLOR_BGR2RGB="BGR2RGB"),
        SimpleNamespace(ImageFormat=SimpleNamespace(SRGB="RGB"), Image=lambda **kwargs: kwargs),
        SimpleNamespace(ascontiguousarray=lambda data: data), None, None,
    )
    task = SimpleNamespace(detect_for_video=lambda image, timestamp: seen.append((image, timestamp)))
    runtime.process_pose_frame(task, frame, 42, deps)
    assert seen == [({"image_format": "RGB", "data": rgb}, 42)]


class FakeCapture:
    def __init__(self, *, opened=True, read_ok=True):
        self.opened, self.read_ok = opened, read_ok
        self.released = False
        self.reads = 0

    def isOpened(self):
        return self.opened

    def set(self, *args):
        pass

    def read(self):
        self.reads += 1
        return self.read_ok, SimpleNamespace(shape=(480, 640, 3)) if self.read_ok else None

    def release(self):
        self.released = True


def camera_deps(capture):
    return (
        SimpleNamespace(VideoCapture=lambda index: capture,
                        CAP_PROP_FRAME_WIDTH=1, CAP_PROP_FRAME_HEIGHT=2),
        None, None, None, None,
    )


def test_headless_capture_stops_and_releases_without_gui_or_saving(monkeypatch, capsys):
    capture = FakeCapture()
    timestamps = []

    def process(task, frame, timestamp, deps):
        timestamps.append(timestamp)
        return SimpleNamespace(pose_landmarks=[])

    monkeypatch.setattr(runtime, "process_pose_frame", process)
    args = SimpleNamespace(camera=0, headless=True, max_frames=2, mirror=True, match_threshold=0.8)
    summary = runtime.run_pose_camera(None, args, camera_deps(capture), [])
    assert capture.reads == 2
    assert capture.released
    assert summary["processed_frames"] == 2
    assert summary["webcam_saved"] is False
    assert summary["match"] is None
    assert timestamps[1] > timestamps[0]
    assert '"mode": "posematch"' in capsys.readouterr().out


@pytest.mark.parametrize("opened,read_ok", [(False, True), (True, False)])
def test_camera_resource_is_released_after_open_or_capture_failure(opened, read_ok):
    capture = FakeCapture(opened=opened, read_ok=read_ok)
    args = SimpleNamespace(camera=0, headless=True, max_frames=2, mirror=True, match_threshold=0.8)
    with pytest.raises(RuntimeError):
        runtime.run_pose_camera(None, args, camera_deps(capture), [])
    assert capture.released


def test_photo_cannot_overwrite_the_input_even_before_processing(tmp_path):
    path = tmp_path / "photo.png"
    args = SimpleNamespace(image=path, output=path)
    with pytest.raises(ValueError, match="imagem original"):
        runtime.run_pose_image(None, args, (None,) * 5, [])


def test_pose_comparison_export_preserves_existing_output(tmp_path, monkeypatch):
    output = tmp_path / "comparison.png"
    output.write_bytes(b"existing output")
    args = SimpleNamespace(image=tmp_path / "photo.png", output=output,
                           mirror=True, match_threshold=0.8)
    monkeypatch.setattr(runtime, "read_image", lambda *args: SimpleNamespace(shape=(2, 2, 3)))
    monkeypatch.setattr(runtime, "process_pose_frame",
                        lambda *args: SimpleNamespace(pose_landmarks=[]))
    monkeypatch.setattr(runtime, "draw_pose_match", lambda *args: (object(), {}))
    cv2 = SimpleNamespace(imencode=lambda *args: (True, SimpleNamespace(tobytes=lambda: b"new")))
    with pytest.raises(FileExistsError):
        runtime.run_pose_image(None, args, (cv2, None, None, None, None), [])
    assert output.read_bytes() == b"existing output"
