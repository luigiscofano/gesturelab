"""Testa a criação do catálogo e o tratamento de imagens sem baixar modelos ou usar câmera."""

import json
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest

from pose_gallery.generate_catalog import BASE, normalized_landmarks
from pose_matching import load_catalog, rank_matches
from scripts import build_pose_catalog as builder
from scripts.build_pose_catalog import parse_args, read_frame, reference_from_result, write_catalog
from vision_runtime import VisionDependencies


def result_with_people(count):
    """Imita a saída do detector com uma quantidade controlada de pessoas."""
    points = [SimpleNamespace(**point) for point in normalized_landmarks(BASE)]
    return SimpleNamespace(pose_landmarks=[points for _ in range(count)])


def reference(result=None):
    """Cria os metadados de uma referência usando a geometria conhecida das ilustrações."""
    return reference_from_result(
        result or result_with_people(1),
        name="pose-001",
        width=480,
        height=640,
        source="Foto do próprio autor",
        license_name="Uso pessoal",
    )


@pytest.mark.parametrize("people", [0, 2])
def test_indexer_does_not_select_an_arbitrary_person(people):
    # Tanto a ausência quanto a presença de duas pessoas impedem a indexação da imagem.
    assert reference(result_with_people(people)) is None


def test_indexer_skips_people_without_reliable_torso():
    result = result_with_people(1)
    result.pose_landmarks[0][11].visibility = 0.1
    assert reference(result) is None


def test_new_catalog_is_portable_and_preserves_provenance(tmp_path):
    """A galeria gerada usa caminhos relativos e mantém origem e condição de uso das fotos."""
    output = tmp_path / "minhas-poses"
    path = write_catalog(output, [reference()], {"pose-001.png": b"test placeholder"})
    refs = load_catalog(path)
    assert len(refs) == 1
    assert refs[0].image_path == output / "images" / "pose-001.png"
    assert refs[0].source == "Foto do próprio autor"
    assert refs[0].license == "Uso pessoal"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["landmark_origin"] == "mediapipe_pose_landmarker"
    assert data["references"][0]["image"] == "images/pose-001.png"


def test_output_directory_must_be_new_and_existing_data_is_untouched(tmp_path):
    # O arquivo marcador permite verificar que a recusa não apaga o conteúdo anterior.
    marker = tmp_path / "previous.txt"
    marker.write_text("keep me", encoding="utf-8")
    with pytest.raises(FileExistsError):
        write_catalog(tmp_path, [reference()], {"pose-001.png": b"test"})
    assert list(tmp_path.iterdir()) == [marker]
    assert marker.read_text(encoding="utf-8") == "keep me"


def test_no_accepted_pose_does_not_create_an_empty_catalog(tmp_path):
    output = tmp_path / "empty"
    with pytest.raises(ValueError, match="Nenhuma imagem"):
        write_catalog(output, [], {})
    assert not output.exists()


def test_catalog_write_failure_cleans_only_its_new_output(tmp_path, monkeypatch):
    """Simula uma gravação parcial e verifica que arquivos alheios à tentativa permanecem intactos."""
    output = tmp_path / "new"
    marker = tmp_path / "keep.txt"
    marker.write_bytes(b"keep")
    original_open = Path.open

    @contextmanager
    def fail_json_write(path, mode="r", *args, **kwargs):
        with original_open(path, mode, *args, **kwargs) as stream:
            if path.suffix == ".json" and mode == "xb":

                def write(data):
                    # A falha acontece depois de criar o arquivo, exercitando a limpeza da saída.
                    stream.write(data[:5])
                    raise OSError("simulated disk full")

                yield SimpleNamespace(write=write)
            else:
                yield stream

    monkeypatch.setattr(Path, "open", fail_json_write)
    with pytest.raises(OSError, match="simulated disk full"):
        write_catalog(output, [reference()], {"pose-001.png": b"test"})
    assert not output.exists()
    assert marker.read_bytes() == b"keep"


def test_bundled_illustrations_have_distinct_poses_and_valid_paths():
    # Cada pose do catálogo deve recuperar sua própria imagem como primeira referência.
    path = Path(__file__).resolve().parents[1] / "pose_gallery" / "catalog.json"
    references = load_catalog(path)
    assert len(references) == 12
    for expected in references:
        matches = rank_matches(expected.pose, references, top_k=1, max_distance=0.01)
        assert matches[0].reference.id == expected.id
        assert matches[0].distance == pytest.approx(0)
        assert expected.license == "MIT"
        assert "Ilustração" in expected.source


def test_indexer_defaults_do_not_claim_ownership_of_user_images(tmp_path):
    """Os valores padrão não presumem autoria ou licença para as fotos fornecidas."""
    args = parse_args(["--input", str(tmp_path), "--output", str(tmp_path / "out")])
    assert args.source == "Imagem fornecida pelo usuário"
    assert "verificar antes de redistribuir" in args.license


@pytest.mark.parametrize("width,height", [(1, 2000), (2000, 1)])
def test_thin_images_keep_a_nonzero_side_when_resized(width, height):
    # Fotografias muito estreitas podem arredondar para zero se o resize não limitar o mínimo.
    frame = SimpleNamespace(shape=(height, width, 3))

    def resize(frame, size, interpolation):
        assert min(size) >= 1
        assert max(size) == 960
        return SimpleNamespace(shape=(size[1], size[0], 3))

    cv2 = SimpleNamespace(imdecode=lambda *args: frame, IMREAD_COLOR=1, resize=resize, INTER_AREA=1)
    np = SimpleNamespace(fromfile=lambda *args, **kwargs: b"image", uint8=object())
    resized = read_frame(Path("thin.png"), cv2, np)
    assert sorted(resized.shape[:2]) == [1, 960]


def test_opencv_error_skips_one_image_and_continues_the_catalog(tmp_path, monkeypatch, capsys):
    """Uma imagem ilegível deve ser ignorada sem impedir a indexação da próxima."""

    class CvError(Exception):
        """Substitui a exceção de decodificação do OpenCV sem importar a biblioteca."""

        pass

    source = tmp_path / "input"
    source.mkdir()
    (source / "bad.png").write_bytes(b"bad")
    (source / "good.png").write_bytes(b"good")
    model = tmp_path / "model.task"
    model.write_bytes(b"test")
    args = parse_args(
        ["--input", str(source), "--output", str(tmp_path / "output"), "--model", str(model)]
    )

    def decode(path, flags):
        if path.name == "bad.png":
            raise CvError("invalid image")
        return SimpleNamespace(shape=(640, 480, 3))

    cv2 = SimpleNamespace(
        error=CvError,
        imdecode=decode,
        IMREAD_COLOR=1,
        COLOR_BGR2RGB=1,
        cvtColor=lambda frame, code: frame,
        imencode=lambda *args: (True, SimpleNamespace(tobytes=lambda: b"png")),
    )
    np = SimpleNamespace(
        fromfile=lambda path, **kwargs: path, uint8=object(), ascontiguousarray=lambda data: data
    )
    mp = SimpleNamespace(Image=lambda **kwargs: kwargs, ImageFormat=SimpleNamespace(SRGB=1))
    python = SimpleNamespace(BaseOptions=lambda **kwargs: kwargs)

    @contextmanager
    def create_task(options):
        # O contexto simula a abertura e o fechamento do detector, sem carregar pesos.
        yield SimpleNamespace(detect=lambda image: result_with_people(1))

    vision = SimpleNamespace(
        RunningMode=SimpleNamespace(IMAGE=1),
        PoseLandmarkerOptions=lambda **kwargs: kwargs,
        PoseLandmarker=SimpleNamespace(create_from_options=create_task),
    )
    # As dependências falsas isolam o tratamento de erro; capsys captura o aviso impresso.
    dependencies = VisionDependencies(cv2, mp, np, python, vision)
    monkeypatch.setattr(builder, "load_dependencies", lambda: dependencies)
    path = builder.build_catalog(args)
    references = load_catalog(path)
    assert [item.title for item in references] == ["good"]
    assert "Ignorada bad.png: invalid image" in capsys.readouterr().out
