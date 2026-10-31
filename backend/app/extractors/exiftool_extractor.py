import json
import subprocess
from pathlib import Path
from typing import Any

from app.config import EXIFTOOL_PATH


def extract_all_metadata(file_path: str) -> dict[str, Any]:
    """Extract all supported metadata using ExifTool."""
    res = extract_with_exiftool(file_path)
    if not res["available"] and res["error"]:
        raise RuntimeError(f"ExifTool extraction failed: {res['error']}")
    return res["metadata"]


def extract_with_exiftool(file_path: str) -> dict[str, Any]:
    """Extract all supported metadata with availability and error reporting."""
    executable = Path(EXIFTOOL_PATH) if EXIFTOOL_PATH else None

    if not executable or not executable.is_file():
        return {
            "available": False,
            "metadata": {},
            "error": f"ExifTool was not found at {EXIFTOOL_PATH or '(not configured)'}",
        }

    try:
        result = subprocess.run(
            [
                str(executable),
                "-json",
                "-G1",
                "-a",
                "-s",
                str(file_path)
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )

        data = json.loads(result.stdout)
        if not data:
            return {"available": True, "metadata": {}, "error": None}

        metadata = data[0]
        metadata.pop("SourceFile", None)

        return {"available": True, "metadata": metadata, "error": None}

    except subprocess.TimeoutExpired as exc:
        return {
            "available": False,
            "metadata": {},
            "error": "Metadata extraction timed out.",
        }
    except subprocess.CalledProcessError as exc:
        return {
            "available": False,
            "metadata": {},
            "error": f"ExifTool extraction failed: {exc.stderr}",
        }
    except json.JSONDecodeError as exc:
        return {
            "available": False,
            "metadata": {},
            "error": "ExifTool returned invalid JSON.",
        }
    except Exception as exc:
        return {
            "available": False,
            "metadata": {},
            "error": str(exc),
        }
