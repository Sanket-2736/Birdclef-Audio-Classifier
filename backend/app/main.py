from pathlib import Path
import time

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .pipeline import predict_pipeline
from .config import get_settings
from .db import init_db
from .routers import auth, recordings, stats
from .utils import get_perf_logger, log_stage


# Initialize performance logger for startup
perf_logger = get_perf_logger()

# Log startup
startup_start = time.perf_counter()
perf_logger.info("="*60)
perf_logger.info("BIRDCLEF BACKEND STARTUP")
perf_logger.info("="*60)

# Initialize settings
with log_stage("Settings Initialization"):
    settings = get_settings()

# Initialize database
with log_stage("Database Initialization"):
    init_db()

# Create app
with log_stage("FastAPI App Creation"):
    app = FastAPI(
        title="BirdCLEF Audio Classifier",
        version="1.0.0",
    )

# Add CORS middleware
with log_stage("CORS Middleware Setup"):
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
            "http://localhost:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include routers
with log_stage("Router Registration"):
    app.include_router(auth.router)
    app.include_router(recordings.router)
    app.include_router(stats.router)

BASE_DIR = Path(__file__).resolve().parent.parent

with log_stage("Static Files Mount"):
    app.mount(
        "/static",
        StaticFiles(directory=BASE_DIR / "static"),
        name="static",
    )

startup_duration = time.perf_counter() - startup_start
perf_logger.info(f"Startup completed in {startup_duration:.2f}s")
perf_logger.info("="*60)


@app.get("/")
async def home():
    return FileResponse(
        BASE_DIR / "static" / "index.html"
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/predict")
async def predict(
    audio: UploadFile = File(...),
    site_id: int = Form(0),
    hour_id: int = Form(12),
):
    """
    Predict bird species from audio.
    
    - **audio**: Audio file (WAV, MP3, OGG)
    - **site_id**: Site ID (0-19)
    - **hour_id**: Hour of day (0-23)
    
    Returns predictions, detections, and metadata.
    """

    if not 0 <= site_id <= 19:
        raise HTTPException(
            status_code=400,
            detail="site_id must be between 0 and 19",
        )

    if not 0 <= hour_id <= 23:
        raise HTTPException(
            status_code=400,
            detail="hour_id must be between 0 and 23",
        )

    uploads_dir = BASE_DIR / "uploads"
    uploads_dir.mkdir(exist_ok=True)
    save_path = uploads_dir / audio.filename

    try:
        contents = await audio.read()

        with open(save_path, "wb") as f:
            f.write(contents)

        result = predict_pipeline(
            audio_path=save_path,
            site_id=site_id,
            hour_id=hour_id,
        )

        return result

    finally:
        if save_path.exists():
            save_path.unlink()


# uvicorn app.main:app --reload