"""Testa o roteamento e o retorno ao menu sem abrir câmera nem janela."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import launcher


@pytest.fixture
def menu():
    # Os objetos de interface são substituídos para que a suíte rode sem Tcl/Tk.
    view = launcher.Launcher.__new__(launcher.Launcher)
    view.root = Mock()
    view.camera = Mock()
    view.camera.get.return_value = "1"
    view.camera_field = Mock()
    view.show_status = Mock()
    view.buttons = {mode: Mock() for mode, *_ in launcher.MODES}
    view.running = False
    return view


@pytest.mark.parametrize("mode", ["hands", "gestures", "airwrite", "posematch"])
def test_opens_mode_with_selected_camera_and_returns(menu, monkeypatch, mode):
    def run(args):
        assert menu.running
        menu.root.withdraw.assert_called_once()
        assert args.mode == mode
        assert args.camera == 1

    monkeypatch.setattr(launcher, "run_mode", run)
    menu.open_mode(mode)
    assert not menu.running
    menu.root.deiconify.assert_called_once()
    menu.buttons[mode].focus_set.assert_called_once()


def test_recovers_after_camera_failure(menu, monkeypatch):
    run = Mock(side_effect=[RuntimeError("Webcam 1 indisponível."), None])
    monkeypatch.setattr(launcher, "run_mode", run)

    menu.open_mode("hands")
    menu.show_status.assert_called_with("Webcam 1 indisponível.", error=True)
    menu.open_mode("gestures")
    assert run.call_count == 2
    assert menu.root.deiconify.call_count == 2
    assert not menu.running


@pytest.mark.parametrize("value", ["", "-1", "1.5", "outra"])
def test_invalid_camera_keeps_menu_open(menu, monkeypatch, value):
    run = Mock()
    monkeypatch.setattr(launcher, "run_mode", run)
    menu.camera.get.return_value = value

    menu.open_mode("hands")

    run.assert_not_called()
    menu.root.withdraw.assert_not_called()
    menu.camera_field.focus_set.assert_called_once()
    assert menu.show_status.call_args.kwargs["error"] is True


def test_number_in_camera_field_does_not_open_a_mode(menu):
    menu.open_mode = Mock()
    menu.open_shortcut(SimpleNamespace(widget=menu.camera_field), "hands")
    menu.open_mode.assert_not_called()
    menu.open_shortcut(SimpleNamespace(widget=menu.buttons["hands"]), "hands")
    menu.open_mode.assert_called_once_with("hands")


def test_does_not_start_second_mode_while_busy(menu, monkeypatch):
    run = Mock()
    monkeypatch.setattr(launcher, "run_mode", run)
    menu.running = True
    menu.open_mode("posematch")
    run.assert_not_called()
