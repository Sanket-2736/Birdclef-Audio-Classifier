"""
Test script to verify padding detection for short audio clips.
"""

import sys
from pathlib import Path
import numpy as np
import soundfile as sf

# Add backend to path
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

from app.audio_utils import load_audio_with_duration, compute_valid_windows, get_waveform_peaks


def create_test_audio(duration_sec, sr=32000):
    """
    Create a test audio file with a simple sine wave.
    
    Parameters
    ----------
    duration_sec : float
        Duration in seconds
    sr : int
        Sample rate
    
    Returns
    -------
    audio_path : Path
        Path to temporary audio file
    """
    
    n_samples = int(duration_sec * sr)
    t = np.arange(n_samples) / sr
    
    # 440 Hz sine wave
    freq = 440
    audio = 0.5 * np.sin(2 * np.pi * freq * t).astype(np.float32)
    
    temp_dir = Path(__file__).resolve().parent / "temp"
    temp_dir.mkdir(exist_ok=True)
    
    audio_path = temp_dir / f"test_{duration_sec}s.wav"
    
    sf.write(audio_path, audio, sr)
    
    return audio_path


def test_padding_detection():
    """
    Test that short clips produce correct valid_windows counts.
    """
    
    print("=" * 70)
    print("PADDING DETECTION TEST")
    print("=" * 70)
    
    # Test a 28 second clip
    print("\n1. Testing 28-second clip...")
    audio_path_28 = create_test_audio(28.0)
    
    audio, real_duration = load_audio_with_duration(audio_path_28)
    valid_windows = compute_valid_windows(real_duration)
    
    print(f"   Real duration: {real_duration:.2f} sec")
    print(f"   Valid windows: {valid_windows}")
    print(f"   Padded windows: {12 - valid_windows}")
    
    assert abs(real_duration - 28.0) < 0.01, "Real duration should be ~28 sec"
    assert valid_windows == 6, f"Expected 6 valid windows, got {valid_windows}"
    print("   ✓ Correct number of valid windows")
    
    # Test a 15 second clip (3 windows)
    print("\n2. Testing 15-second clip...")
    audio_path_15 = create_test_audio(15.0)
    
    audio, real_duration = load_audio_with_duration(audio_path_15)
    valid_windows = compute_valid_windows(real_duration)
    
    print(f"   Real duration: {real_duration:.2f} sec")
    print(f"   Valid windows: {valid_windows}")
    
    assert abs(real_duration - 15.0) < 0.01, "Real duration should be ~15 sec"
    assert valid_windows == 3, f"Expected 3 valid windows, got {valid_windows}"
    print("   ✓ Correct number of valid windows")
    
    # Test a 5 second clip (1 window)
    print("\n3. Testing 5-second clip...")
    audio_path_5 = create_test_audio(5.0)
    
    audio, real_duration = load_audio_with_duration(audio_path_5)
    valid_windows = compute_valid_windows(real_duration)
    
    print(f"   Real duration: {real_duration:.2f} sec")
    print(f"   Valid windows: {valid_windows}")
    
    assert abs(real_duration - 5.0) < 0.01, "Real duration should be ~5 sec"
    assert valid_windows == 1, f"Expected 1 valid window, got {valid_windows}"
    print("   ✓ Correct number of valid windows")
    
    # Test a full 60 second clip
    print("\n4. Testing 60-second clip (no padding)...")
    audio_path_60 = create_test_audio(60.0)
    
    audio, real_duration = load_audio_with_duration(audio_path_60)
    valid_windows = compute_valid_windows(real_duration)
    
    print(f"   Real duration: {real_duration:.2f} sec")
    print(f"   Valid windows: {valid_windows}")
    
    assert abs(real_duration - 60.0) < 0.01, "Real duration should be ~60 sec"
    assert valid_windows == 12, f"Expected 12 valid windows, got {valid_windows}"
    print("   ✓ All windows valid (no padding)")
    
    # Test waveform peaks
    print("\n5. Testing waveform peak computation...")
    peaks = get_waveform_peaks(audio)
    
    assert len(peaks) == 1000, f"Expected 1000 peaks, got {len(peaks)}"
    assert all(0.0 <= p <= 1.0 for p in peaks), "Peaks should be normalized [0, 1]"
    print(f"   ✓ Waveform peaks: shape={len(peaks)}, range=[{min(peaks):.3f}, {max(peaks):.3f}]")
    
    # Cleanup
    for f in [audio_path_28, audio_path_15, audio_path_5, audio_path_60]:
        if f.exists():
            f.unlink()
    
    temp_dir = Path(__file__).resolve().parent / "temp"
    if temp_dir.exists():
        try:
            temp_dir.rmdir()
        except:
            pass
    
    print("\n" + "=" * 70)
    print("✓ ALL AUDIO UTILITY TESTS PASSED")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    try:
        success = test_padding_detection()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
