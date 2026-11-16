# NEW process_inference_background function - to replace the old one
# This is a complete rewrite with proper error handling

def process_inference_background(
    recording_id: str,
    stored_path: str,
    site_id: int,
    hour: int,
):
    """
    Background task to run inference on a recording.
    Updates recording status and creates prediction results.
    Includes comprehensive error handling with proper rollbacks.
    """
    from ..db import SessionLocal
    from ..pipeline import predict_pipeline
    from ..utils import log_stage, log_performance_summary, clear_recording_timings
    from ..utils.serialize import to_jsonable, safe_str, safe_float, safe_int
    import time
    import logging
    
    logger = logging.getLogger("birdclef.background")
    logger.info(f"[BG_TASK_START] Recording {recording_id} - Starting background inference")
    
    db = SessionLocal()
    total_start = time.perf_counter()
    success = False
    result = None
    last_stage = ""
    
    try:
        with log_stage("Background Task Initialization", recording_id=recording_id):
            # Acquire semaphore
            logger.info(f"[BG_TASK] Recording {recording_id} - Acquiring semaphore...")
            acquired = _inference_semaphore.acquire(blocking=True, timeout=3600)
            if not acquired:
                logger.error(f"[BG_TASK_ERROR] Recording {recording_id} - Failed to acquire semaphore")
                raise RuntimeError("Could not acquire inference semaphore")
            logger.info(f"[BG_TASK] Recording {recording_id} - Semaphore acquired")
        
        try:
            with log_stage("Database Recording Load", recording_id=recording_id):
                logger.info(f"[BG_TASK] Recording {recording_id} - Loading from DB")
                recording = db.query(Recording).filter(Recording.id == recording_id).first()
                if not recording:
                    logger.error(f"[BG_TASK_ERROR] Recording {recording_id} - Not found in DB")
                    return
                
                recording.status = "processing"
                recording.progress_stage = "Loading audio"
                db.commit()
                last_stage = "Loading audio"
                logger.info(f"[BG_TASK] Recording {recording_id} - Status set to processing")
            
            with log_stage("File Path Resolution", recording_id=recording_id):
                logger.info(f"[BG_TASK] Recording {recording_id} - Resolving storage path")
                full_path = storage.open_path(stored_path)
            
            # Run pipeline with progress callback
            def progress_callback(stage: str):
                nonlocal last_stage
                last_stage = stage
                recording.progress_stage = stage
                try:
                    db.commit()
                except Exception as e:
                    logger.warning(f"[BG_TASK] Failed to update progress stage: {e}")
                    db.rollback()
            
            with log_stage("Audio Pipeline Execution", recording_id=recording_id):
                logger.info(f"[BG_TASK] Recording {recording_id} - Starting pipeline...")
                result = predict_pipeline(
                    audio_path=str(full_path),
                    site_id=site_id,
                    hour_id=hour,
                    progress_callback=progress_callback,
                    recording_id=recording_id,
                )
                logger.info(f"[BG_TASK] Recording {recording_id} - Pipeline complete")
            
            # Wrap persistence in its own try/except to isolate save failures
            try:
                with log_stage("Prediction Database Persistence", recording_id=recording_id):
                    logger.info(f"[BG_TASK] Recording {recording_id} - Sanitizing result dict...")
                    result = to_jsonable(result)
                    
                    logger.info(f"[BG_TASK] Recording {recording_id} - Creating Prediction object...")
                    prediction = Prediction(
                        recording_id=recording_id,
                        result_json=result,
                        top_species=result.get("top_species", []),
                    )
                    db.add(prediction)
                    
                    logger.info(f"[BG_TASK] Recording {recording_id} - Creating {len(result.get('top_species', []))} Detection records...")
                    for species_info in result.get("top_species", []):
                        detection = Detection(
                            recording_id=recording_id,
                            species_code=safe_str(species_info.get("code", ""), "Unknown")[:50],
                            species_name=safe_str(species_info.get("common_name") or species_info.get("code", ""), "Unknown"),
                            taxon=safe_str(species_info.get("taxon", ""), "Unknown"),
                            max_score=safe_float(species_info.get("max_score"), 0.0),
                            windows_detected=safe_int(species_info.get("windows_detected"), 0),
                        )
                        db.add(detection)
                    
                    db.flush()
                    logger.info(f"[BG_TASK] Recording {recording_id} - Persistence flush successful")
                    
                    # Mark as done AFTER all data is flushed
                    recording.status = "done"
                    recording.progress_stage = "Completed"
                    db.commit()
                    logger.info(f"[BG_TASK] Recording {recording_id} - Status saved to DB as DONE")
                    
                    success = True
            
            except Exception as persist_error:
                # Persistence failed
                logger.exception(f"[BG_TASK_PERSIST] Recording {recording_id} - Save failed: {type(persist_error).__name__}")
                db.rollback()
                
                # Try to mark as failed in current session
                try:
                    recording = db.query(Recording).filter(Recording.id == recording_id).first()
                    if recording:
                        recording.status = "failed"
                        recording.progress_stage = last_stage
                        recording.error_message = f"Save error: {type(persist_error).__name__}: {str(persist_error)[:400]}"
                        db.commit()
                        logger.error(f"[BG_TASK] Recording {recording_id} - Status set to FAILED: {recording.error_message[:80]}")
                except Exception as update_error:
                    logger.warning(f"[BG_TASK] Recording {recording_id} - Could not update status in current session: {update_error}")
                    # Try with new session
                    try:
                        new_db = SessionLocal()
                        rec = new_db.query(Recording).filter(Recording.id == recording_id).first()
                        if rec:
                            rec.status = "failed"
                            rec.progress_stage = last_stage
                            rec.error_message = f"Save error: {type(persist_error).__name__}: {str(persist_error)[:400]}"
                            new_db.commit()
                            logger.error(f"[BG_TASK] Recording {recording_id} - Updated via new session")
                        new_db.close()
                    except Exception as retry_error:
                        logger.exception(f"[BG_TASK] Recording {recording_id} - All attempts to mark failed failed: {retry_error}")
                
                raise
        
        finally:
            _inference_semaphore.release()
            logger.info(f"[BG_TASK] Recording {recording_id} - Semaphore released")
    
    except Exception as e:
        # General exception handler
        if not success:
            logger.exception(f"[BG_TASK_ERROR] Recording {recording_id} - Inference failed")
            db.rollback()
            
            # Try to update status
            try:
                recording = db.query(Recording).filter(Recording.id == recording_id).first()
                if recording:
                    recording.status = "failed"
                    recording.progress_stage = last_stage
                    recording.error_message = f"{type(e).__name__}: {str(e)[:400]}"
                    db.commit()
                    logger.error(f"[BG_TASK] Recording {recording_id} - Failed status: {recording.error_message[:80]}")
            except Exception as update_error:
                logger.warning(f"[BG_TASK] Recording {recording_id} - Could not update to failed: {update_error}")
                try:
                    final_db = SessionLocal()
                    rec = final_db.query(Recording).filter(Recording.id == recording_id).first()
                    if rec:
                        rec.status = "failed"
                        rec.progress_stage = last_stage
                        rec.error_message = f"{type(e).__name__}: {str(e)[:400]}"
                        final_db.commit()
                    final_db.close()
                except:
                    logger.exception(f"[BG_TASK] Recording {recording_id} - Final status update also failed")
    
    finally:
        total_duration = time.perf_counter() - total_start
        num_windows = result.get("valid_windows", 0) if result else 0
        num_predictions = len(result.get("top_species", [])) if result else 0
        
        logger.info(f"[BG_TASK_END] Recording {recording_id} - Success={success}, Duration={total_duration:.2f}s, Windows={num_windows}, Predictions={num_predictions}")
        
        log_performance_summary(
            recording_id=recording_id,
            total_duration=total_duration,
            num_windows=num_windows,
            num_predictions=num_predictions,
            success=success,
        )
        
        clear_recording_timings(recording_id)
        db.close()
