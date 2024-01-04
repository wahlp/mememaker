from io import BytesIO

import pytest
from PIL import Image, ImageSequence

import mememaker


def test_image(image_bytes_fixture):
    buffer = mememaker.add_text_to_image(
        image_data=image_bytes_fixture, text="test", font="default", transparency=False
    )

    im1 = Image.open(BytesIO(image_bytes_fixture))
    im2 = Image.open(buffer)

    assert im2.height > im1.height
    assert im2.width == im1.width


def test_gif(gif_bytes_fixture):
    buffer = mememaker.add_text_to_gif(
        image_data=gif_bytes_fixture, text="test", font="default", transparency=False
    )

    im1 = Image.open(BytesIO(gif_bytes_fixture))
    im2 = Image.open(buffer)

    assert im2.height > im1.height
    assert im2.width == im1.width
    assert im2.n_frames == im1.n_frames


@pytest.mark.parametrize("requested_speed", [0.1, 0.25, 0.5, 1, 1.1, 1.5, 2, 4])
def test_gif_speed_change(gif_bytes_fixture, requested_speed):
    buffer = mememaker.add_text_to_gif(
        image_data=gif_bytes_fixture,
        text="test",
        font="default",
        transparency=False,
        custom_speed=requested_speed,
    )

    im1 = Image.open(BytesIO(gif_bytes_fixture))
    im2 = Image.open(buffer)

    assert im2.height > im1.height
    assert im2.width == im1.width

    im1_duration = sum(frame.info["duration"] for frame in ImageSequence.Iterator(im1))
    im2_duration = sum(frame.info["duration"] for frame in ImageSequence.Iterator(im2))

    # frame durations round to multiples of 10 when saving the output gif
    # so the output speed may not be exactly the same value as the requested speed
    actual_speed = im1_duration / im2_duration
    assert actual_speed >= requested_speed
