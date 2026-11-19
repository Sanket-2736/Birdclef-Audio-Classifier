#!/usr/bin/env python
"""
Debug script to reproduce the save failure.
Runs predict_pipeline on an audio file and attempts to persist results exactly as
process_inference_background does, printing full tracebacks.

Usage:
  python debug_save.py /path/to/audio.ogg
"""

import sys
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

# Add parent to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

from app.db import SessionLocal
from app.db_models import Recording, Prediction, Detection, User
from app.pipeline import predict_pipeline
from app.species_mapping import get_species_info
from app.taxonomy import get_taxon
from datetime import datetime
from uuid import uuid4


def main():
    if len(sys.argv) < 2:
        print("Usage: python debug_save.py /path/to/audio.ogg [site_id] [hour]")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    site_id = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    hour = int(sys.argv[3]) if len(sys.argv) > 3 else 12
    
    if not Path(audio_path).exists():
        print(f"ERROR: Audio file not found: {audio_path}")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print("DEBUG: Running predict_pipeline...")
    print(f"{'='*60}")
    
    # Create a fake recording so we have an ID for the pipeline
    recording_id = str(uuid4())
    print(f"Recording ID: {recording_id}")
    print(f"Audio: {audio_path}")
    print(f"Site: {site_id}, Hour: {hour}\n")
    
    try:
        # Run pipeline with progress callback
        stages = []
        def progress_callback(stage):
            stages.append(stage)
            logger.info(f"[PIPELINE] {stage}")
        
        result = predict_pipeline(
            audio_path=audio_path,
            site_id=site_id,
            hour_id=hour,
            progress_callback=progress_callback,
            recording_id=recording_id,
        )
        
        logger.info(f"\n[PIPELINE] Completed with {len(stages)} stages")
        logger.info(f"[PIPELINE] Result keys: {list(result.keys())}")
        logger.info(f"[PIPELINE] Top species: {len(result.get('top_species', []))}")
        
    except Exception as e:
        logger.exception(f"[PIPELINE_ERROR] Failed to run pipeline")
        print(f"\nPipeline failed: {e}\n")
        return
    
    # Now try to save exactly as process_inference_background does
    print(f"\n{'='*60}")
    print("DEBUG: Creating test recording in database...")
    print(f"{'='*60}\n")
    
    db = SessionLocal()
    
    try:
        # Get or create a test user
        test_user = db.query(User).filter(User.email == "debug@test.local").first()
        if not test_user:
            # Create a minimal user for testing
            test_user = User(
                id=str(uuid4()),
                name="Debug User",
                email="debug@test.local",
                password_hash="dummy",
            )
            db.add(test_user)
            db.commit()
            logger.info(f"[TEST] Created test user: {test_user.id}")
        else:
            logger.info(f"[TEST] Using existing test user: {test_user.id}")
        
        # Create a real recording first
        recording = Recording(
            id=recording_id,
            user_id=test_user.id,
            original_filename="test.ogg",
            stored_path="/tmp/test.ogg",
            file_size_bytes=100000,
            mime_type="audio/ogg",
            sha256="test-sha256",
            duration_sec=30.0,
            sample_rate=32000,
            site_id=site_id,
            hour=hour,
            status="processing",
            progress_stage="Blending results",
        )
        db.add(recording)
        db.commit()
        logger.info(f"[TEST] Recording created: {recording_id}")
        
        print(f"\n{'='*60}")
        print("DEBUG: Attempting to save pipeline results...")
        print(f"{'='*60}\n")
        
        # Try to create Prediction with result_json
        logger.info(f"[TEST] Creating Prediction with result_json...")
        prediction = Prediction(
            recording_id=recording_id,
            result_json=result,
            top_species=result.get("top_species", []),
        )
        
        logger.info(f"[TEST] Prediction object created, adding to session...")
        db.add(prediction)
        
        # Try to create Detection records
        logger.info(f"[TEST] Creating {len(result.get('top_species', []))} Detection records...")
        for i, species_info in enumerate(result.get("top_species", [])):
            detection = Detection(
                recording_id=recording_id,
                species_code=species_info.get("code", ""),
                species_name=species_info.get("common_name", ""),
                taxon=species_info.get("taxon", ""),
                max_score=float(species_info.get("max_score", 0.0)),
                windows_detected=int(species_info.get("windows_detected", 0)),
            )
            db.add(detection)
            if (i + 1) % 5 == 0 or i == 0:
                logger.info(f"  Added {i+1}/{len(result.get('top_species', []))} detections...")
        
        logger.info(f"[TEST] All {len(result.get('top_species', []))} Detection objects added, now flushing...")
        
        db.flush()  # This is where the error would happen
        logger.info(f"[TEST] Flush successful!")
        
        db.commit()
        logger.info(f"[TEST] Commit successful!")
        
    except Exception as e:
        logger.error(f"[TEST] Flush/commit failed, attempting rollback...")
        logger.exception(f"[TEST] Full traceback:")
        print(f"\n{'='*60}")
        print("ORIGINAL EXCEPTION:")
        print(f"{'='*60}")
        print(f"{type(e).__name__}: {e}\n")
        
    else:
        print(f"\n{'='*60}")
        print("[SUCCESS] SAVE TEST PASSED - Results persisted successfully!")
        print(f"{'='*60}\n")
        
    finally:
        db.rollback()
        db.close()


if __name__ == "__main__":
    main()
