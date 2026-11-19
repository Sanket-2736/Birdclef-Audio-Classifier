"""
Log-Mel Spectrogram generation and acoustic feature extraction module.

Completely independent module for generating mel-spectrograms and extracting
acoustic characteristics from audio recordings. Integrates with existing
prediction results to associate acoustic features with detected species.

Does NOT modify existing inference pipeline, prediction scores, or model outputs.
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import librosa
import librosa.feature
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from scipy.stats import skew, kurtosis

from .utils import log_stage


print("[DEBUG] Initializing Log-Mel Spectrogram module...")

# ============================================================
# CONFIGURATION
# ============================================================

# Audio parameters (consistent with pipeline)
SR = 32_000  # Sample rate (32 kHz)
N_MELS = 128  # Number of mel frequency bands
N_FFT = 2048  # FFT window size
HOP_LENGTH = 512  # Hop length (samples)
WINDOW = 'hann'  # Window function
POWER = 2.0  # Power of spectrogram
FMAX = 16_000  # Max frequency (Nyquist = 16kHz for 32kHz sampling)

# Window structure (from existing pipeline)
WINDOW_SEC = 5
N_WINDOWS = 12

# Output directory structure
ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "artifacts" / "logmel"

print(f"[DEBUG] SR: {SR} Hz")
print(f"[DEBUG] N_MELS: {N_MELS}")
print(f"[DEBUG] N_FFT: {N_FFT}")
print(f"[DEBUG] HOP_LENGTH: {HOP_LENGTH}")
print(f"[DEBUG] FMAX: {FMAX} Hz")
print(f"[DEBUG] Artifacts directory: {ARTIFACTS_DIR}")


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_float(val, default=0.0):
    """Convert to float, handle NaN/inf, return default if invalid."""
    try:
        if val is None:
            return default
        f = float(val)
        if np.isnan(f) or np.isinf(f):
            return default
        return f
    except (TypeError, ValueError):
        return default


def safe_list_float(arr, default_val=0.0):
    """Convert array to list of safe floats."""
    try:
        return [safe_float(x, default_val) for x in arr]
    except (TypeError, ValueError):
        return []


# ============================================================
# ACOUSTIC FEATURE EXTRACTION
# ============================================================

def extract_spectral_features(y: np.ndarray, sr: int) -> Dict:
    """
    Extract spectral features from audio signal.
    
    Parameters
    ----------
    y : np.ndarray
        Audio time series
    sr : int
        Sample rate
    
    Returns
    -------
    dict
        Spectral features (all JSON-serializable floats)
    """
    print("[DEBUG] Extracting spectral features...")
    
    try:
        # Compute STFT
        D = librosa.stft(y, n_fft=N_FFT, hop_length=HOP_LENGTH, window=WINDOW)
        S = np.abs(D) ** POWER
        
        # Spectral centroid
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr, S=S, hop_length=HOP_LENGTH)[0]
        
        # Spectral bandwidth
        bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr, S=S, hop_length=HOP_LENGTH)[0]
        
        # Spectral rolloff (85th percentile)
        rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, S=S, hop_length=HOP_LENGTH)[0]
        
        # Spectral flatness (Wiener entropy)
        flatness = librosa.feature.spectral_flatness(y=y, S=S, hop_length=HOP_LENGTH)[0]
        
        # Zero-crossing rate
        zcr = librosa.feature.zero_crossing_rate(y, hop_length=HOP_LENGTH)[0]
        
        # RMS energy
        S_db = librosa.power_to_db(S, ref=np.max)
        rms = librosa.feature.rms(y=y, hop_length=HOP_LENGTH, S=S_db)[0]
        
        features = {
            "spectral_centroid": {
                "mean": safe_float(np.nanmean(centroid)),
                "std": safe_float(np.nanstd(centroid)),
                "min": safe_float(np.nanmin(centroid)),
                "max": safe_float(np.nanmax(centroid)),
            },
            "spectral_bandwidth": {
                "mean": safe_float(np.nanmean(bandwidth)),
                "std": safe_float(np.nanstd(bandwidth)),
                "min": safe_float(np.nanmin(bandwidth)),
                "max": safe_float(np.nanmax(bandwidth)),
            },
            "spectral_rolloff": {
                "mean": safe_float(np.nanmean(rolloff)),
                "std": safe_float(np.nanstd(rolloff)),
                "min": safe_float(np.nanmin(rolloff)),
                "max": safe_float(np.nanmax(rolloff)),
            },
            "spectral_flatness": {
                "mean": safe_float(np.nanmean(flatness)),
                "std": safe_float(np.nanstd(flatness)),
                "min": safe_float(np.nanmin(flatness)),
                "max": safe_float(np.nanmax(flatness)),
            },
            "zero_crossing_rate": {
                "mean": safe_float(np.nanmean(zcr)),
                "std": safe_float(np.nanstd(zcr)),
                "min": safe_float(np.nanmin(zcr)),
                "max": safe_float(np.nanmax(zcr)),
            },
            "rms_energy": {
                "mean": safe_float(np.nanmean(rms)),
                "std": safe_float(np.nanstd(rms)),
                "min": safe_float(np.nanmin(rms)),
                "max": safe_float(np.nanmax(rms)),
            },
        }
        
        print("[DEBUG] Spectral features extracted successfully")
        return features
    
    except Exception as e:
        print(f"[ERROR] Failed to extract spectral features: {e}")
        return {}


def extract_mel_features(y: np.ndarray, sr: int) -> Dict:
    """
    Extract Mel-spectrogram-related features.
    
    Parameters
    ----------
    y : np.ndarray
        Audio time series
    sr : int
        Sample rate
    
    Returns
    -------
    dict
        Mel features (all JSON-serializable)
    """
    print("[DEBUG] Extracting mel features...")
    
    try:
        # Compute mel-spectrogram
        S = librosa.feature.melspectrogram(
            y=y,
            sr=sr,
            n_fft=N_FFT,
            hop_length=HOP_LENGTH,
            n_mels=N_MELS,
            window=WINDOW,
            fmax=FMAX,
            power=POWER,
        )
        
        # Convert to dB scale
        S_db = librosa.power_to_db(S, ref=np.max)
        
        # Per-band energy statistics
        band_energy = np.mean(S, axis=1)  # Mean energy per mel band
        
        # Mel frequency scale (for reference)
        mel_freqs = librosa.mel_frequencies(n_mels=N_MELS, fmax=FMAX)
        
        features = {
            "n_mels": N_MELS,
            "n_fft": N_FFT,
            "hop_length": HOP_LENGTH,
            "fmax_hz": FMAX,
            "mel_energy": {
                "mean_across_bands": safe_float(np.nanmean(band_energy)),
                "std_across_bands": safe_float(np.nanstd(band_energy)),
                "min_band_energy": safe_float(np.nanmin(band_energy)),
                "max_band_energy": safe_float(np.nanmax(band_energy)),
            },
            "mel_db": {
                "mean_db": safe_float(np.nanmean(S_db)),
                "std_db": safe_float(np.nanstd(S_db)),
                "min_db": safe_float(np.nanmin(S_db)),
                "max_db": safe_float(np.nanmax(S_db)),
            },
            "dominant_mel_bands": [],  # Will fill with top bands
            "mel_band_distribution": safe_list_float(band_energy),
        }
        
        # Find top 5 mel bands by energy
        top_band_indices = np.argsort(band_energy)[-5:][::-1].tolist()
        for idx in top_band_indices:
            freq = safe_float(mel_freqs[idx])
            energy = safe_float(band_energy[idx])
            features["dominant_mel_bands"].append({
                "band_index": int(idx),
                "frequency_hz": freq,
                "energy": energy,
            })
        
        print("[DEBUG] Mel features extracted successfully")
        return features
    
    except Exception as e:
        print(f"[ERROR] Failed to extract mel features: {e}")
        return {}


def extract_mfcc_features(y: np.ndarray, sr: int, n_mfcc: int = 13) -> Dict:
    """
    Extract MFCC (Mel-Frequency Cepstral Coefficients) features.
    
    Parameters
    ----------
    y : np.ndarray
        Audio time series
    sr : int
        Sample rate
    n_mfcc : int
        Number of MFCC coefficients
    
    Returns
    -------
    dict
        MFCC features (all JSON-serializable)
    """
    print(f"[DEBUG] Extracting MFCC features ({n_mfcc} coefficients)...")
    
    try:
        # Compute MFCCs
        mfcc = librosa.feature.mfcc(
            y=y,
            sr=sr,
            n_mfcc=n_mfcc,
            n_fft=N_FFT,
            hop_length=HOP_LENGTH,
            window=WINDOW,
            fmax=FMAX,
        )
        
        # Compute delta (first derivative) and delta-delta
        mfcc_delta = librosa.feature.delta(mfcc)
        mfcc_delta_delta = librosa.feature.delta(mfcc, order=2)
        
        features = {
            "n_mfcc": n_mfcc,
            "mfcc_mean": safe_list_float(np.nanmean(mfcc, axis=1)),
            "mfcc_std": safe_list_float(np.nanstd(mfcc, axis=1)),
            "mfcc_min": safe_list_float(np.nanmin(mfcc, axis=1)),
            "mfcc_max": safe_list_float(np.nanmax(mfcc, axis=1)),
            "mfcc_delta_mean": safe_list_float(np.nanmean(mfcc_delta, axis=1)),
            "mfcc_delta_std": safe_list_float(np.nanstd(mfcc_delta, axis=1)),
            "mfcc_delta_delta_mean": safe_list_float(np.nanmean(mfcc_delta_delta, axis=1)),
            "mfcc_delta_delta_std": safe_list_float(np.nanstd(mfcc_delta_delta, axis=1)),
        }
        
        print("[DEBUG] MFCC features extracted successfully")
        return features
    
    except Exception as e:
        print(f"[ERROR] Failed to extract MFCC features: {e}")
        return {}


def extract_basic_audio_properties(y: np.ndarray, sr: int) -> Dict:
    """
    Extract basic audio properties.
    
    Parameters
    ----------
    y : np.ndarray
        Audio time series
    sr : int
        Sample rate
    
    Returns
    -------
    dict
        Basic properties (all JSON-serializable)
    """
    print("[DEBUG] Extracting basic audio properties...")
    
    try:
        properties = {
            "sample_rate_hz": int(sr),
            "duration_sec": safe_float(len(y) / sr),
            "num_samples": int(len(y)),
            "num_channels": 1,  # Already converted to mono
            "peak_amplitude": safe_float(np.nanmax(np.abs(y))),
            "rms_amplitude": safe_float(np.sqrt(np.nanmean(y ** 2))),
            "is_silent": bool(np.nanmax(np.abs(y)) < 1e-6),
        }
        
        print("[DEBUG] Basic properties extracted successfully")
        return properties
    
    except Exception as e:
        print(f"[ERROR] Failed to extract basic properties: {e}")
        return {}


# ============================================================
# MEL-SPECTROGRAM VISUALIZATION
# ============================================================

def generate_mel_spectrogram_image(
    y: np.ndarray,
    sr: int,
    output_path: Path,
    real_duration_sec: float,
) -> bool:
    """
    Generate high-quality mel-spectrogram PNG image.
    
    Parameters
    ----------
    y : np.ndarray
        Audio time series (32kHz, 1920000 samples for 60 sec)
    sr : int
        Sample rate
    output_path : Path
        Path to save PNG
    real_duration_sec : float
        Real audio duration (before padding)
    
    Returns
    -------
    bool
        True if successful, False otherwise
    """
    print(f"[DEBUG] Generating mel-spectrogram image...")
    print(f"[DEBUG] Output path: {output_path}")
    print(f"[DEBUG] Real duration: {real_duration_sec:.2f} sec")
    
    try:
        # Compute mel-spectrogram
        S = librosa.feature.melspectrogram(
            y=y,
            sr=sr,
            n_fft=N_FFT,
            hop_length=HOP_LENGTH,
            n_mels=N_MELS,
            window=WINDOW,
            fmax=FMAX,
            power=POWER,
        )
        
        # Convert to dB scale
        S_db = librosa.power_to_db(S, ref=np.max)
        
        # Create figure with professional appearance
        fig, ax = plt.subplots(figsize=(14, 6), dpi=100)
        
        # Time axis (in seconds)
        frames = S_db.shape[1]
        time_axis = np.linspace(0, real_duration_sec, frames)
        
        # Mel frequency axis (in Hz)
        mel_freqs = librosa.mel_frequencies(n_mels=N_MELS, fmax=FMAX)
        
        # Plot spectrogram with log-frequency axis
        im = ax.pcolormesh(
            time_axis,
            mel_freqs,
            S_db,
            shading='auto',
            cmap='magma',
            vmin=-80,
            vmax=0,
        )
        
        # Configure axes
        ax.set_xlabel('Time (s)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Mel Frequency (Hz)', fontsize=12, fontweight='bold')
        ax.set_title('Log-Mel Spectrogram', fontsize=14, fontweight='bold', pad=15)
        
        # Add colorbar
        cbar = fig.colorbar(im, ax=ax, format='%+2.0f dB')
        cbar.set_label('Power (dB)', fontsize=11, fontweight='bold')
        
        # Set y-axis to log scale for better visualization
        ax.set_yscale('log')
        
        # Add grid for readability
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        
        # Tight layout
        plt.tight_layout()
        
        # Save to PNG
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(str(output_path), dpi=100, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        print(f"[SUCCESS] Mel-spectrogram image saved: {output_path}")
        return True
    
    except Exception as e:
        print(f"[ERROR] Failed to generate mel-spectrogram image: {e}")
        plt.close('all')
        return False


def generate_window_spectrogram_images(
    y: np.ndarray,
    sr: int,
    recording_dir: Path,
    real_duration_sec: float,
) -> List[str]:
    """
    Generate per-window spectrogram PNG images.
    
    Parameters
    ----------
    y : np.ndarray
        Audio time series
    sr : int
        Sample rate
    recording_dir : Path
        Recording artifacts directory
    real_duration_sec : float
        Real audio duration
    
    Returns
    -------
    list
        List of relative paths to generated window images
    """
    print(f"[DEBUG] Generating {N_WINDOWS} window spectrogram images...")
    
    window_images = []
    
    try:
        for window_idx in range(N_WINDOWS):
            # Window time bounds
            start_sec = window_idx * WINDOW_SEC
            end_sec = (window_idx + 1) * WINDOW_SEC
            
            # Skip if beyond real duration
            if start_sec >= real_duration_sec:
                print(f"[DEBUG] Window {window_idx}: beyond real duration, skipping")
                break
            
            # Extract audio window
            start_sample = int(start_sec * sr)
            end_sample = int(min(end_sec * sr, len(y)))
            
            window_audio = y[start_sample:end_sample]
            
            if len(window_audio) == 0:
                print(f"[DEBUG] Window {window_idx}: empty audio, skipping")
                continue
            
            print(f"[DEBUG] Generating window {window_idx:02d} ({start_sec:.1f}-{end_sec:.1f}s)...")
            
            # Generate window spectrogram
            S = librosa.feature.melspectrogram(
                y=window_audio,
                sr=sr,
                n_fft=N_FFT,
                hop_length=HOP_LENGTH,
                n_mels=N_MELS,
                window=WINDOW,
                fmax=FMAX,
                power=POWER,
            )
            
            S_db = librosa.power_to_db(S, ref=np.max)
            
            # Create figure
            fig, ax = plt.subplots(figsize=(10, 4), dpi=80)
            
            mel_freqs = librosa.mel_frequencies(n_mels=N_MELS, fmax=FMAX)
            window_time = np.linspace(start_sec, end_sec, S_db.shape[1])
            
            im = ax.pcolormesh(
                window_time,
                mel_freqs,
                S_db,
                shading='auto',
                cmap='magma',
                vmin=-80,
                vmax=0,
            )
            
            ax.set_xlabel('Time (s)', fontsize=10, fontweight='bold')
            ax.set_ylabel('Mel Frequency (Hz)', fontsize=10, fontweight='bold')
            ax.set_title(f'Window {window_idx} ({start_sec:.0f}-{end_sec:.0f}s)', fontsize=11, fontweight='bold')
            ax.set_yscale('log')
            ax.grid(True, alpha=0.2, linestyle='--', linewidth=0.5)
            
            fig.colorbar(im, ax=ax, format='%+2.0f dB')
            plt.tight_layout()
            
            # Save window image
            window_filename = f"window_{window_idx:02d}.png"
            window_path = recording_dir / window_filename
            plt.savefig(str(window_path), dpi=80, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            
            window_images.append(window_filename)
            print(f"[SUCCESS] Window {window_idx} image saved: {window_filename}")
        
        print(f"[DEBUG] Generated {len(window_images)} window images")
        return window_images
    
    except Exception as e:
        print(f"[ERROR] Failed to generate window spectrogram images: {e}")
        plt.close('all')
        return window_images


# ============================================================
# WINDOW-LEVEL ACOUSTIC ANALYSIS
# ============================================================

def extract_window_acoustic_features(
    y: np.ndarray,
    sr: int,
    window_idx: int,
    real_duration_sec: float,
) -> Dict:
    """
    Extract acoustic features for a specific time window.
    
    Parameters
    ----------
    y : np.ndarray
        Full audio time series
    sr : int
        Sample rate
    window_idx : int
        Window index (0-11)
    real_duration_sec : float
        Real audio duration
    
    Returns
    -------
    dict
        Window acoustic features
    """
    # Window time bounds
    start_sec = window_idx * WINDOW_SEC
    end_sec = (window_idx + 1) * WINDOW_SEC
    
    # Clip to real duration
    if start_sec >= real_duration_sec:
        return {
            "window_index": window_idx,
            "start_sec": start_sec,
            "end_sec": end_sec,
            "is_padding": True,
            "features": {},
        }
    
    end_sec = min(end_sec, real_duration_sec)
    
    # Extract audio window
    start_sample = int(start_sec * sr)
    end_sample = int(end_sec * sr)
    
    window_audio = y[start_sample:end_sample]
    
    if len(window_audio) == 0:
        return {
            "window_index": window_idx,
            "start_sec": start_sec,
            "end_sec": end_sec,
            "is_padding": True,
            "features": {},
        }
    
    # Extract features for this window
    try:
        # Compute mel-spectrogram for this window
        S = librosa.feature.melspectrogram(
            y=window_audio,
            sr=sr,
            n_fft=N_FFT,
            hop_length=HOP_LENGTH,
            n_mels=N_MELS,
            window=WINDOW,
            fmax=FMAX,
            power=POWER,
        )
        
        S_db = librosa.power_to_db(S, ref=np.max)
        
        # Spectral features
        D = librosa.stft(window_audio, n_fft=N_FFT, hop_length=HOP_LENGTH, window=WINDOW)
        S_power = np.abs(D) ** POWER
        
        centroid = librosa.feature.spectral_centroid(S=S_power, sr=sr, hop_length=HOP_LENGTH)[0]
        bandwidth = librosa.feature.spectral_bandwidth(S=S_power, sr=sr, hop_length=HOP_LENGTH)[0]
        rolloff = librosa.feature.spectral_rolloff(S=S_power, sr=sr, hop_length=HOP_LENGTH)[0]
        flatness = librosa.feature.spectral_flatness(S=S_power, hop_length=HOP_LENGTH)[0]
        zcr = librosa.feature.zero_crossing_rate(window_audio, hop_length=HOP_LENGTH)[0]
        rms = librosa.feature.rms(y=window_audio, hop_length=HOP_LENGTH, S=S_db)[0]
        
        # Mel energy
        band_energy = np.mean(S, axis=1)
        mel_freqs = librosa.mel_frequencies(n_mels=N_MELS, fmax=FMAX)
        
        # MFCCs
        mfcc = librosa.feature.mfcc(
            y=window_audio,
            sr=sr,
            n_mfcc=13,
            n_fft=N_FFT,
            hop_length=HOP_LENGTH,
            window=WINDOW,
            fmax=FMAX,
        )
        
        # Dominant frequency region
        dominant_band_idx = np.argmax(band_energy)
        dominant_freq = safe_float(mel_freqs[dominant_band_idx])
        
        features = {
            "spectral_centroid_mean": safe_float(np.nanmean(centroid)),
            "spectral_bandwidth_mean": safe_float(np.nanmean(bandwidth)),
            "spectral_rolloff_mean": safe_float(np.nanmean(rolloff)),
            "spectral_flatness_mean": safe_float(np.nanmean(flatness)),
            "zero_crossing_rate_mean": safe_float(np.nanmean(zcr)),
            "rms_energy_mean": safe_float(np.nanmean(rms)),
            "dominant_frequency_hz": dominant_freq,
            "dominant_mel_band_index": int(dominant_band_idx),
            "mfcc_mean": safe_list_float(np.nanmean(mfcc, axis=1)),
            "mel_band_energy_top5": [
                {
                    "band_index": int(idx),
                    "frequency_hz": safe_float(mel_freqs[idx]),
                    "energy": safe_float(band_energy[idx]),
                }
                for idx in np.argsort(band_energy)[-5:][::-1]
            ],
        }
        
        return {
            "window_index": window_idx,
            "start_sec": start_sec,
            "end_sec": end_sec,
            "is_padding": False,
            "features": features,
        }
    
    except Exception as e:
        print(f"[ERROR] Failed to extract window features for window {window_idx}: {e}")
        return {
            "window_index": window_idx,
            "start_sec": start_sec,
            "end_sec": end_sec,
            "is_padding": False,
            "features": {},
        }


# ============================================================
# SPECIES-ACOUSTIC ASSOCIATION
# ============================================================

def associate_species_with_acoustics(
    window_analysis: List[Dict],
    prediction_windows: List[Dict],
) -> List[Dict]:
    """
    Associate detected species with acoustic characteristics in each window.
    
    Parameters
    ----------
    window_analysis : list
        Per-window acoustic features
    prediction_windows : list
        Per-window predictions from existing pipeline
    
    Returns
    -------
    list
        Window analysis with species-acoustic associations
    """
    print("[DEBUG] Associating species with acoustic features...")
    
    result = []
    
    for window_idx, (win_acoustic, win_pred) in enumerate(zip(window_analysis, prediction_windows)):
        
        # Get detected species for this window
        detected_species = []
        
        if "top_k" in win_pred and win_pred["top_k"]:
            for species_pred in win_pred["top_k"]:
                detected_species.append({
                    "species_code": species_pred.get("code", ""),
                    "species_name": species_pred.get("common_name", ""),
                    "taxon": species_pred.get("taxon", ""),
                    "confidence": safe_float(species_pred.get("score"), 0.0),
                    "acoustic_features": win_acoustic.get("features", {}),
                })
        
        # Build window entry with both acoustic and species info
        entry = {
            "window_index": window_idx,
            "start_sec": win_acoustic.get("start_sec", 0.0),
            "end_sec": win_acoustic.get("end_sec", 5.0),
            "is_padding": win_acoustic.get("is_padding", False),
            "acoustic_summary": win_acoustic.get("features", {}),
            "detected_species": detected_species,
        }
        
        result.append(entry)
    
    print(f"[DEBUG] Associated species with acoustics for {len(result)} windows")
    return result


# ============================================================
# MAIN SPECTROGRAM GENERATION FUNCTION
# ============================================================

def generate_logmel_spectrogram(
    audio_path: Path,
    recording_id: str,
    real_duration_sec: float,
    prediction_result: Optional[Dict] = None,
) -> Dict:
    """
    Generate log-mel spectrogram, extract acoustic features, and associate with predictions.
    
    **COMPLETELY INDEPENDENT** of existing pipeline - does not modify prediction scores
    or inference results. Only adds new artifacts and metadata.
    
    Parameters
    ----------
    audio_path : Path
        Path to audio file (already validated, 32kHz mono, 60 sec padded)
    recording_id : str
        Recording unique identifier
    real_duration_sec : float
        Real audio duration before padding
    prediction_result : dict, optional
        Existing prediction result from pipeline (for species association)
    
    Returns
    -------
    dict
        Spectrogram metadata with paths, features, and associations
        
        Structure:
        {
            "recording_id": str,
            "status": "completed" | "failed",
            "error_message": str (nullable),
            "spectrogram_image": "spectrogram.png",  # Relative path in recording dir
            "window_images": ["window_00.png", ...],  # Optional window images
            "audio_properties": {...},  # Basic audio info
            "spectral_features": {...},  # Spectral analysis
            "mel_features": {...},  # Mel-spectrogram analysis
            "mfcc_features": {...},  # MFCC analysis
            "window_analysis": [...],  # Per-window acoustic + species
            "metadata_json": "metadata.json",  # Relative path
        }
    """
    
    print("\n" + "=" * 70)
    print("[DEBUG] LOG-MEL SPECTROGRAM GENERATION STARTED")
    print("=" * 70)
    print(f"[DEBUG] Recording ID: {recording_id}")
    print(f"[DEBUG] Audio Path: {audio_path}")
    print(f"[DEBUG] Real Duration: {real_duration_sec:.2f} sec")
    print(f"[DEBUG] Prediction Result Available: {prediction_result is not None}")
    
    result = {
        "recording_id": recording_id,
        "status": "processing",
        "error_message": None,
        "spectrogram_image": None,
        "window_images": [],
        "audio_properties": {},
        "spectral_features": {},
        "mel_features": {},
        "mfcc_features": {},
        "window_analysis": [],
        "metadata_json": None,
    }
    
    try:
        # --------------------------------------------------------
        # Create recording artifacts directory
        # --------------------------------------------------------
        recording_dir = ARTIFACTS_DIR / recording_id
        recording_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[DEBUG] Recording artifacts directory: {recording_dir}")
        
        # --------------------------------------------------------
        # Load audio
        # --------------------------------------------------------
        with log_stage("Audio Loading for Spectrogram", recording_id=recording_id):
            print("[DEBUG] Loading audio file...")
            
            try:
                y, sr = librosa.load(str(audio_path), sr=SR, mono=True)
                print(f"[DEBUG] Audio loaded: shape={y.shape}, sr={sr}")
            except Exception as e:
                print(f"[ERROR] Failed to load audio: {e}")
                raise RuntimeError(f"Audio loading failed: {e}")
        
        # --------------------------------------------------------
        # Extract acoustic features
        # --------------------------------------------------------
        with log_stage("Acoustic Feature Extraction", recording_id=recording_id):
            print("[DEBUG] Extracting audio properties...")
            result["audio_properties"] = extract_basic_audio_properties(y, sr)
            
            print("[DEBUG] Extracting spectral features...")
            result["spectral_features"] = extract_spectral_features(y, sr)
            
            print("[DEBUG] Extracting mel features...")
            result["mel_features"] = extract_mel_features(y, sr)
            
            print("[DEBUG] Extracting MFCC features...")
            result["mfcc_features"] = extract_mfcc_features(y, sr, n_mfcc=13)
        
        # --------------------------------------------------------
        # Generate full spectrogram image
        # --------------------------------------------------------
        with log_stage("Spectrogram Image Generation", recording_id=recording_id):
            spec_filename = "spectrogram.png"
            spec_path = recording_dir / spec_filename
            
            if generate_mel_spectrogram_image(y, sr, spec_path, real_duration_sec):
                result["spectrogram_image"] = spec_filename
                print(f"[SUCCESS] Spectrogram image saved")
            else:
                print("[ERROR] Failed to generate spectrogram image")
                result["error_message"] = "Spectrogram image generation failed"
        
        # --------------------------------------------------------
        # Generate window spectrogram images (optional)
        # --------------------------------------------------------
        with log_stage("Window Spectrogram Generation", recording_id=recording_id):
            window_images = generate_window_spectrogram_images(y, sr, recording_dir, real_duration_sec)
            result["window_images"] = window_images
            print(f"[SUCCESS] Generated {len(window_images)} window spectrogram images")
        
        # --------------------------------------------------------
        # Extract per-window acoustic features
        # --------------------------------------------------------
        with log_stage("Per-Window Acoustic Analysis", recording_id=recording_id):
            print("[DEBUG] Extracting per-window acoustic features...")
            
            window_analysis = []
            for window_idx in range(N_WINDOWS):
                win_features = extract_window_acoustic_features(y, sr, window_idx, real_duration_sec)
                window_analysis.append(win_features)
            
            # --------------------------------------------------------
            # Associate with species predictions
            # --------------------------------------------------------
            if prediction_result and "windows" in prediction_result:
                print("[DEBUG] Associating detected species with acoustic features...")
                result["window_analysis"] = associate_species_with_acoustics(
                    window_analysis,
                    prediction_result["windows"],
                )
            else:
                print("[DEBUG] No prediction result provided, storing acoustic features only")
                result["window_analysis"] = window_analysis
        
        # --------------------------------------------------------
        # Save metadata JSON
        # --------------------------------------------------------
        with log_stage("Metadata Serialization", recording_id=recording_id):
            metadata_filename = "metadata.json"
            metadata_path = recording_dir / metadata_filename
            
            # Prepare metadata for JSON serialization
            metadata = {
                "recording_id": recording_id,
                "generated_at": str(__import__('datetime').datetime.utcnow().isoformat()),
                "configuration": {
                    "sample_rate": SR,
                    "n_mels": N_MELS,
                    "n_fft": N_FFT,
                    "hop_length": HOP_LENGTH,
                    "fmax": FMAX,
                    "window_function": WINDOW,
                    "power": POWER,
                },
                "audio_properties": result["audio_properties"],
                "spectral_features": result["spectral_features"],
                "mel_features": result["mel_features"],
                "mfcc_features": result["mfcc_features"],
                "window_analysis": result["window_analysis"],
            }
            
            try:
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                result["metadata_json"] = metadata_filename
                print(f"[SUCCESS] Metadata saved to {metadata_filename}")
            except Exception as e:
                print(f"[ERROR] Failed to save metadata JSON: {e}")
                result["error_message"] = f"Metadata save failed: {e}"
        
        # --------------------------------------------------------
        # Final status
        # --------------------------------------------------------
        result["status"] = "completed"
        print("\n[SUCCESS] LOG-MEL SPECTROGRAM GENERATION COMPLETED")
        print("=" * 70 + "\n")
        
        return result
    
    except Exception as e:
        print(f"\n[ERROR] LOG-MEL SPECTROGRAM GENERATION FAILED: {e}")
        print("=" * 70 + "\n")
        result["status"] = "failed"
        result["error_message"] = str(e)
        return result


print("[SUCCESS] Log-Mel Spectrogram module loaded successfully")
