"""
Recording upload and management endpoints.
"""

import hashlib
import asyncio
from uuid import uuid4
from pathlib import Path
from threading import Semaphore
from datetime import datetime
from typing import Optional
import numpy as np

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
import soundfile as sf
from pydantic import BaseModel

from ..db import get_db
from ..db_models import User, Recording, Prediction, Detection, Feedback
from ..config import get_settings
from ..storage import get_storage
from ..routers.auth import get_current_user


# ============================================================
# SCHEMAS
# ============================================================

class FeedbackRequest(BaseModel):
    """User feedback request."""
    species_code: str
    window_index: int = None
    is_correct: bool


router = APIRouter(prefix="/recordings", tags=["recordings"])
settings = get_settings()
storage = get_storage()

# Semaphore to ensure only one inference runs at a time (models are memory-heavy)
_inference_semaphore = Semaphore(1)


def get_file_extension(filename: str) -> str:
    """Extract file extension without dot."""
    return Path(filename).suffix.lstrip(".").lower()


def validate_upload(
    file: UploadFile,
    site_id: int,
    hour: int,
) -> tuple[str, str]:
    """
    Validate upload parameters.
    
    Returns (extension, error_message) or (ext, "") if valid
    """
    # Validate site_id and hour
    if not isinstance(site_id, int) or site_id < 0:
        raise HTTPException(
            status_code=400,
            detail="site_id must be a non-negative integer",
        )
    
    if not isinstance(hour, int) or not (0 <= hour <= 23):
        raise HTTPException(
            status_code=400,
            detail="hour must be between 0 and 23",
        )
    
    # Validate file extension
    ext = get_file_extension(file.filename or "")
    if ext not in settings.ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported audio format. Allowed: {', '.join(settings.ALLOWED_AUDIO_EXTENSIONS)}",
        )
    
    return ext


async def validate_audio_file(
    file_content: bytes,
    ext: str,
) -> tuple[float, int]:
    """
    Validate audio file can be decoded and return duration and sample rate.
    
    Returns (duration_sec, sample_rate)
    """
    # Check size
    file_size_mb = len(file_content) / (1024 * 1024)
    if file_size_mb > settings.MAX_UPLOAD_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum {settings.MAX_UPLOAD_MB} MB",
        )
    
    # Save to temp file and try to load
    temp_path = Path("/tmp") / f"validate_{uuid4()}.{ext}"
    try:
        temp_path.write_bytes(file_content)
        
        # Try to read with soundfile
        data, sr = sf.read(temp_path, dtype="float32")
        duration = len(data) / sr
        
        if duration < 1.0:
            raise HTTPException(
                status_code=400,
                detail="Audio file must be at least 1 second long",
            )
        
        return duration, sr
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=400,
            detail=f"Failed to decode audio file: {str(e)[:100]}",
        )
    finally:
        temp_path.unlink(missing_ok=True)


def compute_sha256(data: bytes) -> str:
    """Compute SHA-256 hash of file content."""
    return hashlib.sha256(data).hexdigest()


def process_inference_background(
    recording_id: str,
    stored_path: str,
    site_id: int,
    hour: int,
):
    """
    Background task to run inference on a recording.
    Updates recording status and creates prediction results.
    """
    from ..db import SessionLocal
    from ..pipeline import predict_pipeline
    
    db = SessionLocal()
    
    try:
        # Acquire semaphore to ensure only one inference at a time
        acquired = _inference_semaphore.acquire(blocking=True, timeout=3600)  # 1 hour timeout
        if not acquired:
            raise RuntimeError("Could not acquire inference semaphore")
        
        try:
            # Load recording
            recording = db.query(Recording).filter(Recording.id == recording_id).first()
            if not recording:
                return
            
            # Set to processing
            recording.status = "processing"
            recording.progress_stage = "Loading audio"
            db.commit()
            
            # Get full path
            full_path = storage.open_path(stored_path)
            
            # Run pipeline with progress callback
            def progress_callback(stage: str):
                recording.progress_stage = stage
                db.commit()
            
            # Run inference
            result = predict_pipeline(
                audio_path=str(full_path),
                site_id=site_id,
                hour_id=hour,
                progress_callback=progress_callback,
            )
            
            # Save prediction
            prediction = Prediction(
                recording_id=recording_id,
                result_json=result,
                top_species=result.get("top_species", []),
            )
            db.add(prediction)
            
            # Create detection records for each top species
            for species_info in result.get("top_species", []):
                detection = Detection(
                    recording_id=recording_id,
                    species_code=species_info.get("code", ""),
                    species_name=species_info.get("common_name", ""),
                    taxon=species_info.get("taxon", ""),
                    max_score=species_info.get("max_score", 0.0),
                    windows_detected=species_info.get("windows_detected", 0),
                )
                db.add(detection)
            
            # Mark as done
            recording.status = "done"
            recording.progress_stage = "Completed"
            db.commit()
        
        finally:
            _inference_semaphore.release()
    
    except Exception as e:
        # Mark as failed
        recording = db.query(Recording).filter(Recording.id == recording_id).first()
        if recording:
            recording.status = "failed"
            recording.error_message = str(e)[:500]
            db.commit()
    
    finally:
        db.close()


@router.post("/", status_code=202)
async def upload_recording(
    file: UploadFile = File(...),
    site_id: int = Form(0),
    hour: int = Form(12),
    lat: float = Form(None),
    lng: float = Form(None),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload an audio file for inference.
    
    - **file**: Audio file (.wav, .ogg, .mp3, .flac)
    - **site_id**: Site ID (integer >= 0)
    - **hour**: Hour of day (0-23)
    - **lat**: Latitude (optional)
    - **lng**: Longitude (optional)
    
    Returns immediately with recording ID. Inference runs in background.
    Poll /recordings/{id}/status for progress.
    """
    
    # Validate inputs
    ext = validate_upload(file, site_id, hour)
    
    # Read file content
    file_content = await file.read()
    
    # Validate audio file
    duration, sample_rate = await validate_audio_file(file_content, ext)
    
    # Compute hash
    sha256 = compute_sha256(file_content)
    
    # Check for duplicates
    existing = db.query(Recording).filter(
        Recording.sha256 == sha256,
        Recording.user_id == current_user.id,
    ).first()
    
    if existing:
        # Return existing recording with duplicate flag
        return {
            "id": existing.id,
            "status": existing.status,
            "duplicate": True,
            "existing_id": existing.id,
            "message": "This file was already uploaded",
        }
    
    # Generate file ID and save
    file_id = str(uuid4())
    stored_path = storage.save(current_user.id, file_id, file_content, ext)
    
    # Create recording in database
    recording = Recording(
        user_id=current_user.id,
        original_filename=file.filename,
        stored_path=stored_path,
        file_size_bytes=len(file_content),
        mime_type=file.content_type or "audio/unknown",
        sha256=sha256,
        duration_sec=duration,
        sample_rate=sample_rate,
        site_id=site_id,
        hour=hour,
        lat=lat,
        lng=lng,
        status="queued",
    )
    
    db.add(recording)
    db.commit()
    db.refresh(recording)
    
    # Start background inference task
    if background_tasks:
        background_tasks.add_task(
            process_inference_background,
            recording.id,
            stored_path,
            site_id,
            hour,
        )
    
    return {
        "id": recording.id,
        "status": recording.status,
        "message": "Upload successful. Inference queued.",
    }


@router.get("/{recording_id}/status")
async def get_recording_status(
    recording_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get recording processing status."""
    
    recording = db.query(Recording).filter(
        Recording.id == recording_id,
        Recording.user_id == current_user.id,
    ).first()
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    return {
        "id": recording.id,
        "status": recording.status,
        "progress_stage": recording.progress_stage,
        "error_message": recording.error_message,
    }


@router.get("/{recording_id}")
async def get_recording(
    recording_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get recording details including prediction results."""
    
    recording = db.query(Recording).filter(
        Recording.id == recording_id,
        Recording.user_id == current_user.id,
    ).first()
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    # Build response
    response = {
        "id": recording.id,
        "original_filename": recording.original_filename,
        "duration_sec": recording.duration_sec,
        "sample_rate": recording.sample_rate,
        "site_id": recording.site_id,
        "hour": recording.hour,
        "lat": recording.lat,
        "lng": recording.lng,
        "status": recording.status,
        "created_at": recording.created_at.isoformat(),
    }
    
    # Add prediction if available
    if recording.prediction:
        response["prediction"] = recording.prediction.result_json
        response["detections"] = [
            {
                "species_code": d.species_code,
                "species_name": d.species_name,
                "taxon": d.taxon,
                "max_score": d.max_score,
                "windows_detected": d.windows_detected,
            }
            for d in recording.detections
        ]
    
    return response


@router.get("")
async def list_recordings(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    q: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List user's recordings with pagination and filtering.
    
    Query params:
    - page: page number (1-indexed)
    - page_size: items per page (1-50, default 10)
    - q: search in original_filename and species names
    - status: filter by status (queued, processing, done, failed)
    - date_from, date_to: filter by date range (ISO format)
    """
    
    query = db.query(Recording).filter(Recording.user_id == current_user.id)
    
    # Search filter
    if q:
        query = query.filter(
            or_(
                Recording.original_filename.ilike(f"%{q}%"),
                Recording.detections.any(Detection.species_name.ilike(f"%{q}%")),
            )
        )
    
    # Status filter
    if status:
        query = query.filter(Recording.status == status)
    
    # Date range filter
    if date_from:
        try:
            dt = datetime.fromisoformat(date_from)
            query = query.filter(Recording.created_at >= dt)
        except:
            pass
    
    if date_to:
        try:
            dt = datetime.fromisoformat(date_to)
            query = query.filter(Recording.created_at <= dt)
        except:
            pass
    
    # Get total count
    total = query.count()
    
    # Order and paginate
    offset = (page - 1) * page_size
    recordings = query.order_by(
        desc(Recording.created_at)
    ).offset(offset).limit(page_size).all()
    
    # Build items with top 3 species
    items = []
    for r in recordings:
        top_species = []
        if r.detections:
            # Sort by max_score descending, take top 3
            sorted_detections = sorted(r.detections, key=lambda x: x.max_score, reverse=True)[:3]
            top_species = [
                {"name": d.species_name, "code": d.species_code, "score": d.max_score}
                for d in sorted_detections
            ]
        
        items.append({
            "id": r.id,
            "original_filename": r.original_filename,
            "created_at": r.created_at.isoformat(),
            "duration_sec": r.duration_sec,
            "site_id": r.site_id,
            "hour": r.hour,
            "status": r.status,
            "progress_stage": r.progress_stage,
            "top_species": top_species,
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.delete("/{recording_id}")
async def delete_recording(
    recording_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a recording and its associated data."""
    
    recording = db.query(Recording).filter(
        Recording.id == recording_id,
        Recording.user_id == current_user.id,
    ).first()
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    stored_path = recording.stored_path
    
    # Delete from database (cascades to prediction, detections)
    db.delete(recording)
    db.commit()
    
    # Delete audio file from disk
    try:
        full_path = storage.open_path(stored_path)
        if full_path.exists():
            full_path.unlink()
    except:
        pass  # Ignore file not found
    
    return {"message": "Recording deleted successfully"}


@router.get("/{recording_id}/audio")
async def get_audio(
    recording_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get audio file with HTTP range request support.
    
    Usage in browser:
    <audio controls src="/recordings/{id}/audio?token={signed_token}"></audio>
    """
    
    recording = db.query(Recording).filter(
        Recording.id == recording_id,
        Recording.user_id == current_user.id,
    ).first()
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    full_path = storage.open_path(recording.stored_path)
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    # Determine media type
    media_type = recording.mime_type or "audio/wav"
    
    return FileResponse(
        full_path,
        media_type=media_type,
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=3600",
        },
    )


@router.get("/{recording_id}/spectrogram")
async def get_spectrogram(
    recording_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get mel spectrogram as PNG.
    Cached on disk for performance.
    """
    import librosa
    import librosa.display
    import matplotlib.pyplot as plt
    import io
    
    recording = db.query(Recording).filter(
        Recording.id == recording_id,
        Recording.user_id == current_user.id,
    ).first()
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    # Check if spectrogram already cached
    full_path = storage.open_path(recording.stored_path)
    spec_path = full_path.parent / f"{full_path.stem}_spectrogram.png"
    
    if spec_path.exists():
        return FileResponse(spec_path, media_type="image/png")
    
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    try:
        # Load audio
        y, sr = librosa.load(str(full_path), sr=None)
        
        # Compute mel spectrogram
        S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=8000)
        S_db = librosa.power_to_db(S, ref=np.max)
        
        # Create plot
        plt.figure(figsize=(12, 4))
        librosa.display.specshow(S_db, sr=sr, x_axis='time', y_axis='mel', cmap='viridis')
        plt.colorbar(format='%+2.0f dB')
        plt.title('Mel Spectrogram')
        
        # Save to cache
        plt.savefig(spec_path, dpi=100, bbox_inches='tight')
        plt.close()
        
        return FileResponse(spec_path, media_type="image/png")
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate spectrogram: {str(e)}",
        )


@router.post("/{recording_id}/feedback")
async def post_feedback(
    recording_id: str,
    feedback_data: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Save user feedback on species detection.
    
    Request body:
    {
      "species_code": "amcro",
      "window_index": null (optional),
      "is_correct": true
    }
    """
    
    recording = db.query(Recording).filter(
        Recording.id == recording_id,
        Recording.user_id == current_user.id,
    ).first()
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    species_code = feedback_data.species_code
    window_index = feedback_data.window_index
    is_correct = feedback_data.is_correct
    
    # Upsert feedback
    existing = db.query(Feedback).filter(
        Feedback.recording_id == recording_id,
        Feedback.user_id == current_user.id,
        Feedback.species_code == species_code,
        Feedback.window_index == window_index,
    ).first()
    
    if existing:
        existing.is_correct = is_correct
    else:
        feedback = Feedback(
            recording_id=recording_id,
            user_id=current_user.id,
            species_code=species_code,
            window_index=window_index,
            is_correct=is_correct,
        )
        db.add(feedback)
    
    db.commit()
    
    return {
        "message": "Feedback saved",
        "species_code": species_code,
        "is_correct": is_correct,
    }


@router.get("/{recording_id}/feedback")
async def get_feedback(
    recording_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all feedback for a recording."""
    from ..db_models import Feedback
    
    recording = db.query(Recording).filter(
        Recording.id == recording_id,
        Recording.user_id == current_user.id,
    ).first()
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    feedback_records = db.query(Feedback).filter(
        Feedback.recording_id == recording_id,
        Feedback.user_id == current_user.id,
    ).all()
    
    return {
        "feedback": [
            {
                "species_code": f.species_code,
                "window_index": f.window_index,
                "is_correct": f.is_correct,
            }
            for f in feedback_records
        ]
    }
