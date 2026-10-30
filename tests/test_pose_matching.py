"""Contratos geométricos e de catálogo sem câmera, modelo ou bibliotecas de visão."""

import json
import math
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from pose_matching import (
    BODY_JOINTS,
    PoseReference,
    extract_pose,
    load_catalog,
    mirror_pose,
    rank_matches,
)


def landmarks(*, raised_left=False, raised_right=False):
    points = [{"x": 0.5, "y": 0.3, "visibility": 1.0, "presence": 1.0} for _ in range(33)]
    positions = {
        11: (0.4, 0.3), 12: (0.6, 0.3), 13: (0.35, 0.45), 14: (0.65, 0.45),
        15: (0.3, 0.6), 16: (0.7, 0.6), 23: (0.43, 0.55), 24: (0.57, 0.55),
        25: (0.42, 0.72), 26: (0.58, 0.72), 27: (0.4, 0.9), 28: (0.6, 0.9),
    }
    if raised_left:
        positions.update({13: (0.35, 0.2), 15: (0.3, 0.05)})
    if raised_right:
        positions.update({14: (0.65, 0.2), 16: (0.7, 0.05)})
    for index, (x, y) in positions.items():
        points[index].update(x=x, y=y)
    return points


def reference(identifier, points):
    return PoseReference(identifier, identifier, Path(f"{identifier}.png"), extract_pose(points, 640, 480))


def test_scale_and_translation_do_not_change_nearest_pose():
    original = landmarks(raised_left=True)
    transformed = [{**point, "x": point["x"] * 0.6 + 0.1, "y": point["y"] * 0.6 + 0.2}
                   for point in original]
    query = extract_pose(transformed, 640, 480)
    matches = rank_matches(query, [reference("rest", landmarks()), reference("raised", original)])
    assert matches[0].reference.id == "raised"
    assert matches[0].distance == pytest.approx(0, abs=1e-12)
    assert matches[0].joint_count == 12


def test_image_dimensions_correct_normalized_coordinate_aspect_ratio():
    original = landmarks(raised_left=True)
    # Mesmo corpo em pixels, em canvas com o dobro da largura; x normalizado muda.
    wide = [{**point, "x": point["x"] / 2} for point in original]
    query = extract_pose(wide, 1280, 480)
    match = rank_matches(query, [reference("original", original)])[0]
    assert match.distance == pytest.approx(0, abs=1e-12)


def test_mirror_matches_opposite_raised_arm_and_can_be_disabled():
    query = extract_pose(landmarks(raised_left=True), 640, 480)
    ref = reference("right-up", landmarks(raised_right=True))
    match = rank_matches(query, [ref], max_distance=0.05)[0]
    assert match.mirrored
    assert match.distance == pytest.approx(0, abs=1e-12)
    assert rank_matches(query, [ref], max_distance=0.05, allow_mirror=False) == []
    twice = mirror_pose(mirror_pose(query))
    assert twice == query


def test_identical_symmetric_pose_prefers_unmirrored_display():
    ref = reference("rest", landmarks())
    assert rank_matches(ref.pose, [ref])[0].mirrored is False


def test_poor_matches_are_rejected_and_results_have_deterministic_top_k():
    query = extract_pose(landmarks(raised_left=True, raised_right=True), 640, 480)
    assert rank_matches(query, [reference("rest", landmarks())], max_distance=0.05) == []
    refs = [reference(name, landmarks(raised_left=True, raised_right=True)) for name in ("b", "a", "c")]
    assert [match.reference.id for match in rank_matches(query, refs, top_k=2)] == ["a", "b"]
    assert rank_matches(None, refs) == []


@pytest.mark.parametrize("index,field,value", [
    (11, "visibility", 0.1), (24, "presence", 0.1), (23, "x", math.nan), (12, "x", 1.1),
])
def test_missing_or_unreliable_torso_rejects_the_pose(index, field, value):
    points = landmarks()
    points[index][field] = value
    assert extract_pose(points, 640, 480) is None


def test_partial_pose_needs_eight_reliable_joints_and_shared_coverage():
    points = landmarks()
    for index in (13, 14, 15, 16):
        points[index]["visibility"] = 0.1
    query = extract_pose(points, 640, 480)
    assert query.joint_count == 8
    match = rank_matches(query, [reference("rest", landmarks())])[0]
    assert match.joint_count == 8
    other = landmarks()
    for index in (25, 26, 27, 28):
        other[index]["visibility"] = 0.1
    assert rank_matches(query, [reference("upper-only", other)]) == []
    points[25]["visibility"] = 0.1
    assert extract_pose(points, 640, 480) is None


def test_mediapipe_like_objects_are_accepted_and_degenerate_torso_is_rejected():
    objects = [SimpleNamespace(**point) for point in landmarks()]
    assert extract_pose(objects, 640, 480).joint_count == len(BODY_JOINTS)
    assert extract_pose([{"x": 0.5, "y": 0.5}] * 33, 640, 480) is None
    assert extract_pose(objects[:20], 640, 480) is None


@pytest.mark.parametrize("kwargs", [{"top_k": 0}, {"max_distance": math.nan}, {"max_distance": -1}])
def test_invalid_rank_options_are_reported(kwargs):
    with pytest.raises(ValueError):
        rank_matches(None, [], **kwargs)


def catalog_data(tmp_path):
    (tmp_path / "reference.png").write_bytes(b"image validation belongs to the renderer")
    return {"schema_version": 1, "references": [{
        "id": "rest", "title": "Em pé", "image": "reference.png", "width": 640, "height": 480,
        "landmarks": landmarks(), "source": "Ilustração do projeto", "license": "MIT",
        "credit": "GestureLab",
    }]}


def write_catalog(tmp_path, data):
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


def test_catalog_loads_portable_paths_and_preserves_attribution(tmp_path):
    refs = load_catalog(write_catalog(tmp_path, catalog_data(tmp_path)))
    assert refs[0].image_path == (tmp_path / "reference.png").resolve()
    assert refs[0].source == "Ilustração do projeto"
    assert refs[0].license == "MIT"
    assert refs[0].credit == "GestureLab"
    assert refs[0].pose.joint_count == 12


@pytest.mark.parametrize("image", ["../outside.png", "/tmp/outside.png", "C:/outside.png", "..\\outside.png"])
def test_catalog_cannot_escape_its_directory(tmp_path, image):
    data = catalog_data(tmp_path)
    data["references"][0]["image"] = image
    with pytest.raises(ValueError):
        load_catalog(write_catalog(tmp_path, data))


def test_catalog_rejects_duplicate_ids_and_missing_images(tmp_path):
    data = catalog_data(tmp_path)
    data["references"].append(dict(data["references"][0]))
    with pytest.raises(ValueError, match="únicos"):
        load_catalog(write_catalog(tmp_path, data))
    data["references"].pop()
    (tmp_path / "reference.png").unlink()
    with pytest.raises(FileNotFoundError):
        load_catalog(write_catalog(tmp_path, data))


@pytest.mark.parametrize("change", ["version", "landmarks", "torso", "dimensions"])
def test_catalog_rejects_incompatible_or_unusable_records(tmp_path, change):
    data = catalog_data(tmp_path)
    item = data["references"][0]
    if change == "version":
        data["schema_version"] = 2
    elif change == "landmarks":
        item["landmarks"] = []
    elif change == "torso":
        item["landmarks"][11]["visibility"] = 0
    else:
        item["width"] = 0
    with pytest.raises(ValueError):
        load_catalog(write_catalog(tmp_path, data))


def test_weights_are_used_without_turning_distance_into_probability():
    query = extract_pose(landmarks(), 640, 480)
    changed = list(query.points)
    changed[4] = (changed[4][0] + 1, changed[4][1])
    altered = replace(query, points=tuple(changed))
    ref = PoseReference("one-joint", "One joint", Path("unused.png"), altered)
    match = rank_matches(query, [ref], allow_mirror=False)[0]
    assert match.distance == pytest.approx(math.sqrt(1 / 12))
