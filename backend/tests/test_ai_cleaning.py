from io import BytesIO
import pytest
from PIL import Image
from app.image_cleaner import clean_ai_exif_metadata

def make_test_image(image_format: str) -> bytes:
    image = Image.new("RGB", (32, 32), "white")
    exif = Image.Exif()
    exif[305] = "Stable Diffusion"
    exif[315] = "Test Photographer"
    output = BytesIO()
    image.save(output, format=image_format, exif=exif.tobytes())
    return output.getvalue()

@pytest.mark.parametrize("image_format", ["JPEG", "PNG", "WEBP"])
def test_ai_marker_removed_and_other_exif_retained(image_format):
    cleaned = clean_ai_exif_metadata(make_test_image(image_format), image_format)
    with Image.open(BytesIO(cleaned)) as image:
        assert image.format == image_format
        assert image.size == (32, 32)
        exif = image.getexif()
        assert 305 not in exif
        assert exif.get(315) == "Test Photographer"

def test_image_without_ai_marker_still_cleans_successfully():
    output = BytesIO()
    Image.new("RGB", (16, 16), "white").save(output, format="PNG")
    cleaned = clean_ai_exif_metadata(output.getvalue(), "PNG")
    with Image.open(BytesIO(cleaned)) as image:
        assert image.format == "PNG"
        assert image.size == (16, 16)
