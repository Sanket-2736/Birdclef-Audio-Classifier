
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

import logging
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] [%(name)s] %(message)s")
logging.getLogger("birdclef.performance").propagate = False  # avoid duplicate lines

print("\n[DEBUG] Importing BirdCLEF FastAPI application...")


# Initialize performance logger for startup
print("[DEBUG] Initializing performance logger...")
perf_logger = get_perf_logger()

print("[SUCCESS] Performance logger initialized.")


# Log startup
startup_start = time.perf_counter()

perf_logger.info("=" * 60)
perf_logger.info("BIRDCLEF BACKEND STARTUP")
perf_logger.info("=" * 60)

print("\n" + "=" * 60)
print("[DEBUG] BIRDCLEF BACKEND STARTUP")
print("=" * 60)


# Initialize settings
print("\n[DEBUG] Initializing application settings...")

with log_stage("Settings Initialization"):

    settings = get_settings()

    print("[SUCCESS] Application settings loaded.")

    print(f"[DEBUG] Database URL: {settings.DATABASE_URL}")
    print(f"[DEBUG] Debug mode: {settings.DEBUG}")
    print(f"[DEBUG] Frontend origin: {settings.FRONTEND_ORIGIN}")
    print(f"[DEBUG] Storage root: {settings.STORAGE_ROOT}")
    print(f"[DEBUG] Maximum upload size: {settings.MAX_UPLOAD_MB} MB")
    print(f"[DEBUG] Inference timeout: {settings.INFERENCE_TIMEOUT_SEC}s")


# Initialize database
print("\n[DEBUG] Starting database initialization...")

with log_stage("Database Initialization"):

    init_db()

    print("[SUCCESS] Database initialization completed.")


# Create app
print("\n[DEBUG] Creating FastAPI application...")

with log_stage("FastAPI App Creation"):

    app = FastAPI(
        title="BirdCLEF Audio Classifier",
        version="1.0.0",
    )

    print("[SUCCESS] FastAPI application created.")
    print(f"[DEBUG] Application title: {app.title}")
    print(f"[DEBUG] Application version: {app.version}")


# Add CORS middleware
print("\n[DEBUG] Configuring CORS middleware...")

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

    print("[SUCCESS] CORS middleware registered.")

    print("[DEBUG] Allowed origins:")
    print("    - http://localhost:5173")
    print("    - http://localhost:5174")
    print("    - http://127.0.0.1:5173")
    print("    - http://127.0.0.1:5174")
    print("    - http://localhost:3000")

    print("[DEBUG] Allowed methods: All")
    print("[DEBUG] Allowed headers: All")
    print("[DEBUG] Credentials enabled: True")


# Include routers
print("\n[DEBUG] Registering application routers...")

with log_stage("Router Registration"):

    print("[DEBUG] Registering recordings router...")
    app.include_router(auth.router)
    print("[SUCCESS] Authentication router registered.")

    print("[DEBUG] Registering recordings router...")
    app.include_router(recordings.router)
    print("[SUCCESS] Recordings router registered.")

    print("[DEBUG] Registering log-mel spectrogram router...")
    from .routers import logmel
    app.include_router(logmel.router)
    print("[SUCCESS] Log-Mel Spectrogram router registered.")

    print("[DEBUG] Registering statistics router...")
    app.include_router(stats.router)
    print("[SUCCESS] Statistics router registered.")


# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

print(f"\n[DEBUG] Application BASE_DIR: {BASE_DIR}")


# Static files mount
print("\n[DEBUG] Mounting static files...")

with log_stage("Static Files Mount"):

    static_dir = BASE_DIR / "static"

    print(f"[DEBUG] Static directory: {static_dir}")
    print(f"[DEBUG] Static directory exists: {static_dir.exists()}")

    app.mount(
        "/static",
        StaticFiles(directory=BASE_DIR / "static"),
        name="static",
    )

    print("[SUCCESS] Static files mounted at /static.")


# Startup duration
startup_duration = time.perf_counter() - startup_start

perf_logger.info(f"Startup completed in {startup_duration:.2f}s")
perf_logger.info("=" * 60)

print("\n" + "=" * 60)
print("[SUCCESS] BIRDCLEF BACKEND STARTUP COMPLETED")
print(f"[DEBUG] Total startup duration: {startup_duration:.2f}s")
print("=" * 60)


# ============================================================
# HOME ENDPOINT
# ============================================================

@app.get("/")
async def home():

    print("\n[DEBUG] GET / endpoint called.")

    index_path = BASE_DIR / "static" / "index.html"

    print(f"[DEBUG] Index file path: {index_path}")
    print(f"[DEBUG] Index file exists: {index_path.exists()}")

    print("[DEBUG] Returning frontend index.html.")

    return FileResponse(
        index_path
    )


# ============================================================
# HEALTH CHECK ENDPOINT
# ============================================================

@app.get("/health")
async def health():
    """Health check endpoint."""

    print("\n[DEBUG] GET /health endpoint called.")

    response = {"status": "healthy"}

    print(f"[DEBUG] Health check response: {response}")

    return response


# ============================================================
# PREDICTION ENDPOINT
# ============================================================

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

    print("\n" + "=" * 60)
    print("[DEBUG] POST /predict ENDPOINT CALLED")
    print("=" * 60)

    # --------------------------------------------------------
    # Request information
    # --------------------------------------------------------

    print("\n[DEBUG] Reading request metadata...")

    print(f"[DEBUG] Uploaded filename: {audio.filename}")
    print(f"[DEBUG] Content type: {audio.content_type}")
    print(f"[DEBUG] Site ID: {site_id}")
    print(f"[DEBUG] Hour ID: {hour_id}")

    # --------------------------------------------------------
    # Validate site ID
    # --------------------------------------------------------

    print("\n[DEBUG] Validating site_id...")

    if not 0 <= site_id <= 19:

        print("[ERROR] Invalid site_id received.")
        print(f"[ERROR] Received site_id: {site_id}")
        print("[ERROR] Expected range: 0-19")

        raise HTTPException(
            status_code=400,
            detail="site_id must be between 0 and 19",
        )

    print("[SUCCESS] site_id validation passed.")

    # --------------------------------------------------------
    # Validate hour ID
    # --------------------------------------------------------

    print("\n[DEBUG] Validating hour_id...")

    if not 0 <= hour_id <= 23:

        print("[ERROR] Invalid hour_id received.")
        print(f"[ERROR] Received hour_id: {hour_id}")
        print("[ERROR] Expected range: 0-23")

        raise HTTPException(
            status_code=400,
            detail="hour_id must be between 0 and 23",
        )

    print("[SUCCESS] hour_id validation passed.")

    # --------------------------------------------------------
    # Prepare upload directory
    # --------------------------------------------------------

    print("\n[DEBUG] Preparing upload directory...")

    uploads_dir = BASE_DIR / "uploads"

    print(f"[DEBUG] Upload directory: {uploads_dir}")

    uploads_dir.mkdir(exist_ok=True)

    print("[SUCCESS] Upload directory ready.")

    save_path = uploads_dir / audio.filename

    print(f"[DEBUG] Audio save path: {save_path}")

    # --------------------------------------------------------
    # Process uploaded audio
    # --------------------------------------------------------

    try:

        print("\n[DEBUG] Reading uploaded audio contents...")

        contents = await audio.read()

        print("[SUCCESS] Audio contents read successfully.")
        print(f"[DEBUG] Uploaded file size: {len(contents):,} bytes")

        # Save uploaded audio
        print("\n[DEBUG] Saving uploaded audio to disk...")

        with open(save_path, "wb") as f:

            f.write(contents)

        print("[SUCCESS] Audio file saved successfully.")
        print(f"[DEBUG] Saved file exists: {save_path.exists()}")

        # Run prediction pipeline
        print("\n" + "-" * 60)
        print("[DEBUG] STARTING BIRDCLEF PREDICTION PIPELINE")
        print("-" * 60)

        inference_start = time.perf_counter()

        result = predict_pipeline(
            audio_path=save_path,
            site_id=site_id,
            hour_id=hour_id,
        )

        inference_duration = time.perf_counter() - inference_start

        print("\n[SUCCESS] Prediction pipeline completed.")

        print(f"[DEBUG] Inference duration: {inference_duration:.2f}s")
        print(f"[DEBUG] Result type: {type(result).__name__}")

        if isinstance(result, dict):

            print(f"[DEBUG] Result keys: {list(result.keys())}")

        print("\n[DEBUG] Returning prediction response.")

        return result

    finally:

        # ----------------------------------------------------
        # Cleanup uploaded file
        # ----------------------------------------------------

        print("\n[DEBUG] Executing upload cleanup...")

        if save_path.exists():

            print(f"[DEBUG] Removing temporary file: {save_path}")

            save_path.unlink()

            print("[SUCCESS] Temporary uploaded file removed.")

        else:

            print("[DEBUG] Temporary uploaded file does not exist.")

        print("[DEBUG] POST /predict request processing finished.")

        print("=" * 60)

# uvicorn app.main:app --reload
# python -u -m uvicorn app.main:app --host 127.0.0.1 --port 8000