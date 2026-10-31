from typing import Any
from app.extractors.exiftool_extractor import extract_all_metadata


def extract_png_metadata(source: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(source, dict):
        metadata = source
    else:
        try:
            metadata = extract_all_metadata(source)
        except Exception:
            metadata = {}

    return {
        key: value
        for key, value in metadata.items()
        if key.split(":", 1)[0].startswith("PNG")
    }
