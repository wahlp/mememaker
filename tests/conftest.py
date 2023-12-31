import pytest


@pytest.fixture
def image_bytes_fixture():
    file_path = "tests/demoman.jpg"
    with open(file_path, "rb") as image_file:
        image_bytes = image_file.read()
        return image_bytes


@pytest.fixture
def gif_bytes_fixture():
    file_path = "tests/steven.gif"
    with open(file_path, "rb") as image_file:
        image_bytes = image_file.read()
        return image_bytes
