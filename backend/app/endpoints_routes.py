import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pymongo.database import Database
from pymongo.errors import PyMongoError
from app.auth import current_user, get_db
from app.config import R2_BUCKET_NAME, R2_PUBLIC_BASE_URL
from app.image_cleaner import FORMAT_SETTINGS, clean_ai_exif_metadata, clean_all_metadata
from app.image_validation import read_and_validate_image
from app.metadata_extractor import extract_metadata
from app.schemas.accounts import EndpointCreate, EndpointUpdate
from app.schemas.metadata import CleanMode
from app.storage import put_image, get_image, delete_image

router = APIRouter(tags=["User endpoints", "Public endpoints"])
MAX_IMAGES_PER_ENDPOINT = 10

def now_utc():
    return datetime.now(timezone.utc)

def require_owned_endpoint(db: Database, endpoint_id: str, user: dict) -> dict:
    endpoint = db.endpoints.find_one({"endpoint_id": endpoint_id, "user_id": str(user["_id"])})
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found.")
    return endpoint

def image_url(endpoint_id: str, image_id: str) -> str:
    return f"/api/public/{endpoint_id}/images/{image_id}"

@router.post("/api/endpoints", status_code=201)
def create_endpoint(payload: EndpointCreate, user: dict = Depends(current_user), db: Database = Depends(get_db)):
    now = now_utc()
    endpoint_id = secrets.token_urlsafe(32)
    doc = {"endpoint_id": endpoint_id, "user_id": str(user["_id"]), "name": payload.name.strip(), "created_at": now, "updated_at": now}
    db.endpoints.insert_one(doc)
    return {"endpoint_id": endpoint_id, "name": doc["name"], "created_at": now, "updated_at": now, "image_count": 0, "public_url": f"/api/public/{endpoint_id}"}

@router.get("/api/endpoints")
def list_endpoints(user: dict = Depends(current_user), db: Database = Depends(get_db)):
    result = []
    for endpoint in db.endpoints.find({"user_id": str(user["_id"])}).sort("created_at", -1):
        count = db.endpoint_images.count_documents({"endpoint_id": endpoint["endpoint_id"]})
        result.append({"endpoint_id": endpoint["endpoint_id"], "name": endpoint["name"], "created_at": endpoint["created_at"], "updated_at": endpoint["updated_at"], "image_count": count, "public_url": f"/api/public/{endpoint['endpoint_id']}"})
    return result

@router.patch("/api/endpoints/{endpoint_id}")
def rename_endpoint(endpoint_id: str, payload: EndpointUpdate, user: dict = Depends(current_user), db: Database = Depends(get_db)):
    require_owned_endpoint(db, endpoint_id, user)
    db.endpoints.update_one({"endpoint_id": endpoint_id}, {"$set": {"name": payload.name.strip(), "updated_at": now_utc()}})
    return {"endpoint_id": endpoint_id, "name": payload.name.strip()}

@router.delete("/api/endpoints/{endpoint_id}", status_code=204)
def delete_endpoint(endpoint_id: str, user: dict = Depends(current_user), db: Database = Depends(get_db)):
    require_owned_endpoint(db, endpoint_id, user)
    images = list(db.endpoint_images.find({"endpoint_id": endpoint_id}))
    for item in images:
        try:
            delete_image(item["object_key"])
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc))
    db.endpoint_images.delete_many({"endpoint_id": endpoint_id})
    db.endpoints.delete_one({"endpoint_id": endpoint_id, "user_id": str(user["_id"])})

@router.post("/api/endpoints/{endpoint_id}/images", status_code=201)
async def add_cleaned_image(endpoint_id: str, file: UploadFile = File(...), mode: CleanMode = Form(CleanMode.ALL), user: dict = Depends(current_user), db: Database = Depends(get_db)):
    require_owned_endpoint(db, endpoint_id, user)
    image_data = await read_and_validate_image(file)
    if mode == CleanMode.AI_ONLY:
        cleaned = clean_ai_exif_metadata(image_data["contents"], image_data["format"])
    else:
        cleaned = clean_all_metadata(image_data["contents"], image_data["format"])
    metadata = extract_metadata(image_data)
    image_id = secrets.token_urlsafe(18)
    extension = FORMAT_SETTINGS[image_data["format"]]["extension"]
    filename = f"{__import__('pathlib').Path(image_data['filename']).stem}-cleaned{extension}"
    object_key = f"endpoints/{endpoint_id}/{image_id}{extension}"
    try:
        put_image(object_key, cleaned, FORMAT_SETTINGS[image_data["format"]]["media_type"])
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    now = now_utc()
    doc = {"image_id": image_id, "endpoint_id": endpoint_id, "object_key": object_key, "filename": filename, "format": image_data["format"], "marker_count": metadata.ai_marker_count, "size_bytes": len(cleaned), "created_at": now}
    db.endpoint_images.insert_one(doc)
    # FIFO: remove the oldest images beyond the most recent 10.

    image_count = db.endpoint_images.count_documents(
        {"endpoint_id": endpoint_id}
    )

    excess_count = max(0, image_count - MAX_IMAGES_PER_ENDPOINT)

    old = list(
        db.endpoint_images.find(
            {"endpoint_id": endpoint_id}
        )
        .sort([("created_at", 1), ("_id", 1)])
        .limit(excess_count)
    )

    for item in old:
        try:
            delete_image(item["object_key"])
        finally:
            db.endpoint_images.delete_one({"image_id": item["image_id"]})
    return {"image_id": image_id, "filename": filename, "format": image_data["format"], "marker_count": metadata.ai_marker_count, "size_bytes": len(cleaned), "created_at": now, "url": image_url(endpoint_id, image_id)}

@router.delete("/api/endpoints/{endpoint_id}/images/{image_id}", status_code=204)
def delete_endpoint_image(endpoint_id: str, image_id: str, user: dict = Depends(current_user), db: Database = Depends(get_db)):
    require_owned_endpoint(db, endpoint_id, user)
    item = db.endpoint_images.find_one({"endpoint_id": endpoint_id, "image_id": image_id})
    if not item:
        raise HTTPException(status_code=404, detail="Image not found.")
    try:
        delete_image(item["object_key"])
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    db.endpoint_images.delete_one({"image_id": image_id, "endpoint_id": endpoint_id})

@router.get("/api/public/{endpoint_id}")
def public_endpoint(endpoint_id: str, db: Database = Depends(get_db)):
    endpoint = db.endpoints.find_one({"endpoint_id": endpoint_id}, {"_id": 0, "endpoint_id": 1, "name": 1, "created_at": 1})
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found.")
    images = db.endpoint_images.find({"endpoint_id": endpoint_id}, {"_id": 0, "image_id": 1, "filename": 1, "format": 1, "marker_count": 1, "size_bytes": 1, "created_at": 1}).sort("created_at", -1).limit(MAX_IMAGES_PER_ENDPOINT)
    return {"endpoint": endpoint, "images": [{**item, "url": image_url(endpoint_id, item["image_id"])} for item in images]}

@router.get("/api/public/{endpoint_id}/images/{image_id}")
def public_image(endpoint_id: str, image_id: str, db: Database = Depends(get_db)):
    item = db.endpoint_images.find_one({"endpoint_id": endpoint_id, "image_id": image_id})
    if not item:
        raise HTTPException(status_code=404, detail="Image not found.")
    try:
        data, content_type = get_image(item["object_key"])
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return Response(content=data, media_type=content_type, headers={"Content-Disposition": f'inline; filename="{item["filename"]}"', "X-Content-Type-Options": "nosniff"})
