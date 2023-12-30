from io import BytesIO

from PIL import Image

import mememaker


def test_image(image_bytes_fixture):
    buffer = mememaker.add_text_to_image(
        image_data=image_bytes_fixture, 
        text='test', 
        font='default', 
        transparency=False
    )
    
    im1 = Image.open(BytesIO(image_bytes_fixture))
    im2 = Image.open(buffer)

    assert im2.height > im1.height
    assert im2.width == im1.width


def test_gif(gif_bytes_fixture):
    buffer = mememaker.add_text_to_gif(
        image_data=gif_bytes_fixture, 
        text='test', 
        font='default', 
        transparency=False
    )
    
    im1 = Image.open(BytesIO(gif_bytes_fixture))
    im2 = Image.open(buffer)
    
    assert im2.height > im1.height
    assert im2.width == im1.width
    assert im2.n_frames == im1.n_frames