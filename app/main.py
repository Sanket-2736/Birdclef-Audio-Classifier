from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .pipeline import predict_pipeline


app = FastAPI(
    title="BirdCLEF Audio Classifier",
    version="1.0.0",
)


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


@app.post("/predict")
async def predict(
    audio: UploadFile = File(...),
    site_id: int = Form(0),
    hour_id: int = Form(12),
):

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

    uploads_dir.mkdir(
        exist_ok=True
    )


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