from io import BytesIO
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

client = TestClient(app)


def create_sample_image(format_name: str, add_ai_marker: bool = True) -> tuple[bytes, str]:
    img = Image.new("RGB", (64, 64), color="lightblue")
    output = BytesIO()
    if add_ai_marker:
        exif = Image.Exif()
        exif[305] = "Midjourney v6.0"
        exif[315] = "Original Photographer"
        img.save(output, format=format_name, exif=exif.tobytes())
    else:
        img.save(output, format=format_name)
    ext = "jpg" if format_name.upper() == "JPEG" else format_name.lower()
    return output.getvalue(), f"sample.{ext}"


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_check_metadata_endpoint():
    img_bytes, filename = create_sample_image("JPEG", add_ai_marker=True)
    files = {"file": (filename, img_bytes, "image/jpeg")}
    response = client.post("/api/metadata/check", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == filename
    assert data["format"] == "JPEG"
    assert data["ai_marker_count"] >= 1
    marker_names = [m["name"] for m in data["ai_markers"]]
    assert any("Midjourney" in name for name in marker_names)


def test_clean_metadata_ai_only():
    img_bytes, filename = create_sample_image("JPEG", add_ai_marker=True)
    files = {"file": (filename, img_bytes, "image/jpeg")}
    data = {"mode": "ai_only"}
    response = client.post("/api/metadata/clean", files=files, data=data)
    assert response.status_code == 200
    assert "attachment" in response.headers.get("content-disposition", "")
    assert "-ai-cleaned" in response.headers.get("content-disposition", "")

    # Verify cleaned image
    cleaned_bytes = response.content
    with Image.open(BytesIO(cleaned_bytes)) as cleaned:
        exif = cleaned.getexif()
        assert 305 not in exif  # Midjourney removed
        assert exif.get(315) == "Original Photographer"  # Photographer retained


def test_clean_metadata_all():
    img_bytes, filename = create_sample_image("PNG", add_ai_marker=True)
    files = {"file": (filename, img_bytes, "image/png")}
    data = {"mode": "all"}
    response = client.post("/api/metadata/clean", files=files, data=data)
    assert response.status_code == 200
    assert "-cleaned" in response.headers.get("content-disposition", "")

    cleaned_bytes = response.content
    with Image.open(BytesIO(cleaned_bytes)) as cleaned:
        exif = cleaned.getexif()
        assert len(exif) == 0  # All metadata stripped
