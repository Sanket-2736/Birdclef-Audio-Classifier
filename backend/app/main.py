from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .pipeline import predict_pipeline
from .config import get_settings
from .db import init_db
from .routers import auth, recordings, stats


# Initialize settings
settings = get_settings()

# Initialize database
init_db()

# Create app
app = FastAPI(
    title="BirdCLEF Audio Classifier",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN, "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(recordings.router)
app.include_router(stats.router)

BASE_DIR = Path(__file__).resolve().parent.parent


app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)


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