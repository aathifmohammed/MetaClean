from io import BytesIO
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any
from PIL import Image, PngImagePlugin

from app.config import EXIFTOOL_PATH
from app.ai_marker_detector import AI_TOOLS, DIGITAL_SOURCE_TYPES

FORMAT_SETTINGS = {
    "JPEG": {"extension": ".jpg", "media_type": "image/jpeg"},
    "PNG": {"extension": ".png", "media_type": "image/png"},
    "WEBP": {"extension": ".webp", "media_type": "image/webp"},
}

# Compile flat list of lowercase marker strings
ALL_AI_MARKER_TERMS = [
    marker.lower()
    for markers in AI_TOOLS.values()
    for marker in markers
] + list(DIGITAL_SOURCE_TYPES.keys()) + [
    "containsaigeneratedcontent",
    "aigeneratedcontent",
    "canva ai",
    "canva magic",
]


def _has_ai_marker(value: Any) -> bool:
    """Check if any string representation of a metadata value contains AI markers."""
    if value is None:
        return False
    val_str = str(value).lower()
    return any(marker in val_str for marker in ALL_AI_MARKER_TERMS)


def clean_ai_exif_metadata(contents: bytes, image_format: str) -> bytes:
    """
    Remove AI-related EXIF and info fields while preserving photographic metadata.
    """
    fmt = image_format.upper()
    if fmt == "JPG":
        fmt = "JPEG"

    with Image.open(BytesIO(contents)) as image:
        # 1. Clean EXIF tags
        exif = image.getexif()
        tags_to_delete = []

        for tag_id, value in list(exif.items()):
            if _has_ai_marker(value):
                tags_to_delete.append(tag_id)

        for tag_id in tags_to_delete:
            del exif[tag_id]

        # Check sub-IFDs if available (e.g. ExifIFD 0x8769)
        try:
            exif_ifd = exif.get_ifd(0x8769)
            if exif_ifd:
                sub_tags_to_delete = [
                    k for k, v in exif_ifd.items() if _has_ai_marker(v)
                ]
                for k in sub_tags_to_delete:
                    del exif_ifd[k]
        except Exception:
            pass

        # 2. Build output
        output = BytesIO()
        exif_bytes = exif.tobytes() if len(exif) > 0 else None

        save_kwargs: dict[str, Any] = {}
        if exif_bytes:
            save_kwargs["exif"] = exif_bytes

        # If PNG, handle pnginfo without AI fields
        if fmt == "PNG":
            png_info = PngImagePlugin.PngInfo()
            has_png_info = False
            for k, v in getattr(image, "text", {}).items():
                if not _has_ai_marker(k) and not _has_ai_marker(v):
                    png_info.add_text(k, str(v))
                    has_png_info = True
            if has_png_info:
                save_kwargs["pnginfo"] = png_info

        # Preserve transparency or mode
        if fmt == "JPEG" and image.mode in ("RGBA", "P", "LA"):
            rgb_image = image.convert("RGB")
            rgb_image.save(output, format="JPEG", **save_kwargs)
        else:
            image.save(output, format=fmt, **save_kwargs)

        cleaned_bytes = output.getvalue()

    # Optional: If ExifTool is configured, strip AI-specific XMP tags if any
    executable = Path(EXIFTOOL_PATH) if EXIFTOOL_PATH else None
    if executable and executable.is_file():
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=FORMAT_SETTINGS.get(fmt, {}).get("extension", ".tmp")) as src_tmp:
                src_tmp.write(cleaned_bytes)
                src_path = src_tmp.name

            out_path = src_path + ".clean"

            # Delete common AI XMP and C2PA tags using ExifTool, keeping standard EXIF
            ai_tags_args = [
                "-XMP-dc:Description=",
                "-XMP:Prompt=",
                "-XMP:Workflow=",
                "-XMP:Parameters=",
                "-JUMBF:all=",
                "-o", out_path,
                src_path
            ]
            result = subprocess.run([str(executable)] + ai_tags_args, capture_output=True, timeout=15)
            if result.returncode == 0 and os.path.exists(out_path):
                with open(out_path, "rb") as f:
                    cleaned_bytes = f.read()
                os.remove(out_path)
            if os.path.exists(src_path):
                os.remove(src_path)
        except Exception:
            pass

    return cleaned_bytes


def clean_all_metadata(contents: bytes, image_format: str) -> bytes:
    """
    Remove all metadata (EXIF, IPTC, XMP, C2PA JUMBF, comments) completely.
    """
    fmt = image_format.upper()
    if fmt == "JPG":
        fmt = "JPEG"

    executable = Path(EXIFTOOL_PATH) if EXIFTOOL_PATH else None

    # First attempt with ExifTool for complete metadata stripping
    if executable and executable.is_file():
        temp_in = None
        temp_out = None
        try:
            ext = FORMAT_SETTINGS.get(fmt, {}).get("extension", ".jpg")
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
                f.write(contents)
                temp_in = f.name
            temp_out = temp_in + "-clean" + ext

            subprocess.run(
                [
                    str(executable),
                    "-all=",
                    "-JUMBF:all=",
                    "-overwrite_original" if False else "-o",
                    temp_out,
                    temp_in,
                ],
                capture_output=True,
                text=True,
                timeout=20,
                check=True,
            )

            if os.path.exists(temp_out):
                with open(temp_out, "rb") as f:
                    return f.read()
        except Exception:
            # Fall back to Pillow clean re-encoding
            pass
        finally:
            if temp_in and os.path.exists(temp_in):
                os.remove(temp_in)
            if temp_out and os.path.exists(temp_out):
                os.remove(temp_out)

    # Reliable fallback: Re-encode with Pillow, dropping all metadata and headers
    with Image.open(BytesIO(contents)) as image:
        output = BytesIO()
        # Create a new image of identical mode and size to discard all attached info/exif
        if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
            if fmt == "JPEG":
                clean_img = Image.new("RGB", image.size, (255, 255, 255))
                clean_img.paste(image, mask=image.split()[-1] if "A" in image.mode else None)
            else:
                clean_img = Image.new("RGBA", image.size)
                clean_img.paste(image)
        else:
            clean_img = Image.new("RGB", image.size)
            clean_img.paste(image)

        clean_img.save(output, format=fmt)
        return output.getvalue()


def clean_all_metadata_exiftool(input_path: str, output_path: str) -> str:
    """Remove metadata using ExifTool CLI."""
    executable = Path(EXIFTOOL_PATH) if EXIFTOOL_PATH else None
    if not executable or not executable.is_file():
        raise FileNotFoundError(f"ExifTool was not found: {EXIFTOOL_PATH}")

    command = [
        str(executable),
        "-all=",
        "-JUMBF:all=",
        "-o",
        output_path,
        input_path,
    ]

    subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )

    if not Path(output_path).exists():
        raise RuntimeError("Cleaned image was not created.")

    return output_path