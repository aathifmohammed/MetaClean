from io import BytesIO
import os
from pathlib import Path
import tempfile
from typing import Any
from PIL import Image, ExifTags

from app.extractors.exiftool_extractor import extract_with_exiftool
from app.extractors.c2pa_extractor import extract_c2pa
from app.ai_marker_detector import (
    detect_ai_markers,
    format_ai_markers_for_ui,
    generate_structured_report,
)


class MetadataResult(dict):
    """Result object supporting both attribute access (e.g. .ai_marker_count) and dict access."""
    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'MetadataResult' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


def _extract_pillow_metadata(image: Image.Image) -> dict[str, Any]:
    """Fallback extraction using Pillow if ExifTool is not available."""
    metadata = {}
    try:
        exif = image.getexif()
        if exif:
            for tag_id, value in exif.items():
                tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                metadata[f"EXIF:{tag_name}"] = str(value)
    except Exception:
        pass

    try:
        for k, v in getattr(image, "text", {}).items():
            metadata[f"PNG:{k}"] = str(v)
    except Exception:
        pass

    return metadata


def analyze_image(file_path: str) -> dict[str, Any]:
    """Perform complete metadata analysis on a file path."""
    exiftool_result = extract_with_exiftool(file_path)
    metadata = exiftool_result.get("metadata", {})

    c2pa_result = extract_c2pa(file_path)

    with Image.open(file_path) as image:
        image_info = {
            "format": image.format,
            "width": image.width,
            "height": image.height,
            "mode": image.mode,
            "has_transparency": (
                "A" in image.getbands() or "transparency" in image.info
            ),
        }
        # If ExifTool didn't find metadata or wasn't available, merge Pillow EXIF
        if not metadata:
            pillow_meta = _extract_pillow_metadata(image)
            metadata.update(pillow_meta)

    ai_markers = detect_ai_markers(metadata, c2pa_result)

    return {
        "image": image_info,
        "metadata": metadata,
        "metadata_extraction": {
            "available": exiftool_result["available"],
            "error": exiftool_result["error"],
        },
        "c2pa": c2pa_result,
        "ai_analysis": {
            "detected": len(ai_markers) > 0,
            "signal_count": len(ai_markers),
            "signals": ai_markers,
        },
    }


def extract_metadata(image_source: dict[str, Any] | str | bytes) -> MetadataResult:
    """
    Extract metadata and format for both route handlers and frontend response.
    Supports image_data dict (from read_and_validate_image), file path string, or raw bytes.
    """
    temp_path = None
    filename = "image"
    file_format = None
    width = 0
    height = 0
    file_size_bytes = 0

    try:
        if isinstance(image_source, dict):
            filename = image_source.get("filename", "image")
            file_format = image_source.get("format")
            width = image_source.get("width", 0)
            height = image_source.get("height", 0)
            file_size_bytes = image_source.get("file_size_bytes", 0)
            contents = image_source.get("contents")

            if contents:
                suffix = Path(filename).suffix or ".tmp"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(contents)
                    temp_path = tmp.name
                analysis = analyze_image(temp_path)
            else:
                analysis = {
                    "image": {"format": file_format, "width": width, "height": height, "mode": "RGB", "has_transparency": False},
                    "metadata": {},
                    "metadata_extraction": {"available": False, "error": "No image bytes provided"},
                    "c2pa": {"available": False, "has_manifest": False},
                    "ai_analysis": {"detected": False, "signal_count": 0, "signals": []},
                }

        elif isinstance(image_source, str) and os.path.exists(image_source):
            filename = Path(image_source).name
            file_size_bytes = os.path.getsize(image_source)
            analysis = analyze_image(image_source)
            file_format = analysis["image"].get("format")
            width = analysis["image"].get("width", 0)
            height = analysis["image"].get("height", 0)

        elif isinstance(image_source, bytes):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as tmp:
                tmp.write(image_source)
                temp_path = tmp.name
            file_size_bytes = len(image_source)
            analysis = analyze_image(temp_path)
            file_format = analysis["image"].get("format")
            width = analysis["image"].get("width", 0)
            height = analysis["image"].get("height", 0)

        else:
            raise ValueError("Unsupported image source provided to extract_metadata.")

        raw_metadata = analysis.get("metadata", {})
        metadata_list = [
            {"key": str(k), "value": str(v)}
            for k, v in raw_metadata.items()
        ]

        ai_analysis = analysis.get("ai_analysis", {})
        signals = ai_analysis.get("signals", [])
        ui_markers = format_ai_markers_for_ui(signals)

        structured = generate_structured_report(
            raw_metadata,
            analysis.get("c2pa", {}),
            signals,
            analysis.get("image", {}),
        )

        warnings = []
        if analysis.get("metadata_extraction", {}).get("error"):
            warnings.append(analysis["metadata_extraction"]["error"])
        if analysis.get("c2pa", {}).get("has_manifest"):
            warnings.append("C2PA Content Credentials manifest detected.")

        result = MetadataResult({
            "filename": filename,
            "format": file_format or analysis["image"].get("format", "Unknown"),
            "width": width or analysis["image"].get("width", 0),
            "height": height or analysis["image"].get("height", 0),
            "file_size_bytes": file_size_bytes,
            "metadata_count": len(metadata_list),
            "metadata": metadata_list,
            "ai_marker_count": len(signals),
            "ai_markers": ui_markers,
            "warnings": warnings,
            "verdict": structured["verdict"],
            "ai_signals": structured["ai_signals"],
            "groups": structured["groups"],
            "ai_analysis": ai_analysis,
            "c2pa": analysis.get("c2pa", {}),
            "image": analysis.get("image", {}),
            "metadata_extraction": analysis.get("metadata_extraction", {}),
            "raw_metadata": raw_metadata,
        })
        return result

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
