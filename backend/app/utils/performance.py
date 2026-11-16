
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
print("[DEBUG] Initializing BirdCLEF performance logger module...")

_perf_logger = None
_stage_timings = local()  # Thread-local storage for nested stage tracking
_recording_timings = {}  # Global dict mapping recording_id -> {stage_name -> duration}
_recording_lock = __import__('threading').Lock()

print("[DEBUG] Performance logger module initialized successfully.")


def get_perf_logger():
    """Get or create the performance logger."""
    global _perf_logger

    print("[DEBUG] get_perf_logger() called.")

    if _perf_logger is not None:
        print("[DEBUG] Existing performance logger found. Reusing it.")
        return _perf_logger

    print("[DEBUG] Creating new performance logger...")
    _perf_logger = logging.getLogger("birdclef.performance")

    # Only add handler if not already present (avoid duplicates)
    if not _perf_logger.handlers:
        print("[DEBUG] No existing handlers found. Adding StreamHandler.")

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(levelname)s] [%(name)s] %(message)s"
        )
        handler.setFormatter(formatter)
        _perf_logger.addHandler(handler)
        _perf_logger.setLevel(logging.INFO)

        print("[DEBUG] Performance logger handler configured successfully.")
    else:
        print("[DEBUG] Logger already has handlers. Skipping handler creation.")

    print("[SUCCESS] Performance logger ready.")
    return _perf_logger


def _get_stage_stack():
    """Get the thread-local stack of nested stages."""

    print("[DEBUG] Retrieving thread-local stage stack.")

    if not hasattr(_stage_timings, 'stack'):
        print("[DEBUG] Stage stack not found. Initializing new stack.")
        _stage_timings.stack = []
        _stage_timings.start_times = {}

    print(f"[DEBUG] Current nested stage count: {len(_stage_timings.stack)}")
    return _stage_timings.stack


def _get_start_times():
    """Get the thread-local start times dict."""

    print("[DEBUG] Retrieving thread-local stage start times.")

    if not hasattr(_stage_timings, 'start_times'):
        print("[DEBUG] Start times not found. Initializing.")
        _stage_timings.stack = []
        _stage_timings.start_times = {}

    print(f"[DEBUG] Active stage timers: {len(_stage_timings.start_times)}")
    return _stage_timings.start_times


@contextmanager
def log_stage(
    stage_name: str,
    recording_id: Optional[str] = None,
):
    """
    Context manager for measuring and logging stage performance.
    """

    print("\n[DEBUG] ==========================================")
    print(f"[DEBUG] log_stage() invoked")
    print(f"[DEBUG] Stage name: {stage_name}")
    print(f"[DEBUG] Recording ID: {recording_id}")
    print("[DEBUG] ==========================================")

    logger = get_perf_logger()
    stack = _get_stage_stack()
    start_times = _get_start_times()

    print(f"[DEBUG] Current stage stack: {stack}")

    # Construct unique stage identifier for nested tracking
    stage_id = f"{len(stack)}:{stage_name}"

    print(f"[DEBUG] Generated stage ID: {stage_id}")

    # Log start
    rec_context = f" | recording_id={recording_id}" if recording_id else ""
    indent = "  " * len(stack)

    logger.info(
        f"{indent}[PERF] START | stage={stage_name}{rec_context}"
    )

    print(f"[INFO] Starting performance measurement: {stage_name}")

    if recording_id:
        print(f"[DEBUG] Associating stage with recording: {recording_id}")

    stack.append(stage_name)
    start_times[stage_id] = time.perf_counter()

    print(f"[DEBUG] Stage pushed to stack: {stack}")
    print(f"[DEBUG] Timer started for {stage_id}")

    result = {
        'duration': 0.0,
        'success': False,
        'exception': None,
    }

    print("[DEBUG] Initial stage result dictionary created.")

    try:
        print(f"[DEBUG] Yielding control to stage: {stage_name}")

        yield result

        result['success'] = True

        print(f"[SUCCESS] Stage completed successfully: {stage_name}")

    except Exception as e:
        result['exception'] = e
        result['success'] = False

        print(f"[ERROR] Exception occurred in stage: {stage_name}")
        print(f"[ERROR] Exception type: {type(e).__name__}")
        print(f"[ERROR] Exception message: {str(e)}")
        print("[DEBUG] Capturing exception for performance logging.")

        raise

    finally:
        print(f"[DEBUG] Executing finally block for stage: {stage_name}")

        # Calculate duration
        end_time = time.perf_counter()
        start_time = start_times.pop(stage_id, start_time := end_time)
        duration = end_time - start_time
        result['duration'] = duration

        print(f"[DEBUG] Stage end timestamp: {end_time}")
        print(f"[DEBUG] Stage start timestamp: {start_time}")
        print(f"[DEBUG] Calculated duration: {duration:.4f}s")

        # Pop from stack
        stack.pop()

        print(f"[DEBUG] Stage removed from stack.")
        print(f"[DEBUG] Remaining stage stack: {stack}")

        indent = "  " * len(stack)

        # Log end
        if result['success']:

            print(f"[SUCCESS] Finalizing successful stage: {stage_name}")

            logger.info(
                f"{indent}[PERF] END | stage={stage_name} | "
                f"duration={duration:.3f}s{rec_context}"
            )

            # Track timing for recording
            if recording_id:
                print(f"[DEBUG] Recording timing for recording ID: {recording_id}")

                with _recording_lock:

                    if recording_id not in _recording_timings:
                        print("[DEBUG] Creating new recording timing entry.")
                        _recording_timings[recording_id] = {}

                    _recording_timings[recording_id][stage_name] = duration

                    print(
                        f"[DEBUG] Timing stored: "
                        f"{stage_name} = {duration:.4f}s"
                    )

                    print(
                        f"[DEBUG] Total tracked stages for recording: "
                        f"{len(_recording_timings[recording_id])}"
                    )

            print(f"[SUCCESS] Stage logging completed: {stage_name}")

        else:
            exc = result['exception']

            print(f"[ERROR] Stage failed: {stage_name}")
            print(f"[ERROR] Failed after {duration:.4f}s")
            print(f"[DEBUG] Exception details: {exc}")

            logger.error(
                f"{indent}[PERF] FAILED | stage={stage_name} | "
                f"duration={duration:.3f}s{rec_context}\n"
                f"{traceback.format_exc()}"
            )

            print("[DEBUG] Failure details logged successfully.")

        print(f"[DEBUG] log_stage() finished for: {stage_name}")
        print("[DEBUG] ==========================================\n")


def get_recording_timings(recording_id: str) -> Dict[str, float]:
    """
    Get all recorded stage timings for a recording.
    """

    print(f"[DEBUG] get_recording_timings() called for: {recording_id}")

    with _recording_lock:

        timings = _recording_timings.get(recording_id, {}).copy()

        print(f"[DEBUG] Retrieved timings: {timings}")
        print(f"[DEBUG] Number of recorded stages: {len(timings)}")

        return timings


def clear_recording_timings(recording_id: str):
    """Clear recorded timings for a recording."""

    print(f"[DEBUG] clear_recording_timings() called for: {recording_id}")

    with _recording_lock:

        existed = recording_id in _recording_timings

        _recording_timings.pop(recording_id, None)

        if existed:
            print(f"[SUCCESS] Cleared timings for recording: {recording_id}")
        else:
            print(f"[WARNING] No timing data found for: {recording_id}")


def log_performance_summary(
    recording_id: str,
    total_duration: float,
    num_windows: int = 0,
    num_predictions: int = 0,
    success: bool = True,
):
    """
    Log a comprehensive performance summary for a recording.
    """

    print("\n[DEBUG] ==========================================")
    print("[DEBUG] log_performance_summary() called")
    print(f"[DEBUG] Recording ID: {recording_id}")
    print(f"[DEBUG] Total duration: {total_duration:.4f}s")
    print(f"[DEBUG] Number of windows: {num_windows}")
    print(f"[DEBUG] Number of predictions: {num_predictions}")
    print(f"[DEBUG] Processing success: {success}")
    print("[DEBUG] ==========================================")

    logger = get_perf_logger()

    print("[DEBUG] Fetching recording stage timings...")

    timings = get_recording_timings(recording_id)

    print(f"[DEBUG] Retrieved {len(timings)} stage timings.")

    if not timings:

        print("[WARNING] No stage timings recorded for this recording.")

        # No timings recorded
        logger.info(
            f"\n{'='*60}\n"
            f"PERFORMANCE SUMMARY: {recording_id}\n"
            f"Total Duration: {total_duration:.2f}s\n"
            f"Status: {'SUCCESS' if success else 'FAILED'}\n"
            f"{'='*60}\n"
        )

        print("[DEBUG] Basic performance summary logged.")
        return

    # Calculate percentages
    print("[DEBUG] Calculating stage duration percentages...")

    stage_percentages = {}

    for stage, duration in timings.items():

        pct = (duration / total_duration * 100) if total_duration > 0 else 0

        stage_percentages[stage] = pct

        print(
            f"[DEBUG] Stage: {stage} | "
            f"Duration: {duration:.4f}s | "
            f"Percentage: {pct:.2f}%"
        )

    # Find slowest stage
    print("[DEBUG] Identifying slowest processing stage...")

    slowest_stage = max(timings.items(), key=lambda x: x[1])

    print(
        f"[DEBUG] Slowest stage: {slowest_stage[0]} "
        f"({slowest_stage[1]:.4f}s)"
    )

    # Build summary lines
    print("[DEBUG] Building performance summary...")

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

        print(
            f"[DEBUG] Adding stage to summary: {stage} "
            f"({duration:.4f}s, {pct:.2f}%)"
        )

        summary_lines.append(
            f"  {stage:.<40} {duration:>7.3f}s ({pct:>5.1f}%)"
        )

    summary_lines.extend([
        "",
        f"Slowest Stage: {slowest_stage[0]} ({slowest_stage[1]:.2f}s)",
        "="*60,
    ])

    # Log summary
    print("[DEBUG] Joining performance summary lines...")

    summary_text = "\n".join(summary_lines)

    logger.info(summary_text)

    print("[SUCCESS] Performance summary logged successfully.")
    print("[DEBUG] log_performance_summary() execution completed.")
    print("[DEBUG] ==========================================\n")
