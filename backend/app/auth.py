from datetime import datetime, timezone
import hashlib
import logging
import secrets

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from pymongo.database import Database

from app.config import GOOGLE_CLIENT_ID

_bearer = HTTPBearer(auto_error=False)
_logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_db(request: Request) -> Database | None:
    return getattr(request.app.state, "db", None)


def _user_from_credentials(credentials: HTTPAuthorizationCredentials, db: Database | None) -> dict:
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=503, detail="Google sign-in is not configured on the server.")
    if db is None:
        raise HTTPException(status_code=503, detail="Database is currently unavailable.")
    try:
        claims = id_token.verify_oauth2_token(
            credentials.credentials,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=60,
        )
    except Exception as error:
        # Never log the credential itself; the validation reason is enough to
        # distinguish expiry, audience mismatch, and issuer/configuration errors.
        _logger.warning(
            "Google ID token validation failed (%s): %s",
            type(error).__name__, error,
        )
        reason = str(error).lower()
        if "expired" in reason:
            detail = "Google sign-in token expired. Sign out and complete Google sign-in again."
        elif "audience" in reason or "recipient" in reason:
            detail = "Google token audience does not match the backend GOOGLE_CLIENT_ID. Restart the backend after updating backend/.env."
        elif "issuer" in reason:
            detail = "Google token issuer was rejected. Check the Google OAuth client configuration."
        else:
            safe_reason = str(error).replace(credentials.credentials, "[credential]").replace("\n", " ")[:240]
            detail = f"Google credential validation failed ({type(error).__name__}): {safe_reason or 'no additional reason provided'}"
        raise HTTPException(status_code=401, detail=detail)
    google_id = claims.get("sub")
    email = claims.get("email")
    if not google_id or not claims.get("email_verified", False):
        raise HTTPException(status_code=401, detail="Google account email must be verified.")
    now = utc_now()
    db.users.update_one(
        {"google_id": google_id},
        {"$set": {"email": email, "name": claims.get("name"), "picture": claims.get("picture"), "updated_at": now},
         "$setOnInsert": {"google_id": google_id, "created_at": now}},
        upsert=True,
    )
    return db.users.find_one({"google_id": google_id})


def current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Database | None = Depends(get_db),
) -> dict:
    if credentials is not None and credentials.scheme.lower() == "bearer":
        return _user_from_credentials(credentials, db)
    session = request.cookies.get("metaclean_session")
    if session and db is not None:
        record = db.sessions.find_one({"session_hash": hashlib.sha256(session.encode()).hexdigest(), "expires_at": {"$gt": utc_now()}})
        user = db.users.find_one({"google_id": record.get("google_id")}) if record else None
        if user:
            return user
    raise HTTPException(status_code=401, detail="Sign in with Google to use this feature.")


def optional_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Database | None = Depends(get_db),
) -> dict | None:
    try:
        return current_user(request, credentials, db)
    except Exception as error:
        # Image inspection and cleaning must remain usable if optional account
        # lookup/session storage is unavailable. Activity logging is skipped.
        _logger.warning("Optional account lookup skipped for image processing (%s).", type(error).__name__)
        return None
