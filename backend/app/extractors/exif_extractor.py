
from app.extractors.exiftool_extractor import extract_all_metadata


EXIF_GROUPS = {
    "EXIF",
    "ExifIFD",
    "IFD0",
    "IFD1",
    "GPS",
    "InteropIFD",
    "MakerNotes"
}


def extract_exif(file_path: str) -> dict:
    metadata = extract_all_metadata(file_path)

    return {
        key: value
        for key, value in metadata.items()
        if key.split(":", 1)[0] in EXIF_GROUPS
    }
