from io import BytesIO
import logging
from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import StreamingResponse
from PIL import Image, ImageDraw
from pymongo.database import Database

from app.activity import record_activity
from app.auth import get_db, optional_user
from app.image_cleaner import (
    FORMAT_SETTINGS,
    clean_ai_exif_metadata,
    clean_all_metadata,
)
from app.image_validation import read_and_validate_image
from app.metadata_extractor import extract_metadata
from app.schemas.metadata import CleanMode, MetadataCheckResponse

router = APIRouter(
    prefix="/api/metadata",
    tags=["Metadata"]
)
_logger = logging.getLogger(__name__)


@router.post("/check", response_model=MetadataCheckResponse)
async def check_metadata(
    file: UploadFile = File(...),
    record_activity: bool = Form(True),
    user: dict | None = Depends(optional_user),
    db: Database | None = Depends(get_db),
):
    try:
        image_data = await read_and_validate_image(file)
        result = extract_metadata(image_data)

        if record_activity and user is not None and db is not None:
            try:
                record_activity(
                    db,
                    str(user["_id"]),
                    "check_metadata",
                    image_data["filename"],
                    result.ai_marker_count,
                )
            except Exception:
                _logger.exception("Failed to record image-check activity")

        return result

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )


@router.post("/clean")
async def clean_metadata(
    file: UploadFile = File(...),
    mode: CleanMode = Form(...),
    user: dict | None = Depends(optional_user),
    db: Database | None = Depends(get_db),
):
    image_data = await read_and_validate_image(file)

    if mode == CleanMode.AI_ONLY:
        cleaned_bytes = clean_ai_exif_metadata(image_data["contents"], image_data["format"])
    else:
        cleaned_bytes = clean_all_metadata(image_data["contents"], image_data["format"])

    marker_count = extract_metadata(image_data).ai_marker_count

    if user is not None and db is not None:
        try:
            record_activity(
                db,
                str(user["_id"]),
                f"clean_{mode.value}",
                image_data["filename"],
                marker_count,
            )
        except Exception:
            _logger.exception("Failed to record image-clean activity")

    original_name = Path(image_data["filename"]).name
    settings = FORMAT_SETTINGS[image_data["format"]]
    suffix = "-ai-cleaned" if mode == CleanMode.AI_ONLY else "-cleaned"
    download_name = f"{Path(original_name).stem}{suffix}{settings['extension']}"

    return StreamingResponse(
        iter([cleaned_bytes]),
        media_type=settings["media_type"],
        headers={
            "Content-Disposition": f'attachment; filename="{download_name}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@router.get("/samples/{sample_type}")
def get_sample_image(sample_type: str):
    """Generate a sample JPEG image for testing detection and cleaning."""
    img = Image.new("RGB", (400, 300), color=(30, 35, 55))
    draw = ImageDraw.Draw(img)

    exif = Image.Exif()
    output = BytesIO()

    if sample_type == "ai":
        # Draw gradient-like banner
        draw.rectangle([20, 20, 380, 280], fill=(45, 52, 85), outline=(130, 115, 245), width=2)
        draw.text((40, 50), "MetaClean AI Sample Image", fill=(240, 240, 255))
        draw.text((40, 90), "Tool: Midjourney v6.0", fill=(255, 180, 120))
        draw.text((40, 120), "Refiner: Stable Diffusion XL", fill=(255, 180, 120))
        draw.text((40, 160), "Artist: AI Artist Alex", fill=(200, 210, 230))
        draw.text((40, 200), "Click 'Check Metadata' to inspect", fill=(180, 180, 200))

        exif[305] = "Midjourney v6.0"  # Software
        exif[270] = "Prompt: cybernetic city, synthwave aesthetic, photorealistic --v 6.0"  # ImageDescription
        exif[315] = "AI Artist Alex"  # Artist
        exif[37510] = "Refined with Stable Diffusion XL"  # UserComment
        filename = "sample-ai-midjourney.jpg"
    else:
        # Standard camera photo sample
        draw.rectangle([20, 20, 380, 280], fill=(25, 60, 50), outline=(50, 180, 120), width=2)
        draw.text((40, 50), "MetaClean Camera Sample Photo", fill=(240, 255, 245))
        draw.text((40, 90), "Camera: Canon EOS R5", fill=(130, 230, 180))
        draw.text((40, 130), "Lens: EF 50mm f/1.2L", fill=(130, 230, 180))
        draw.text((40, 170), "Photographer: Jane Doe Photography", fill=(200, 240, 220))

        exif[271] = "Canon"  # Make
        exif[272] = "Canon EOS R5"  # Model
        exif[315] = "Jane Doe Photography"  # Artist
        exif[33434] = (1, 250)  # ExposureTime
        exif[34855] = 100  # ISOSpeedRatings
        filename = "sample-camera-photo.jpg"

    img.save(output, format="JPEG", exif=exif.tobytes())
    return Response(
        content=output.getvalue(),
        media_type="image/jpeg",
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )
