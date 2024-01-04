import io
import logging
import textwrap
from enum import Enum
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageSequence

# todo:
# add unicode text support

logger = logging.getLogger(__name__)


class FontOptions(Enum):
    default = ("Futura", "caption.otf")
    comic_sans = ("Comic Sans", "Comic Sans MS Bold.ttf")


def calc_line_splitting(text, image_width, font):
    # init starting values for loop
    pixel_width = image_width
    max_char_per_line = len(text)

    draw = ImageDraw.Draw(Image.new("RGB", (image_width, 1), "white"))

    lines = textwrap.wrap(text, max_char_per_line)
    num_words = 0
    min_side_padding = 10 * 2
    while pixel_width + min_side_padding > image_width:
        # calc until we find a limit that fits the image width
        lines = textwrap.wrap(text, max_char_per_line)
        pixel_width = max(draw.textbbox((0, 0), line, font=font)[2] for line in lines)
        max_char_per_line = len(text.rsplit(" ", num_words)[0])
        num_words += 1

    return lines


def draw_text_as_image(
    image_width: int,
    text: str,
    font: ImageFont.FreeTypeFont,
    text_color: str,
):
    # https://stackoverflow.com/a/56205095

    lines = calc_line_splitting(text, image_width, font)

    # calculate starting height based on expected space required
    draw_dummy = ImageDraw.Draw(Image.new("RGB", (1, 1), "white"))
    line_heights = [draw_dummy.textbbox((0, 0), line, font=font)[3] for line in lines]
    text_height = max(line_heights) * len(line_heights)

    padding = 20
    new_img_height = text_height + padding * 2
    image = Image.new("RGB", (image_width, new_img_height), "white")
    draw = ImageDraw.Draw(image)

    y_text = padding - max(line_heights) // 16
    for line in lines:
        _, _, line_width, line_height = draw.textbbox((0, 0), line, font=font)
        draw.text(
            ((image_width - line_width) / 2, y_text), line, font=font, fill=text_color
        )
        y_text += max(line_heights)

    if y_text > new_img_height:
        logger.warning(
            f"drawn text has exceeded the height of the image. {image_width=}, {lines=}"
        )

    return image


def merge_images(img_above: Image.Image, img_below: Image.Image, transparency: bool):
    if transparency:
        mode = "RGBA"
    else:
        mode = "RGB"

    output_image = Image.new(
        mode, (img_above.width, img_above.height + img_below.height)
    )
    output_image.paste(img_above, (0, 0))
    output_image.paste(img_below, (0, img_above.height))

    return output_image


def get_file_path(relative_path: str):
    base_path = Path(__file__).parent
    abs_path = (base_path / relative_path).resolve()
    return str(abs_path)


def init_font(input_img_width: int, font: str):
    fontsize = input_img_width // 10

    font_location = get_file_path(f"./fonts/{FontOptions[font].value[1]}")
    font = ImageFont.truetype(font_location, fontsize)
    text_color = "black"

    return font, text_color


def add_text_to_image(image_data: bytes, text: str, font: str, transparency: bool):
    input_file = io.BytesIO(image_data)
    input_img = Image.open(input_file)

    font_object, text_color = init_font(input_img.width, font)
    caption_img = draw_text_as_image(input_img.width, text, font_object, text_color)
    output_image = merge_images(caption_img, input_img, transparency)

    buffer = io.BytesIO()
    img_format = "PNG" if transparency else "JPEG"
    output_image.save(buffer, format=img_format)
    buffer.seek(0)
    return buffer


def add_text_to_gif(
    image_data: bytes,
    text: str,
    font: str,
    transparency: bool,
    custom_speed: float = 1,
):
    # sort of broken with transparency
    # the frames sequentially get drawn on top of each other without clearing the old ones
    input_file = io.BytesIO(image_data)
    input_gif = Image.open(input_file)

    font_object, text_color = init_font(input_gif.width, font)
    caption_img = draw_text_as_image(input_gif.width, text, font_object, text_color)

    frames: list[Image.Image] = []
    frame_durations: list[int] = []
    for frame in ImageSequence.Iterator(input_gif):
        frame_copy = frame.copy()
        output_image = merge_images(caption_img, frame_copy, transparency)
        frames.append(output_image)
        frame_durations.append(frame_copy.info["duration"])

    durations, frame_drop_interval = calc_final_frame_durations(
        frame_durations, custom_speed
    )

    frames_to_keep = frames[::frame_drop_interval]
    durations_to_keep = durations[::frame_drop_interval]

    buffer = io.BytesIO()
    frames_to_keep[0].save(
        buffer,
        format="GIF",
        save_all=True,
        append_images=frames_to_keep[1:],
        loop=0,
        duration=durations_to_keep,
        optimize=True,
    )
    buffer.seek(0)
    return buffer


def calc_final_frame_durations(initial_durations: list[int], custom_speed: float):
    # gif frame durations have a lower bound of how short they can be
    # https://stackoverflow.com/questions/64473278/gif-frame-duration-seems-slower-than-expected
    # work around this by dropping alternate frames to look like we actually still sped up
    lowest_valid_duration = 20

    frame_drop_interval = 1
    final_durations = []
    for duration in initial_durations:
        frame_duration = duration / custom_speed
        # if lowest is 20, 15 is still acceptable, so keep interval at 1
        # any lower than that is closer to 10, interval should be at least 2
        if frame_duration < lowest_valid_duration:
            if frame_duration < lowest_valid_duration * 0.75:
                # round desired speed multiplier to nearest integer
                unachievable_speedup = int(lowest_valid_duration / frame_duration + 0.5)
                frame_drop_interval = max(frame_drop_interval, unachievable_speedup)
            final_durations.append(lowest_valid_duration)
        else:
            final_durations.append(frame_duration)

    return final_durations, frame_drop_interval
