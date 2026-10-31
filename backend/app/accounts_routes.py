from datetime import timedelta
import hashlib
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from pymongo.database import Database
from app.auth import current_user, get_db, utc_now, _user_from_credentials
from app.config import SESSION_COOKIE_SAMESITE, SESSION_COOKIE_SECURE
from fastapi.security import HTTPAuthorizationCredentials
from app.schemas.accounts import UserResponse, ActivityResponse

router = APIRouter(prefix="/api/account", tags=["Account"])

class GoogleCredential(BaseModel):
    credential: str

@router.post("/session")
def create_session(payload: GoogleCredential, request: Request, response: Response, db: Database = Depends(get_db)):
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=payload.credential)
    user = _user_from_credentials(credentials, db)
    raw_session = secrets.token_urlsafe(32)
    expires = utc_now() + timedelta(days=7)
    db.sessions.insert_one({"session_hash": hashlib.sha256(raw_session.encode()).hexdigest(), "google_id": user["google_id"], "expires_at": expires, "created_at": utc_now()})
    response.set_cookie("metaclean_session", raw_session, max_age=7 * 24 * 60 * 60, httponly=True, secure=SESSION_COOKIE_SECURE or request.url.scheme == "https", samesite=SESSION_COOKIE_SAMESITE, path="/")
    return {"id": str(user["_id"]), "email": user.get("email"), "name": user.get("name"), "picture": user.get("picture")}

@router.post("/session/logout", status_code=204)
def delete_session(request: Request, response: Response, db: Database = Depends(get_db)):
    raw_session = request.cookies.get("metaclean_session")
    if raw_session and db is not None:
        db.sessions.delete_one({"session_hash": hashlib.sha256(raw_session.encode()).hexdigest()})
    response.delete_cookie("metaclean_session", path="/", httponly=True, secure=SESSION_COOKIE_SECURE or request.url.scheme == "https", samesite=SESSION_COOKIE_SAMESITE)

@router.get("/me", response_model=UserResponse)
def get_me(user: dict = Depends(current_user)):
    return {"id": str(user["_id"]), "email": user.get("email"), "name": user.get("name"), "picture": user.get("picture")}

@router.get("/activities", response_model=list[ActivityResponse])
def get_activities(user: dict = Depends(current_user), db: Database = Depends(get_db)):
    rows = db.recent_activities.find({"user_id": str(user["_id"])}, {"_id": 0, "operation": 1, "filename": 1, "marker_count": 1, "created_at": 1}).sort("created_at", -1).limit(10)
    return list(rows)
