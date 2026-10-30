"""Verifica coordenadas, nomes dos gestos e tempo usando apenas valores de exemplo."""

import math

import pytest

from core import HAND_CONNECTIONS, FrameClock, gesture_label, handedness_label, pixel_point


def test_mirror_matches_horizontal_image_flip():
    # Espelhar troca a posição horizontal; a altura de cada ponto deve permanecer igual.
    for x in (0.0, 0.13, 0.5, 0.91, 1.0):
        original_x, original_y = pixel_point(x, 0.3, 640, 480, False)
        flipped_x, flipped_y = pixel_point(x, 0.3, 640, 480, True)
        assert flipped_x == 639 - original_x
        assert flipped_y == original_y


def test_landmarks_outside_image_are_clamped():
    """Pontos estimados fora da imagem são limitados à borda ao desenhar."""
    assert pixel_point(-0.1, 1.2, 640, 480, False) == (0, 479)
    assert pixel_point(1.1, -0.1, 640, 480, True) == (0, 0)


@pytest.mark.parametrize("width,height", [(0, 480), (640, 0), (-1, 480)])
def test_invalid_image_size_is_rejected(width, height):
    # parametrize executa este mesmo teste para cada tamanho inválido da lista.
    with pytest.raises(ValueError):
        pixel_point(0.5, 0.5, width, height, False)


def test_nonfinite_coordinates_are_rejected():
    with pytest.raises(ValueError):
        pixel_point(math.nan, 0.5, 640, 480, False)


def test_low_score_and_out_of_vocabulary_gestures_are_unknown():
    """Um nome só é aceito se a classe for conhecida e a pontuação atingir o limiar."""
    assert gesture_label("Thumb_Up", 0.64, 0.65) == "DESCONHECIDO"
    assert gesture_label("None", 0.99, 0.65) == "DESCONHECIDO"
    assert gesture_label("Not_A_Class", 0.99, 0.65) == "DESCONHECIDO"
    assert gesture_label(None, 0.99, 0.65) == "DESCONHECIDO"
    assert gesture_label("Thumb_Up", math.nan, 0.65) == "DESCONHECIDO"


def test_threshold_accepts_exact_boundary():
    # O valor exato do limiar também é aceito, evitando uma diferença entre >= e >.
    assert gesture_label("Thumb_Up", 0.65, 0.65) == "JOIA"


def test_person_handedness_is_not_swapped_by_display_mirroring():
    """Esquerda e direita identificam a mão da pessoa, não o lado da tela."""
    assert handedness_label("Left") == "Esquerda"
    assert handedness_label("Right") == "Direita"


def test_timestamps_remain_strictly_increasing_with_equal_milliseconds():
    # Mesmo com arredondamento ou recuo do relógio, o modelo deve receber tempos crescentes.
    clock = FrameClock()
    values = [clock.tick(t) for t in (0.0, 0.0001, 0.0002, 0.005, 0.004)]
    assert values == [0, 1, 2, 5, 6]


def test_all_landmarks_are_part_of_the_hand_graph():
    """Os 21 pontos participam das conexões, sem arestas duplicadas."""
    assert {point for connection in HAND_CONNECTIONS for point in connection} == set(range(21))
    assert len(HAND_CONNECTIONS) == len(set(HAND_CONNECTIONS))
