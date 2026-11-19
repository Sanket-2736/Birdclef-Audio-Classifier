"""
Log-Mel Spectrogram API endpoints.

Completely independent router for accessing generated spectrogram artifacts,
acoustic metadata, and species-acoustic associations. Does not modify existing
endpoints or responses.
"""

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path as PathParam
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ..db_models import User, Recording
from ..routers.auth import get_current_user
from ..logmel_spectrogram import ARTIFACTS_DIR


print("[DEBUG] Initializing Log-Mel Spectrogram router...")

router = APIRouter(prefix="/recordings", tags=["logmel-spectrogram"])


# ============================================================
# HELPERS
# ============================================================

def get_user_recording(
    recording_id: str,
    current_user: User,
    db: Session,
) -> Recording:
    """Get recording and verify ownership."""
    recording = db.query(Recording).filter(
        Recording.id == recording_id,
        Recording.user_id == current_user.id,
    ).first()
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    return recording


def get_recording_artifact_dir(recording_id: str) -> Path:
    """Get recording artifact directory."""
    artifact_dir = ARTIFACTS_DIR / recording_id
    
    if not artifact_dir.exists():
        raise HTTPException(
            status_code=404,
            detail="Spectrogram artifacts not found. Generation may be pending.",
        )
    
    return artifact_dir


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/{recording_id}/logmel")
async def get_logmel_metadata(
    recording_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve log-mel spectrogram metadata and analysis results.
    
    Returns:
    - Recording ID and status
    - Audio properties (sample rate, duration, channels, etc.)
    - Spectral features (centroid, bandwidth, rolloff, flatness, ZCR, energy)
    - Mel features (mel-band energy distribution, statistics)
    - MFCC features (mean, std, deltas)
    - Per-window acoustic analysis (associated with detected species)
    - Paths to generated images
    
    This endpoint provides **temporal associations** between detected species
    and measured acoustic characteristics. These are NOT independently
    validated species signatures, but rather observations of what was heard
    during the same time interval as the detection.
    """
    
    # Verify recording ownership
    recording = get_user_recording(recording_id, current_user, db)
    
    # Get artifact directory
    artifact_dir = get_recording_artifact_dir(recording_id)
    
    # Load metadata JSON
    metadata_path = artifact_dir / "metadata.json"
    
    if not metadata_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Spectrogram metadata not found",
        )
    
    try:
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read metadata: {str(e)[:100]}",
        )
    
    # Build response with image URLs
    spectrogram_image_url = None
    if (artifact_dir / "spectrogram.png").exists():
        spectrogram_image_url = f"/recordings/{recording_id}/logmel/image"
    
    window_images_urls = []
    for i in range(12):
        window_file = artifact_dir / f"window_{i:02d}.png"
        if window_file.exists():
            window_images_urls.append({
                "window_index": i,
                "url": f"/recordings/{recording_id}/logmel/window/{i:02d}",
            })
    
    return {
        "recording_id": recording_id,
        "recording_duration_sec": recording.duration_sec,
        "spectrogram_image_url": spectrogram_image_url,
        "window_images": window_images_urls,
        "audio_properties": metadata.get("audio_properties", {}),
        "spectral_features": metadata.get("spectral_features", {}),
        "mel_features": metadata.get("mel_features", {}),
        "mfcc_features": metadata.get("mfcc_features", {}),
        "window_analysis": metadata.get("window_analysis", []),
        "configuration": metadata.get("configuration", {}),
        "note": "Acoustic features shown are temporal associations with detected species, not independently validated signatures",
    }


@router.get("/{recording_id}/logmel/image")
async def get_logmel_image(
    recording_id: str,
    token: Optional[str] = Query(None),
    authorization: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve full-recording log-mel spectrogram PNG image.
    
    Returns PNG image with:
    - X-axis: Time in seconds
    - Y-axis: Mel frequency in Hz (log scale)
    - Color: Relative log-power intensity in dB
    - Colorbar: Power scale in dB
    
    Accepts token as query parameter for browser display:
    GET /recordings/{id}/logmel/image?token={jwt_token}
    """
    
    # Verify recording ownership
    get_user_recording(recording_id, current_user, db)
    
    # Get artifact directory
    artifact_dir = get_recording_artifact_dir(recording_id)
    
    # Get spectrogram image
    spec_path = artifact_dir / "spectrogram.png"
    
    if not spec_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Spectrogram image not found",
        )
    
    return FileResponse(
        spec_path,
        media_type="image/png",
        headers={
            "Cache-Control": "public, max-age=86400",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/{recording_id}/logmel/window/{window_index}")
async def get_window_logmel_image(
    recording_id: str,
    window_index: int = PathParam(..., ge=0, le=11),
    token: Optional[str] = Query(None),
    authorization: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve per-window log-mel spectrogram PNG image.
    
    Parameters:
    - window_index: Window number (0-11, representing 5-second intervals)
    - token: Optional JWT token as query parameter for browser display
    
    Returns PNG image for the specified 5-second window.
    """
    
    # Verify recording ownership
    get_user_recording(recording_id, current_user, db)
    
    # Get artifact directory
    artifact_dir = get_recording_artifact_dir(recording_id)
    
    # Get window image
    window_path = artifact_dir / f"window_{window_index:02d}.png"
    
    if not window_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Window {window_index} spectrogram image not found",
        )
    
    return FileResponse(
        window_path,
        media_type="image/png",
        headers={
            "Cache-Control": "public, max-age=86400",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.post("/{recording_id}/logmel/generate")
async def regenerate_logmel_spectrogram(
    recording_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Manually regenerate log-mel spectrogram for a recording.
    
    This endpoint allows re-generation of spectrogram artifacts without
    re-running the inference pipeline. Useful if artifacts were deleted
    or need to be regenerated.
    
    Returns immediately (202 Accepted) and regenerates in background.
    
    **Important:** Regeneration does not affect existing prediction results.
    Only spectrogram artifacts are regenerated.
    """
    
    from ..logmel_spectrogram import generate_logmel_spectrogram
    from ..storage import get_storage
    import threading
    import logging
    
    logger = logging.getLogger("birdclef.logmel")
    
    # Verify recording ownership and exists
    recording = get_user_recording(recording_id, current_user, db)
    
    if recording.status == "queued" or recording.status == "processing":
        raise HTTPException(
            status_code=409,
            detail="Recording is currently processing. Cannot regenerate spectrogram.",
        )
    
    if recording.status == "failed":
        raise HTTPException(
            status_code=400,
            detail="Recording analysis failed. Cannot regenerate spectrogram.",
        )
    
    # Get audio file
    storage = get_storage()
    try:
        audio_path = storage.open_path(recording.stored_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Audio file not found. Cannot regenerate spectrogram.",
        )
    
    # Get prediction result if available
    prediction_result = None
    if recording.prediction:
        prediction_result = recording.prediction.result_json
    
    # Background task to regenerate
    def background_regenerate():
        try:
            logger.info(f"[LOGMEL_BG] Starting spectrogram regeneration for {recording_id}")
            
            result = generate_logmel_spectrogram(
                audio_path=audio_path,
                recording_id=recording_id,
                real_duration_sec=recording.duration_sec,
                prediction_result=prediction_result,
            )
            
            if result["status"] == "completed":
                logger.info(f"[LOGMEL_BG] Spectrogram regeneration successful for {recording_id}")
            else:
                logger.error(f"[LOGMEL_BG] Spectrogram regeneration failed for {recording_id}: {result.get('error_message')}")
        
        except Exception as e:
            logger.exception(f"[LOGMEL_BG] Unexpected error regenerating spectrogram for {recording_id}: {e}")
    
    # Start background thread
    thread = threading.Thread(target=background_regenerate, daemon=True)
    thread.start()
    
    return {
        "recording_id": recording_id,
        "status": "regeneration_queued",
        "message": "Spectrogram regeneration started. Check back in a few moments.",
    }


print("[SUCCESS] Log-Mel Spectrogram router loaded successfully")
