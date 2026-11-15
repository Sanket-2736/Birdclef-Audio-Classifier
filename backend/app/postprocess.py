from pathlib import Path

import numpy as np


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"

TEMPERATURES_PATH = MODELS_DIR / "temperatures.npy"
THRESHOLDS_PATH = MODELS_DIR / "per_class_thresholds.npy"


# ============================================================
# CONFIG
# ============================================================

N_WINDOWS = 12
N_CLASSES = 234


# ============================================================
# LOAD ARTIFACTS
# ============================================================

print("\nLoading post-processing artifacts...")

temperatures = np.load(
    TEMPERATURES_PATH
).astype(np.float32)

per_class_thresholds = np.load(
    THRESHOLDS_PATH
).astype(np.float32)


print(
    "  temperatures:",
    temperatures.shape
)

print(
    "  thresholds:",
    per_class_thresholds.shape
)


if temperatures.shape != (N_CLASSES,):
    raise ValueError(
        f"Expected temperatures shape "
        f"({N_CLASSES},), got {temperatures.shape}"
    )


if per_class_thresholds.shape != (N_CLASSES,):
    raise ValueError(
        f"Expected thresholds shape "
        f"({N_CLASSES},), got {per_class_thresholds.shape}"
    )


# ============================================================
# SIGMOID
# ============================================================

def sigmoid(x):
    x = np.clip(
        x,
        -30.0,
        30.0,
    )

    return 1.0 / (
        1.0 + np.exp(-x)
    )


# ============================================================
# TEMPERATURE SCALING
# ============================================================

def apply_temperature_scaling(
    scores,
):
    """
    Apply per-class temperature scaling.

    scores:
        (12, 234)
    """

    scores = np.asarray(
        scores,
        dtype=np.float32,
    )

    return (
        scores
        / temperatures[None, :]
    ).astype(np.float32)


# ============================================================
# RANK-AWARE SCALING
# ============================================================

def apply_rank_scaling(
    probs,
):
    """
    Rank-aware scaling across the 12 windows.

    Higher ranked detections receive stronger weight.
    """

    probs = np.asarray(
        probs,
        dtype=np.float32,
    )

    ranks = np.argsort(
        np.argsort(
            probs,
            axis=0
        ),
        axis=0
    )

    rank_norm = (
        ranks.astype(np.float32)
        / max(N_WINDOWS - 1, 1)
    )

    # Keep the scaling gentle.
    scale = 0.85 + 0.30 * rank_norm

    return (
        probs * scale
    ).astype(np.float32)


# ============================================================
# FILE CONFIDENCE SCALING
# ============================================================

def apply_file_confidence_scaling(
    probs,
):
    """
    Increase consistency for classes that appear
    across multiple windows.
    """

    probs = np.asarray(
        probs,
        dtype=np.float32,
    )

    presence = (
        probs > 0.5
    ).astype(np.float32)

    file_fraction = (
        presence.mean(axis=0)
    )

    scale = (
        0.85
        + 0.30 * file_fraction
    )

    return (
        probs * scale[None, :]
    ).astype(np.float32)


# ============================================================
# ADAPTIVE DELTA SMOOTHING
# ============================================================

def adaptive_delta_smoothing(
    probs,
):
    """
    Smooth predictions across neighboring windows.

    Uses neighboring windows while preserving the
    original temporal structure.
    """

    probs = np.asarray(
        probs,
        dtype=np.float32,
    )

    if probs.shape[0] <= 1:
        return probs.copy()

    prev = np.concatenate(
        [
            probs[:1],
            probs[:-1],
        ],
        axis=0,
    )

    nxt = np.concatenate(
        [
            probs[1:],
            probs[-1:],
        ],
        axis=0,
    )

    delta_prev = np.abs(
        probs - prev
    )

    delta_next = np.abs(
        probs - nxt
    )

    delta = (
        delta_prev
        + delta_next
    ) * 0.5

    # Adaptive smoothing:
    # smoother when neighboring predictions
    # are already consistent.
    smooth_weight = np.exp(
        -2.0 * delta
    )

    smoothed = (
        probs * 0.70
        + 0.15 * smooth_weight * prev
        + 0.15 * smooth_weight * nxt
    )

    return np.clip(
        smoothed,
        0.0,
        1.0,
    ).astype(np.float32)


# ============================================================
# PER-CLASS THRESHOLDS
# ============================================================

def apply_per_class_thresholds(
    probs,
):
    """
    Apply trained per-class thresholds.

    Values below a class's threshold are suppressed.
    """

    probs = np.asarray(
        probs,
        dtype=np.float32,
    )

    result = probs.copy()

    mask = (
        result
        < per_class_thresholds[None, :]
    )

    result[mask] = 0.0

    return result.astype(np.float32)


# ============================================================
# COMPLETE PROTO POSTPROCESSING
# ============================================================

def postprocess_proto_scores(
    corrected_scores,
):
    """
    Complete Proto branch post-processing.

    Input:
        corrected_scores: (12, 234)

    Output:
        probabilities: (12, 234)
    """

    corrected_scores = np.asarray(
        corrected_scores,
        dtype=np.float32,
    )

    if corrected_scores.shape != (
        N_WINDOWS,
        N_CLASSES,
    ):
        raise ValueError(
            f"Expected corrected scores "
            f"shape ({N_WINDOWS}, {N_CLASSES}), "
            f"got {corrected_scores.shape}"
        )

    # --------------------------------------------------------
    # 1. Temperature scaling
    # --------------------------------------------------------

    calibrated_logits = (
        apply_temperature_scaling(
            corrected_scores
        )
    )

    # --------------------------------------------------------
    # 2. Sigmoid
    # --------------------------------------------------------

    probs = sigmoid(
        calibrated_logits
    )

    # --------------------------------------------------------
    # 3. File confidence
    # --------------------------------------------------------

    probs = (
        apply_file_confidence_scaling(
            probs
        )
    )

    # --------------------------------------------------------
    # 4. Rank-aware scaling
    # --------------------------------------------------------

    probs = (
        apply_rank_scaling(
            probs
        )
    )

    # --------------------------------------------------------
    # 5. Adaptive temporal smoothing
    # --------------------------------------------------------

    probs = (
        adaptive_delta_smoothing(
            probs
        )
    )

    # --------------------------------------------------------
    # 6. Clip
    # --------------------------------------------------------

    probs = np.clip(
        probs,
        0.0,
        1.0,
    )

    # --------------------------------------------------------
    # 7. Per-class thresholds
    # --------------------------------------------------------

    probs = (
        apply_per_class_thresholds(
            probs
        )
    )

    return probs.astype(
        np.float32
    )