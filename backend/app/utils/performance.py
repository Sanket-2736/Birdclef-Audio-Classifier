"""
Centralized performance logging for the BirdCLEF pipeline.

Provides context manager for measuring and logging stage durations.
Supports nested stages and concurrent recording processing.
"""

import time
import logging
import traceback
from contextlib import contextmanager
from typing import Optional, Dict
from collections import defaultdict
from threading import local


# Set up performance logger
_perf_logger = None
_stage_timings = local()  # Thread-local storage for nested stage tracking
_recording_timings = {}  # Global dict mapping recording_id -> {stage_name -> duration}
_recording_lock = __import__('threading').Lock()


def get_perf_logger():
    """Get or create the performance logger."""
    global _perf_logger
    
    if _perf_logger is not None:
        return _perf_logger
    
    _perf_logger = logging.getLogger("birdclef.performance")
    
    # Only add handler if not already present (avoid duplicates)
    if not _perf_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(levelname)s] [%(name)s] %(message)s"
        )
        handler.setFormatter(formatter)
        _perf_logger.addHandler(handler)
        _perf_logger.setLevel(logging.INFO)
    
    return _perf_logger


def _get_stage_stack():
    """Get the thread-local stack of nested stages."""
    if not hasattr(_stage_timings, 'stack'):
        _stage_timings.stack = []
        _stage_timings.start_times = {}
    return _stage_timings.stack


def _get_start_times():
    """Get the thread-local start times dict."""
    if not hasattr(_stage_timings, 'start_times'):
        _stage_timings.stack = []
        _stage_timings.start_times = {}
    return _stage_timings.start_times


@contextmanager
def log_stage(
    stage_name: str,
    recording_id: Optional[str] = None,
):
    """
    Context manager for measuring and logging stage performance.
    
    Logs stage start, duration, and any exceptions.
    Supports nested stages and concurrent processing.
    
    Parameters
    ----------
    stage_name : str
        Name of the stage being measured
    recording_id : str, optional
        Recording ID for context (included in logs)
    
    Yields
    ------
    dict
        Dictionary with keys:
        - duration: elapsed time in seconds
        - success: whether the stage completed without exception
        - exception: exception object if one occurred
    
    Example
    -------
    with log_stage("Audio Preprocessing", recording_id=rec_id) as result:
        # do work
        pass
    
    if result['success']:
        print(f"Completed in {result['duration']:.2f}s")
    """
    
    logger = get_perf_logger()
    stack = _get_stage_stack()
    start_times = _get_start_times()
    
    # Construct unique stage identifier for nested tracking
    stage_id = f"{len(stack)}:{stage_name}"
    
    # Log start
    rec_context = f" | recording_id={recording_id}" if recording_id else ""
    indent = "  " * len(stack)
    logger.info(
        f"{indent}[PERF] START | stage={stage_name}{rec_context}"
    )
    
    stack.append(stage_name)
    start_times[stage_id] = time.perf_counter()
    
    result = {
        'duration': 0.0,
        'success': False,
        'exception': None,
    }
    
    try:
        yield result
        result['success'] = True
        
    except Exception as e:
        result['exception'] = e
        result['success'] = False
        
    finally:
        # Calculate duration
        end_time = time.perf_counter()
        start_time = start_times.pop(stage_id, start_time := end_time)
        duration = end_time - start_time
        result['duration'] = duration
        
        # Pop from stack
        stack.pop()
        indent = "  " * len(stack)
        
        # Log end
        if result['success']:
            logger.info(
                f"{indent}[PERF] END | stage={stage_name} | "
                f"duration={duration:.3f}s{rec_context}"
            )
            
            # Track timing for recording
            if recording_id:
                with _recording_lock:
                    if recording_id not in _recording_timings:
                        _recording_timings[recording_id] = {}
                    _recording_timings[recording_id][stage_name] = duration
        
        else:
            exc = result['exception']
            logger.error(
                f"{indent}[PERF] FAILED | stage={stage_name} | "
                f"duration={duration:.3f}s{rec_context}\n"
                f"{traceback.format_exc()}"
            )


def get_recording_timings(recording_id: str) -> Dict[str, float]:
    """
    Get all recorded stage timings for a recording.
    
    Parameters
    ----------
    recording_id : str
        Recording ID
    
    Returns
    -------
    dict
        Mapping of stage_name -> duration in seconds
    """
    with _recording_lock:
        return _recording_timings.get(recording_id, {}).copy()


def clear_recording_timings(recording_id: str):
    """Clear recorded timings for a recording."""
    with _recording_lock:
        _recording_timings.pop(recording_id, None)


def log_performance_summary(
    recording_id: str,
    total_duration: float,
    num_windows: int = 0,
    num_predictions: int = 0,
    success: bool = True,
):
    """
    Log a comprehensive performance summary for a recording.
    
    Parameters
    ----------
    recording_id : str
        Recording ID
    total_duration : float
        Total processing duration in seconds
    num_windows : int, optional
        Number of audio windows processed
    num_predictions : int, optional
        Number of predictions generated
    success : bool
        Whether processing was successful
    """
    
    logger = get_perf_logger()
    timings = get_recording_timings(recording_id)
    
    if not timings:
        # No timings recorded
        logger.info(
            f"\n{'='*60}\n"
            f"PERFORMANCE SUMMARY: {recording_id}\n"
            f"Total Duration: {total_duration:.2f}s\n"
            f"Status: {'SUCCESS' if success else 'FAILED'}\n"
            f"{'='*60}\n"
        )
        return
    
    # Calculate percentages
    stage_percentages = {}
    for stage, duration in timings.items():
        pct = (duration / total_duration * 100) if total_duration > 0 else 0
        stage_percentages[stage] = pct
    
    # Find slowest stage
    slowest_stage = max(timings.items(), key=lambda x: x[1])
    
    # Build summary lines
    summary_lines = [
        "\n" + "="*60,
        "PERFORMANCE SUMMARY",
        "="*60,
        f"Recording ID: {recording_id}",
        f"Total Duration: {total_duration:.2f}s",
        f"Windows: {num_windows}",
        f"Predictions: {num_predictions}",
        f"Status: {'SUCCESS' if success else 'FAILED'}",
        "",
    ]
    
    # Add individual stage timings
    summary_lines.append("Stage Timings:")
    for stage in sorted(timings.keys(), key=lambda s: timings[s], reverse=True):
        duration = timings[stage]
        pct = stage_percentages[stage]
        summary_lines.append(
            f"  {stage:.<40} {duration:>7.3f}s ({pct:>5.1f}%)"
        )
    
    summary_lines.extend([
        "",
        f"Slowest Stage: {slowest_stage[0]} ({slowest_stage[1]:.2f}s)",
        "="*60,
    ])
    
    # Log summary
    summary_text = "\n".join(summary_lines)
    logger.info(summary_text)
