import json
import math
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

import hand_app
from airwriting import AirWriter, writing_pose
from hand_app import update_airwriter


def hand_points():
    # Configuração esquemática: indicador reto e outros dedos formando uma dobra.
    points = [(120.0, 300.0)] * 21
    points[1:5] = [(90, 250), (60, 230), (40, 200), (20, 180)]
    points[5:9] = [(80, 220), (80, 160), (80, 115), (80, 70)]
    for start, x in ((9, 120), (13, 155), (17, 190)):
        points[start : start + 4] = [(x, 220), (x, 175), (x - 10, 205), (x, 225)]
    return points


def begin(writer, point=(100.0, 100.0), start=0, hand="Right"):
    writer.update(point, True, start, hand_tag=hand)
    writer.update(point, True, start + 100, hand_tag=hand)
    assert writer.writing


def test_index_pose_ignores_thumb():
    points = hand_points()
    assert writing_pose(points)
    points[1:5] = [(500, -50), (30, 90), (0, 0), (400, 400)]
    assert writing_pose(points)


@pytest.mark.parametrize("angle,scale", [(90, 0.4), (180, 2.0), (-35, 1.2)])
def test_pose_is_invariant_to_in_plane_rotation_translation_and_scale(angle, scale):
    radians = math.radians(angle)
    points = [
        (
            scale * (x * math.cos(radians) - y * math.sin(radians)) + 900,
            scale * (x * math.sin(radians) + y * math.cos(radians)) - 300,
        )
        for x, y in hand_points()
    ]
    assert writing_pose(points)


def test_peace_sign_and_closed_index_do_not_write():
    peace = hand_points()
    peace[9:13] = [(120, 220), (120, 160), (120, 115), (120, 70)]
    assert not writing_pose(peace)
    closed = hand_points()
    closed[5:9] = [(80, 220), (80, 175), (70, 205), (80, 225)]
    assert not writing_pose(closed)


def test_degenerate_or_nonfinite_landmarks_are_rejected():
    assert not writing_pose([(0, 0)] * 21)
    assert not writing_pose(hand_points()[:20])
    points = hand_points()
    points[8] = (math.nan, 3)
    assert not writing_pose(points)


def test_brief_pose_noise_does_not_create_a_dot():
    writer = AirWriter(1000, 600)
    writer.update((100, 100), True, 0)
    writer.update((105, 100), True, 50)
    writer.update((110, 100), False, 90)
    assert not writer.strokes
    assert not writer.writing


def test_reposition_after_pen_up_does_not_bridge_or_reuse_filter_history():
    writer = AirWriter(1000, 600, smooth_ms=100)
    begin(writer)
    writer.update((150, 100), True, 150, hand_tag="Right")
    writer.update((160, 100), False, 170, hand_tag="Right")
    assert not writer.writing
    begin(writer, (800, 400), start=200)
    assert len(writer.strokes) == 2
    assert writer.strokes[0][-1].x < 150
    assert writer.strokes[1][0].x == 800
    assert writer.strokes[1][0].y == 400


def test_missing_hand_immediately_ends_the_trace():
    writer = AirWriter(1000, 600)
    begin(writer)
    writer.update(None, False, 101, unavailable="SEM MAO DETECTADA")
    assert not writer.writing
    assert len(writer.completed) == 1
    assert writer.status == "SEM MAO DETECTADA"


@pytest.mark.parametrize("break_kind", ["gap", "jump", "hand_change"])
def test_discontinuities_require_new_confirmation_and_separate_stroke(break_kind):
    writer = AirWriter(1000, 600)
    begin(writer)
    point = (800, 100) if break_kind == "jump" else (110, 100)
    timestamp = 500 if break_kind == "gap" else 110
    hand = "Left" if break_kind == "hand_change" else "Right"
    writer.update(point, True, timestamp, hand_tag=hand)
    assert not writer.writing
    writer.update(point, True, timestamp + 100, hand_tag=hand)
    assert len(writer.strokes) == 2
    assert writer.strokes[1][0].x == point[0]


def test_pause_discards_candidate_and_does_not_accrue_confirmation_time():
    writer = AirWriter(1000, 600)
    begin(writer)
    writer.toggle_pause()
    writer.update((500, 500), True, 200, hand_tag="Right")
    writer.update((500, 500), True, 5000, hand_tag="Right")
    assert not writer.writing
    assert writer.status == "PAUSADO"
    writer.toggle_pause()
    writer.update((500, 500), True, 5010, hand_tag="Right")
    assert not writer.writing
    writer.update((500, 500), True, 5110, hand_tag="Right")
    assert writer.writing
    assert len(writer.strokes) == 2
    assert writer.strokes[1][0].x == 500


def test_clear_and_undo_reset_an_active_pen():
    writer = AirWriter(1000, 600)
    begin(writer)
    writer.lift()
    begin(writer, (300, 100), 200)
    writer.undo()
    assert len(writer.strokes) == 1
    assert not writer.writing
    writer.update((400, 100), True, 310, hand_tag="Right")
    assert not writer.writing
    writer.clear()
    assert writer.strokes == []
    writer.update((800, 400), True, 320, hand_tag="Right")
    writer.update((800, 400), True, 420, hand_tag="Right")
    assert writer.strokes[0][0].x == 800


def test_time_based_smoothing_is_consistent_at_different_frame_rates():
    slow = AirWriter(1000, 600, smooth_ms=50, confirm_ms=0)
    fast = AirWriter(1000, 600, smooth_ms=50, confirm_ms=0)
    slow.update((100, 100), True, 0)
    fast.update((100, 100), True, 0)
    slow.update((200, 100), True, 100)
    fast.update((200, 100), True, 50)
    fast.update((200, 100), True, 100)
    assert slow.current[-1].x == pytest.approx(fast.current[-1].x)
    assert 100 < slow.current[-1].x < 200


def test_zero_smoothing_tracks_input_without_lag():
    writer = AirWriter(1000, 600, smooth_ms=0, confirm_ms=0)
    writer.update((100, 100), True, 0)
    writer.update((200, 120), True, 50)
    assert writer.current[-1].x == 200
    assert writer.current[-1].y == 120


def test_snapshot_records_coordinate_convention_and_stroke_boundaries():
    writer = AirWriter(1000, 600, mirrored=False)
    begin(writer)
    writer.lift()
    begin(writer, (300, 300), 200)
    snapshot = writer.snapshot()
    assert snapshot["frame_size"] == {"width": 1000, "height": 600}
    assert snapshot["mirrored"] is False
    assert snapshot["point_processing"] == "ema_smoothed"
    assert snapshot["stroke_semantics"] == "pen_down_segments_not_characters"
    assert len(snapshot["strokes"]) == 2
    assert snapshot["strokes"][0]["points"][0] == {"x": 100.0, "y": 100.0, "t_ms": 100}


def test_outside_frame_or_nonfinite_tip_lifts_without_clamping_a_false_line():
    writer = AirWriter(1000, 600)
    begin(writer)
    writer.update((-1, 100), True, 110, hand_tag="Right")
    assert not writer.writing
    assert len(writer.strokes[0]) == 1
    writer.update((math.nan, 100), True, 120, hand_tag="Right")
    assert not writer.writing


def test_nonincreasing_timestamps_are_rejected():
    writer = AirWriter(1000, 600)
    writer.update(None, False, 10)
    with pytest.raises(ValueError):
        writer.update(None, False, 10)


def test_two_detected_hands_pause_writing_instead_of_picking_a_list_index():
    writer = AirWriter(1000, 600)
    begin(writer)
    two_hands = SimpleNamespace(hand_landmarks=[[], []], handedness=[])
    assert update_airwriter(writer, two_hands, 110) is None
    assert not writer.writing
    assert writer.status == "DEIXE APENAS UMA MAO VISIVEL"


def test_landmark_adapter_applies_display_mirroring_to_tip_and_export():
    result = SimpleNamespace(
        hand_landmarks=[[SimpleNamespace(x=x / 999, y=y / 599) for x, y in hand_points()]],
        handedness=[[SimpleNamespace(category_name="Right")]],
    )
    writer = AirWriter(1000, 600, mirrored=True, confirm_ms=0)
    tip = update_airwriter(writer, result, 0)
    assert tip == pytest.approx((999 - 80, 70))
    assert writer.snapshot()["strokes"][0]["points"][0]["x"] == pytest.approx(919)


@pytest.fixture
def export_environment(tmp_path, monkeypatch):
    """Codificador substituído: valida arquivos e falhas, sem instalar OpenCV."""
    monkeypatch.setattr(hand_app, "ROOT", tmp_path)
    monkeypatch.setattr(
        hand_app, "datetime", SimpleNamespace(now=lambda: datetime(2026, 1, 2, 3, 4, 5))
    )
    monkeypatch.setattr(hand_app.uuid, "uuid4", lambda: SimpleNamespace(hex="0123456789abcdef"))
    writer = AirWriter(640, 480)
    args = SimpleNamespace(pen_width=5)
    cv2 = SimpleNamespace(imencode=lambda *args: (True, SimpleNamespace(tobytes=lambda: b"png")))
    np = SimpleNamespace(full=lambda *args, **kwargs: None, uint8=object())
    return writer, args, cv2, np


def test_airwrite_export_preserves_json_metadata(export_environment):
    png_path, json_path = hand_app.save_airwriting(*export_environment)
    assert png_path.read_bytes() == b"png"
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["frame_size"] == {"width": 640, "height": 480}
    assert data["coordinate_space"] == "display_pixels"
    assert data["pen_width_px"] == 5
    assert data["strokes"] == []


def test_json_collision_preserves_existing_file_and_removes_new_png(
    export_environment,
    tmp_path,
):
    folder = tmp_path / "outputs"
    folder.mkdir()
    existing = folder / "airwrite_20260102_030405_01234567.json"
    existing.write_bytes(b"existing trajectories")

    with pytest.raises(FileExistsError):
        hand_app.save_airwriting(*export_environment)

    assert list(folder.iterdir()) == [existing]
    assert existing.read_bytes() == b"existing trajectories"


def test_failed_json_write_removes_both_partial_export_files(
    export_environment,
    tmp_path,
    monkeypatch,
):
    original_open = Path.open

    @contextmanager
    def fail_json_write(path, mode="r", *args, **kwargs):
        with original_open(path, mode, *args, **kwargs) as output:
            if path.suffix == ".json" and mode.startswith("x"):

                def write(data):
                    output.write(data[:5])
                    raise OSError("simulated disk full")

                yield SimpleNamespace(write=write)
            else:
                yield output

    monkeypatch.setattr(Path, "open", fail_json_write)
    with pytest.raises(OSError, match="simulated disk full"):
        hand_app.save_airwriting(*export_environment)

    assert list((tmp_path / "outputs").iterdir()) == []
