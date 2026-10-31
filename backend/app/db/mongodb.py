from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.database import Database

from app.config import MONGODB_DATABASE, MONGODB_URI

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if not MONGODB_URI:
        raise RuntimeError("MONGODB_URI is missing. Configure it in .env.")
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    try:
        client.admin.command("ping")
        db = client[MONGODB_DATABASE]
        # Required indexes for lookups, sorting, and unique IDs.
        db.users.create_index([("google_id", ASCENDING)], unique=True)
        db.recent_activities.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
        db.endpoints.create_index([("endpoint_id", ASCENDING)], unique=True)
        db.endpoints.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
        db.endpoint_images.create_index([("image_id", ASCENDING)], unique=True)
        db.endpoint_images.create_index([("endpoint_id", ASCENDING), ("created_at", ASCENDING)])
        app.state.mongo_client = client
        app.state.db = db
        yield
    finally:
        client.close()

def get_database(app: FastAPI) -> Database:
    return app.state.db
