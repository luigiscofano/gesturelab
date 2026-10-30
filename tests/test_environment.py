"""Contratos de diagnóstico sem dependências de visão, rede ou câmera."""

import hashlib
from importlib import metadata

import pytest

from scripts import check_environment as environment


def installed_versions(monkeypatch, versions):
    def version(name):
        if name not in versions:
            raise metadata.PackageNotFoundError(name)
        return versions[name]

    monkeypatch.setattr(environment.metadata, "version", version)


def test_missing_mismatched_and_matching_packages_are_distinguished(monkeypatch):
    installed_versions(monkeypatch, {"numpy": "2.0", "mediapipe": "1.2"})
    checks = environment.check_dependencies(
        {"numpy": "2.1", "mediapipe": "1.2", "opencv-contrib-python": "5.0"}
    )
    assert [(check.name, check.passed) for check in checks] == [
        ("numpy", False),
        ("mediapipe", True),
        ("opencv-contrib-python", False),
    ]
    assert "ausente" in checks[-1].message


def test_opencv_conflict_is_rejected_even_when_requested_version_matches(monkeypatch):
    installed_versions(
        monkeypatch, {"opencv-contrib-python": "5.0", "opencv-python-headless": "5.0"}
    )
    checks = environment.check_dependencies({"opencv-contrib-python": "5.0"})
    assert checks[0].passed
    assert not checks[1].passed
    assert "opencv-python-headless" in checks[1].message


def test_reference_python_and_architecture_are_checked_independently(monkeypatch):
    monkeypatch.setattr(environment.sys, "version_info", (3, 13, 0))
    monkeypatch.setattr(environment.sys, "maxsize", 2**31 - 1)
    assert all(not check.passed for check in environment.check_python())


def test_pinned_requirements_allow_comments_but_reject_silent_skips(tmp_path):
    path = tmp_path / "requirements.txt"
    path.write_text("# comentário\nnumpy==2.5.4 # versão\n", encoding="utf-8")
    assert environment.read_requirements(path) == {"numpy": "2.5.4"}
    path.write_text("numpy>=2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="linha 1"):
        environment.read_requirements(path)


def test_missing_and_corrupt_models_fail_without_modifying_files(monkeypatch, tmp_path):
    content = b"modelo de teste"
    expected = hashlib.sha256(content).hexdigest()
    monkeypatch.setattr(
        environment,
        "MODELS",
        {
            "hands": ("hands.task", "unused", expected),
            "gestures": ("gestures.task", "unused", expected),
        },
    )
    corrupt = tmp_path / "hands.task"
    corrupt.write_bytes(b"corrompido")
    checks = environment.check_models("all", tmp_path)
    assert [check.passed for check in checks] == [False, False]
    assert "SHA-256" in checks[0].message
    assert "ausente" in checks[1].message
    assert corrupt.read_bytes() == b"corrompido"
    assert not (tmp_path / "gestures.task").exists()


def test_model_selection_checks_only_requested_file(monkeypatch, tmp_path):
    content = b"modelo de teste"
    monkeypatch.setattr(
        environment,
        "MODELS",
        {
            "hands": ("hands.task", "unused", hashlib.sha256(content).hexdigest()),
            "gestures": ("missing.task", "unused", "unimportant"),
        },
    )
    (tmp_path / "hands.task").write_bytes(content)
    checks = environment.check_models("hands", tmp_path)
    assert len(checks) == 1
    assert checks[0].passed


def test_native_library_error_is_reported_and_other_imports_continue(monkeypatch):
    imported = []

    def import_module(name):
        imported.append(name)
        if name == "cv2":
            raise OSError("biblioteca nativa ausente")

    monkeypatch.setattr(environment.importlib, "import_module", import_module)
    checks = environment.check_imports()
    assert [check.passed for check in checks] == [True, False, True]
    assert imported[-1] == "mediapipe.tasks.python.vision"
    assert "OSError" in checks[1].message


@pytest.mark.parametrize("missing,expected_exit", [(False, 0), (True, 1)])
def test_default_cli_checks_metadata_without_importing_or_checking_models(
    monkeypatch, capsys, missing, expected_exit
):
    monkeypatch.setattr(environment, "check_python", lambda: [])
    monkeypatch.setattr(environment, "read_requirements", lambda path: {"numpy": "2.5.4"})
    installed_versions(monkeypatch, {} if missing else {"numpy": "2.5.4"})

    def unexpected(*args, **kwargs):
        raise AssertionError("verificação opcional não foi solicitada")

    monkeypatch.setattr(environment, "check_imports", unexpected)
    monkeypatch.setattr(environment, "check_models", unexpected)
    assert environment.main([]) == expected_exit
    assert "câmera" in capsys.readouterr().out


def test_cli_routes_requested_import_and_model_checks(monkeypatch, tmp_path):
    monkeypatch.setattr(environment, "check_python", lambda: [])
    monkeypatch.setattr(environment, "read_requirements", lambda path: {})
    installed_versions(monkeypatch, {})
    calls = []
    monkeypatch.setattr(environment, "check_imports", lambda: calls.append("imports") or [])
    monkeypatch.setattr(
        environment,
        "check_models",
        lambda selection, directory: calls.append((selection, directory)) or [],
    )
    assert environment.main(["--imports", "--models", "all", "--directory", str(tmp_path)]) == 0
    assert calls == ["imports", ("all", tmp_path)]
