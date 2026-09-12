from pathlib import Path
import shutil
import uuid

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Form,
    HTTPException,
)
from fastapi.middleware.cors import CORSMiddleware

from .pipeline import predict_pipeline


BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"

UPLOAD_DIR.mkdir(exist_ok=True)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="BirdCLEF 2026 API",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "BirdCLEF 2026 FastAPI Backend Running"
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "ok"
    }


# ============================================================
# PREDICT
# ============================================================

@app.post("/predict")
async def predict(
    audio: UploadFile = File(...),
    site_id: int = Form(0),
    hour_id: int = Form(12),
):

    # --------------------------------------------------------
    # Validate metadata
    # --------------------------------------------------------

    if site_id < 0 or site_id >= 20:
        raise HTTPException(
            status_code=400,
            detail="site_id must be between 0 and 19",
        )

    if hour_id < 0 or hour_id >= 24:
        raise HTTPException(
            status_code=400,
            detail="hour_id must be between 0 and 23",
        )

    # --------------------------------------------------------
    # Save uploaded audio
    # --------------------------------------------------------

    extension = Path(
        audio.filename or ".wav"
    ).suffix.lower()

    if not extension:
        extension = ".wav"

    filename = f"{uuid.uuid4()}{extension}"

    save_path = UPLOAD_DIR / filename

    try:

        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(
                audio.file,
                buffer,
            )

        # ----------------------------------------------------
        # Run complete pipeline
        # ----------------------------------------------------

        result = predict_pipeline(
            audio_path=save_path,
            site_id=site_id,
            hour_id=hour_id,
        )

        result["filename"] = audio.filename

        return result

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    finally:

        # ----------------------------------------------------
        # Always remove uploaded file
        # ----------------------------------------------------

        save_path.unlink(
            missing_ok=True
        )

# uvicorn app.main:app --reload