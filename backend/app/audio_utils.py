"""
Audio loading utilities that track real duration before padding.
Includes performance logging.
"""

from pathlib import Path
import numpy as np
import soundfile as sf
from .utils import log_stage


SR = 32_000
WINDOW_SEC = 5
FILE_SECONDS = 60
FILE_SAMPLES = FILE_SECONDS * SR


def load_audio_with_duration(audio_path, recording_id=None):
    """
    Load audio and return both padded array and real duration.
    Includes performance logging for each step.
    
    Parameters
    ----------
    audio_path : str or Path
        Path to audio file
    recording_id : str, optional
        Recording ID for logging context
    
    Returns
    -------
    audio : np.ndarray
        Padded/truncated audio of shape (1920000,) for 60 seconds at 32 kHz
    real_duration_sec : float
        Actual duration of the loaded audio before padding/truncation
    """
    
    with log_stage("Audio File Read", recording_id=recording_id):
        audio, sr = sf.read(
            audio_path,
            dtype="float32"
        )
    
    with log_stage("Audio Format Validation", recording_id=recording_id):
        if sr != SR:
            raise ValueError(
                f"Expected {SR} Hz audio, "
                f"but received {sr} Hz"
            )
    
    with log_stage("Audio Channel Conversion", recording_id=recording_id):
        # Stereo → mono
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
    
    with log_stage("Audio Duration Calculation", recording_id=recording_id):
        # Calculate real duration in seconds
        real_duration_sec = len(audio) / SR
    
    with log_stage("Audio Padding/Truncation", recording_id=recording_id):
        # Pad or truncate to exactly 60 seconds
        if len(audio) < FILE_SAMPLES:
            audio = np.pad(
                audio,
                (0, FILE_SAMPLES - len(audio))
            )
        else:
            audio = audio[:FILE_SAMPLES]
    
    return audio.astype(np.float32), real_duration_sec


def compute_valid_windows(real_duration_sec, recording_id=None):
    """
    Compute number of valid (non-padding) windows.
    
    Parameters
    ----------
    real_duration_sec : float
        Real duration of audio in seconds
    recording_id : str, optional
        Recording ID for logging context
    
    Returns
    -------
    valid_windows : int
        Number of windows with real audio content (0-12)
    """
    import math
    
    with log_stage("Valid Windows Computation", recording_id=recording_id):
        valid_windows = min(
            math.ceil(real_duration_sec / WINDOW_SEC),
            12
        )
    
    return valid_windows


def get_waveform_peaks(audio, n_buckets=1000, recording_id=None):
    """
    Compute normalized max-abs amplitude per bucket.
    Includes performance logging.
    
    Parameters
    ----------
    audio : np.ndarray
        Audio waveform (float32)
    n_buckets : int
        Number of buckets to divide audio into
    recording_id : str, optional
        Recording ID for logging context
    
    Returns
    -------
    peaks : np.ndarray
        Normalized peaks [0..1] of shape (n_buckets,)
    """
    
    with log_stage("Waveform Peaks Computation", recording_id=recording_id):
        audio = np.asarray(audio, dtype=np.float32)
        
        bucket_size = len(audio) // n_buckets
        peaks = []
        
        for i in range(n_buckets):
            start = i * bucket_size
            end = start + bucket_size
            bucket = audio[start:end]
            
            if len(bucket) > 0:
                peak = np.max(np.abs(bucket))
            else:
                peak = 0.0
            
            peaks.append(float(peak))
        
        peaks = np.array(peaks, dtype=np.float32)
        max_peak = np.max(peaks) if peaks.max() > 0 else 1.0
        peaks = peaks / (max_peak + 1e-7)
    
    return np.clip(peaks, 0.0, 1.0).tolist()
