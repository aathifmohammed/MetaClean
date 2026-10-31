from datetime import datetime, timezone
from pymongo.database import Database

MAX_ACTIVITIES = 10

def record_activity(db: Database, user_id: str, operation: str, filename: str, marker_count: int | None) -> None:
    now = datetime.now(timezone.utc)
    db.recent_activities.insert_one({"user_id": user_id, "operation": operation, "filename": filename, "marker_count": max(0, marker_count) if marker_count is not None else None, "created_at": now})
    old_records = db.recent_activities.find({"user_id": user_id}, {"_id": 1}).sort("created_at", -1).skip(MAX_ACTIVITIES)
    ids = [doc["_id"] for doc in old_records]
    if ids:
        db.recent_activities.delete_many({"_id": {"$in": ids}})
