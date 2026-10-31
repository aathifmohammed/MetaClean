from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pymongo.errors import PyMongoError
from app.config import CORS_ORIGINS
from app.db.mongodb import lifespan
from app.metadata_routes import router as metadata_router
from app.accounts_routes import router as accounts_router
from app.endpoints_routes import router as endpoints_router

FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend-dist"

app = FastAPI(
    title="MetaClean API",
    description="Check and clean image metadata, manage saved cleaned-image endpoints.",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

@app.get("/")
def root():
    frontend_index = FRONTEND_DIR / "index.html"
    if frontend_index.is_file():
        return FileResponse(frontend_index)
    return {"message": "Welcome to MetaClean API", "status": "running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/health/database")
def database_health(request: Request):
    try:
        request.app.state.mongo_client.admin.command("ping")
        return {"status": "healthy", "database": "connected"}
    except (PyMongoError, AttributeError, Exception):
        return {"status": "unhealthy", "database": "disconnected"}

app.include_router(metadata_router)
app.include_router(accounts_router)
app.include_router(endpoints_router)

# The Docker image includes the production Vite build. Keep this mount last so
# API, health, and OpenAPI routes are matched before the frontend static files.
if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
