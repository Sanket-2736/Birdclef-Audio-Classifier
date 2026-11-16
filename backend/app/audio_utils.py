
"""
Audio loading utilities that track real duration before padding.
Includes performance logging.
"""

from pathlib import Path
import numpy as np
import soundfile as sf
from .utils import log_stage


print("[DEBUG] Initializing audio utilities...")

SR = 32_000
WINDOW_SEC = 5
FILE_SECONDS = 60
FILE_SAMPLES = FILE_SECONDS * SR

print(f"[DEBUG] Sample Rate: {SR} Hz")
print(f"[DEBUG] Window Duration: {WINDOW_SEC} seconds")
print(f"[DEBUG] File Duration: {FILE_SECONDS} seconds")
print(f"[DEBUG] Expected File Samples: {FILE_SAMPLES}")


def load_audio_with_duration(audio_path, recording_id=None):
    """
    Load audio and return both padded array and real duration.
    Includes performance logging for each step.
    """

    print("\n[DEBUG] ==========================================")
    print("[DEBUG] load_audio_with_duration() called")
    print(f"[DEBUG] Audio Path: {audio_path}")
    print(f"[DEBUG] Recording ID: {recording_id}")
    print("[DEBUG] ==========================================")

    # Audio file reading
    print("[DEBUG] Starting audio file reading...")

    with log_stage("Audio File Read", recording_id=recording_id):
        print(f"[DEBUG] Reading audio file: {audio_path}")

        audio, sr = sf.read(
            audio_path,
            dtype="float32"
        )

        print("[SUCCESS] Audio file read successfully.")
        print(f"[DEBUG] Loaded Audio Shape: {audio.shape}")
        print(f"[DEBUG] Loaded Audio Dtype: {audio.dtype}")
        print(f"[DEBUG] Original Sample Rate: {sr}")

        if audio.ndim > 1:
            print(f"[DEBUG] Audio has {audio.shape[1]} channels.")
        else:
            print("[DEBUG] Audio is mono.")

    # Sample rate validation
    print("\n[DEBUG] Starting audio format validation...")

    with log_stage("Audio Format Validation", recording_id=recording_id):

        print(f"[DEBUG] Expected Sample Rate: {SR}")
        print(f"[DEBUG] Received Sample Rate: {sr}")

        if sr != SR:
            print("[ERROR] Sample rate mismatch!")
            print(f"[ERROR] Expected: {SR}, Received: {sr}")

            raise ValueError(
                f"Expected {SR} Hz audio, "
                f"but received {sr} Hz"
            )

        print("[SUCCESS] Audio sample rate validation passed.")

    # Channel conversion
    print("\n[DEBUG] Starting audio channel conversion...")

    with log_stage("Audio Channel Conversion", recording_id=recording_id):

        # Stereo → mono
        if audio.ndim > 1:

            print("[DEBUG] Stereo/Multi-channel audio detected.")
            print(f"[DEBUG] Original Shape: {audio.shape}")
            print("[DEBUG] Converting audio to mono using mean(axis=1)...")

            audio = audio.mean(axis=1)

            print("[SUCCESS] Audio converted to mono.")
            print(f"[DEBUG] Updated Audio Shape: {audio.shape}")

        else:

            print("[DEBUG] Audio already mono. No conversion required.")

    # Duration calculation
    print("\n[DEBUG] Starting real audio duration calculation...")

    with log_stage("Audio Duration Calculation", recording_id=recording_id):

        # Calculate real duration in seconds
        audio_samples = len(audio)

        print(f"[DEBUG] Total Audio Samples: {audio_samples}")
        print(f"[DEBUG] Sample Rate: {SR}")

        real_duration_sec = len(audio) / SR

        print(f"[SUCCESS] Real Audio Duration: {real_duration_sec:.4f} seconds")

    # Padding/Truncation
    print("\n[DEBUG] Starting audio padding/truncation...")

    with log_stage("Audio Padding/Truncation", recording_id=recording_id):

        # Pad or truncate to exactly 60 seconds

        print(f"[DEBUG] Current Audio Samples: {len(audio)}")
        print(f"[DEBUG] Required Audio Samples: {FILE_SAMPLES}")

        if len(audio) < FILE_SAMPLES:

            padding_samples = FILE_SAMPLES - len(audio)

            print("[DEBUG] Audio is shorter than 60 seconds.")
            print(f"[DEBUG] Padding Required: {padding_samples} samples")
            print(f"[DEBUG] Padding Duration: {padding_samples / SR:.4f} seconds")

            audio = np.pad(
                audio,
                (0, FILE_SAMPLES - len(audio))
            )

            print("[SUCCESS] Audio padding completed.")

        else:

            if len(audio) > FILE_SAMPLES:
                print("[DEBUG] Audio exceeds 60 seconds.")
                print(f"[DEBUG] Truncating {len(audio) - FILE_SAMPLES} samples.")
            else:
                print("[DEBUG] Audio is exactly 60 seconds. No padding/truncation needed.")

            audio = audio[:FILE_SAMPLES]

            print("[SUCCESS] Audio truncation/length adjustment completed.")

        print(f"[DEBUG] Final Audio Shape: {audio.shape}")
        print(f"[DEBUG] Final Audio Samples: {len(audio)}")

    # Final conversion
    print("\n[DEBUG] Converting final audio to float32...")

    final_audio = audio.astype(np.float32)

    print(f"[DEBUG] Final Audio Dtype: {final_audio.dtype}")
    print(f"[DEBUG] Final Audio Shape: {final_audio.shape}")
    print(f"[DEBUG] Real Duration (before padding): {real_duration_sec:.4f}s")
    print("[SUCCESS] Audio loading and preprocessing completed.")
    print("[DEBUG] ==========================================\n")

    return final_audio, real_duration_sec


def compute_valid_windows(real_duration_sec, recording_id=None):
    """
    Compute number of valid (non-padding) windows.
    """

    import math

    print("\n[DEBUG] ==========================================")
    print("[DEBUG] compute_valid_windows() called")
    print(f"[DEBUG] Recording ID: {recording_id}")
    print(f"[DEBUG] Real Duration: {real_duration_sec}")
    print(f"[DEBUG] Window Duration: {WINDOW_SEC}s")
    print("[DEBUG] ==========================================")

    with log_stage("Valid Windows Computation", recording_id=recording_id):

        print("[DEBUG] Calculating number of valid windows...")

        valid_windows = min(
            math.ceil(real_duration_sec / WINDOW_SEC),
            12
        )

        print(f"[DEBUG] Calculated Valid Windows: {valid_windows}")
        print("[DEBUG] Maximum Allowed Windows: 12")

    print(f"[SUCCESS] Valid Windows Computed: {valid_windows}")
    print("[DEBUG] ==========================================\n")

    return valid_windows


def get_waveform_peaks(audio, n_buckets=1000, recording_id=None):
    """
    Compute normalized max-abs amplitude per bucket.
    Includes performance logging.
    """

    print("\n[DEBUG] ==========================================")
    print("[DEBUG] get_waveform_peaks() called")
    print(f"[DEBUG] Recording ID: {recording_id}")
    print(f"[DEBUG] Input Audio Shape: {np.shape(audio)}")
    print(f"[DEBUG] Requested Number of Buckets: {n_buckets}")
    print("[DEBUG] ==========================================")

    with log_stage("Waveform Peaks Computation", recording_id=recording_id):

        print("[DEBUG] Converting audio to float32 NumPy array...")

        audio = np.asarray(audio, dtype=np.float32)

        print(f"[DEBUG] Audio Shape: {audio.shape}")
        print(f"[DEBUG] Audio Dtype: {audio.dtype}")
        print(f"[DEBUG] Total Audio Samples: {len(audio)}")

        bucket_size = len(audio) // n_buckets

        print(f"[DEBUG] Calculated Bucket Size: {bucket_size}")
        print(f"[DEBUG] Total Buckets: {n_buckets}")

        peaks = []

        print("[DEBUG] Starting bucket-wise peak calculation...")

        for i in range(n_buckets):

            start = i * bucket_size
            end = start + bucket_size
            bucket = audio[start:end]

            if len(bucket) > 0:

                peak = np.max(np.abs(bucket))

            else:

                peak = 0.0

            peaks.append(float(peak))

            # Print selected buckets to avoid excessive terminal output
            if i < 5 or i == n_buckets - 1:
                print(
                    f"[DEBUG] Bucket {i}: "
                    f"Start={start}, End={end}, "
                    f"Samples={len(bucket)}, Peak={peak:.6f}"
                )

        print("[SUCCESS] Bucket-wise peak calculation completed.")

        peaks = np.array(peaks, dtype=np.float32)

        print(f"[DEBUG] Peaks Array Shape: {peaks.shape}")
        print(f"[DEBUG] Peaks Array Dtype: {peaks.dtype}")

        max_peak = np.max(peaks) if peaks.max() > 0 else 1.0

        print(f"[DEBUG] Maximum Peak Value: {max_peak}")

        print("[DEBUG] Normalizing waveform peaks...")

        peaks = peaks / (max_peak + 1e-7)

        print("[SUCCESS] Waveform normalization completed.")

        print(f"[DEBUG] Normalized Maximum: {np.max(peaks)}")
        print(f"[DEBUG] Normalized Minimum: {np.min(peaks)}")

    print("[DEBUG] Applying clipping between 0.0 and 1.0...")

    result = np.clip(peaks, 0.0, 1.0).tolist()

    print(f"[SUCCESS] Waveform peaks generated successfully.")
    print(f"[DEBUG] Final Number of Peaks: {len(result)}")
    print("[DEBUG] ==========================================\n")

    return result


print("[SUCCESS] Audio utilities loaded successfully.")
