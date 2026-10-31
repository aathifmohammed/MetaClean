from io import BytesIO
from pathlib import Path
from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


def validate_image(file_path: str) -> dict:
    """Validate an image file from a filesystem path."""
    path = Path(file_path)
    if not path.is_file():
        raise HTTPException(status_code=400, detail="Image file does not exist.")
    
    file_size = path.stat().st_size
    if file_size == 0:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if file_size > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds the 10 MiB upload limit.")
        
    try:
        with Image.open(file_path) as image:
            image_format = image.format
            width, height = image.size
            if image_format not in ALLOWED_FORMATS:
                raise HTTPException(status_code=415, detail="Unsupported image format. Use JPEG, PNG, or WebP.")
            if width * height > MAX_IMAGE_PIXELS:
                raise HTTPException(status_code=413, detail="Image dimensions exceed the allowed limit.")
            image.verify()
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise HTTPException(status_code=415, detail="Unsupported or unreadable image format. Use JPEG, PNG, or WebP.")
        
    return {
        "filename": path.name,
        "format": image_format,
        "width": width,
        "height": height,
        "file_size_bytes": file_size,
    }


async def read_and_validate_image(file: UploadFile) -> dict:
    """Read and validate an uploaded image file."""
    contents = await file.read(MAX_UPLOAD_BYTES + 1)
    if not contents:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds the 10 MiB upload limit.")
    try:
        with Image.open(BytesIO(contents)) as image:
            image_format = image.format
            width, height = image.size
            if image_format not in ALLOWED_FORMATS:
                raise HTTPException(status_code=415, detail="Unsupported image format. Use JPEG, PNG, or WebP.")
            if width * height > MAX_IMAGE_PIXELS:
                raise HTTPException(status_code=413, detail="Image dimensions exceed the allowed limit.")
            image.verify()
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise HTTPException(status_code=415, detail="Unsupported or unreadable image format. Use JPEG, PNG, or WebP.")
    return {
        "filename": file.filename or "image",
        "format": image_format,
        "width": width,
        "height": height,
        "file_size_bytes": len(contents),
        "contents": contents,
    }
