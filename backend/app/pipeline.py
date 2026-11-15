from pathlib import Path
import json
import math
import numpy as np
from typing import Optional, Callable

from .species_mapping import get_species_info
from .audio_utils import load_audio_with_duration, compute_valid_windows, get_waveform_peaks
from .taxonomy import get_taxon
from .first_pass_predict import predict_first_pass
from .sed_predict import predict_sed
from .final_blend import final_rank_blend
from .postprocess import per_class_thresholds


BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# LOAD CLASSES
# ============================================================

with open(BASE_DIR / "models" / "classes.json", "r") as f:
    CLASSES = json.load(f)

N_CLASSES = len(CLASSES)
N_WINDOWS = 12
WINDOW_SEC = 5


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def mask_padding_windows(scores, valid_windows):
    """Zero out scores for padding windows."""
    scores = scores.copy()
    if valid_windows < N_WINDOWS:
        scores[valid_windows:, :] = 0.0
    return scores


def compute_window_detections(final_probs, valid_windows):
    """For each species, count windows where it was detected."""
    detections = np.zeros(N_CLASSES, dtype=np.int32)
    valid_probs = final_probs[:valid_windows]
    
    for class_idx in range(N_CLASSES):
        threshold = per_class_thresholds[class_idx]
        detected = (valid_probs[:, class_idx] >= threshold).sum()
        detections[class_idx] = int(detected)
    
    return detections


def rank_species(final_probs, valid_windows, real_duration_sec):
    """Rank species by: detections (desc), mean_score (desc), max_score (desc)."""
    valid_probs = final_probs[:valid_windows]
    detections = compute_window_detections(final_probs, valid_windows)
    max_scores = final_probs.max(axis=0)
    mean_scores = valid_probs.mean(axis=0)
    
    rankings = [
        (
            -int(detections[i]),
            -float(mean_scores[i]),
            -float(max_scores[i]),
            i
        )
        for i in range(N_CLASSES)
    ]
    
    rankings.sort()
    top_species = []
    
    for rank, (_, _, _, class_idx) in enumerate(rankings[:10]):
        label = CLASSES[class_idx]
        species = get_species_info(label)
        
        windows_detected = int(detections[class_idx])
        seconds_present = min(
            windows_detected * WINDOW_SEC,
            real_duration_sec
        )
        
        top_species.append({
            "rank": rank + 1,
            "code": label,
            "common_name": species["common_name"],
            "scientific_name": species["scientific_name"],
            "taxon": get_taxon(label),
            "max_score": float(max_scores[class_idx]),
            "mean_score": float(mean_scores[class_idx]),
            "windows_detected": windows_detected,
            "seconds_present": min(seconds_present, real_duration_sec),
        })
    
    return top_species


def build_windows_response(final_probs, valid_windows, real_duration_sec):
    """Build per-window predictions with padding flags."""
    windows = []
    
    for window_idx in range(N_WINDOWS):
        is_padding = window_idx >= valid_windows
        
        if is_padding:
            top_window_idx = []
        else:
            top_window_idx = np.argsort(
                final_probs[window_idx]
            )[::-1][:5]
        
        predictions = []
        
        for idx in top_window_idx:
            label = CLASSES[idx]
            species = get_species_info(label)
            
            predictions.append({
                "code": label,
                "common_name": species["common_name"],
                "scientific_name": species["scientific_name"],
                "taxon": get_taxon(label),
                "score": float(final_probs[window_idx][idx]),
            })
        
        windows.append({
            "index": window_idx,
            "start_sec": window_idx * WINDOW_SEC,
            "end_sec": (window_idx + 1) * WINDOW_SEC,
            "is_padding": is_padding,
            "top_k": predictions,
        })
    
    return windows


def build_heatmap(final_probs, valid_windows):
    """Build heatmap: species detected at least once."""
    valid_probs = final_probs[:valid_windows]
    max_per_species = valid_probs.max(axis=0)
    detected_mask = max_per_species > 0
    detected_indices = np.where(detected_mask)[0]
    
    species_list = []
    heatmap_matrix = []
    
    for class_idx in detected_indices:
        label = CLASSES[class_idx]
        species = get_species_info(label)
        
        species_list.append({
            "code": label,
            "common_name": species["common_name"],
            "scientific_name": species["scientific_name"],
            "taxon": get_taxon(label),
        })
        
        heatmap_matrix.append(valid_probs[:, class_idx].tolist())
    
    return {
        "species": species_list,
        "matrix": heatmap_matrix,
    }


def build_branch_scores(proto_result, sed_result, final_probs, valid_windows):
    """Extract branch scores for visualization."""
    valid_probs = final_probs[:valid_windows]
    top_indices = np.argsort(valid_probs.max(axis=0))[::-1][:15]
    
    branch_scores = {
        "proto": proto_result.get("proto_probs", []).tolist()[:valid_windows]
            if isinstance(proto_result.get("proto_probs"), np.ndarray)
            else proto_result.get("proto_probs", [])[:valid_windows],
        "sed": (sed_result[0] if isinstance(sed_result, tuple) else sed_result).tolist()[:valid_windows]
            if isinstance((sed_result[0] if isinstance(sed_result, tuple) else sed_result), np.ndarray)
            else (sed_result[0] if isinstance(sed_result, tuple) else sed_result)[:valid_windows],
        "final": final_probs.tolist()[:valid_windows],
        "species_indices": top_indices.tolist(),
    }
    
    return branch_scores


# ============================================================
# COMPLETE PIPELINE
# ============================================================

def predict_pipeline(
    audio_path,
    site_id=0,
    hour_id=12,
    progress_callback: Optional[Callable[[str], None]] = None,
):
    """
    Complete BirdCLEF pipeline with progress tracking.

    Parameters
    ----------
    audio_path : str or Path
        Path to audio file
    site_id : int
        Site ID (0-19)
    hour_id : int
        Hour of day (0-23)
    progress_callback : callable, optional
        Callback function(stage_name) called at each stage

    Returns
    -------
    dict
        Prediction results with windows, heatmap, top_species, etc.
    """
    
    def progress(stage: str):
        """Call progress callback if provided."""
        if progress_callback:
            progress_callback(stage)

    # --------------------------------------------------------
    # LOAD AUDIO WITH REAL DURATION
    # --------------------------------------------------------
    
    progress("Loading audio")
    audio, real_duration_sec = load_audio_with_duration(audio_path)
    valid_windows = compute_valid_windows(real_duration_sec)

    # --------------------------------------------------------
    # PROTO BRANCH
    # --------------------------------------------------------

    progress("Perch embeddings")
    proto_result = predict_first_pass(
        audio_path=audio_path,
        site_id=site_id,
        hour_id=hour_id,
    )

    proto_probs = np.asarray(
        proto_result["proto_probs"],
        dtype=np.float32,
    )

    # --------------------------------------------------------
    # SED BRANCH
    # --------------------------------------------------------

    progress("SED detection")
    sed_result = predict_sed(audio_path)

    if isinstance(sed_result, tuple):
        sed_probs = sed_result[0]
    else:
        sed_probs = sed_result

    sed_probs = np.asarray(
        sed_probs,
        dtype=np.float32,
    )

    # --------------------------------------------------------
    # FINAL BLEND
    # --------------------------------------------------------

    progress("Blending results")
    final_probs = final_rank_blend(
        proto_probs,
        sed_probs,
    )

    final_probs = np.asarray(
        final_probs,
        dtype=np.float32,
    )

    # --------------------------------------------------------
    # MASK PADDING WINDOWS
    # --------------------------------------------------------
    
    final_probs = mask_padding_windows(final_probs, valid_windows)

    # --------------------------------------------------------
    # POST-PROCESSING
    # --------------------------------------------------------
    
    progress("Post-processing")
    
    # Get waveform peaks from real audio only
    real_audio_samples = int(real_duration_sec * 32000)
    waveform_peaks = get_waveform_peaks(audio[:real_audio_samples])
    
    top_species = rank_species(final_probs, valid_windows, real_duration_sec)
    windows = build_windows_response(final_probs, valid_windows, real_duration_sec)
    heatmap = build_heatmap(final_probs, valid_windows)
    branch_scores = build_branch_scores(proto_result, sed_result, final_probs, valid_windows)
    
    progress("Completed")
    
    return {
        "real_duration_sec": float(real_duration_sec),
        "n_windows": int(final_probs.shape[0]),
        "n_classes": int(final_probs.shape[1]),
        "valid_windows": int(valid_windows),
        "windows": windows,
        "heatmap": heatmap,
        "branch_scores": branch_scores,
        "top_species": top_species,
        "waveform_peaks": waveform_peaks,
    }