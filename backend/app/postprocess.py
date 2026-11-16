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

print("\n[POSTPROCESS] Loading post-processing artifacts...")
print(f"[POSTPROCESS] Models directory: {MODELS_DIR}")
print(f"[POSTPROCESS] Temperatures file exists: {TEMPERATURES_PATH.exists()}")
print(f"[POSTPROCESS] Thresholds file exists: {THRESHOLDS_PATH.exists()}")

temperatures = np.load(
    TEMPERATURES_PATH
).astype(np.float32)

per_class_thresholds = np.load(
    THRESHOLDS_PATH
).astype(np.float32)

print(
    "[POSTPROCESS] temperatures:",
    temperatures.shape,
    f"dtype={temperatures.dtype}",
    f"min={temperatures.min():.6f}",
    f"max={temperatures.max():.6f}",
)

print(
    "[POSTPROCESS] thresholds:",
    per_class_thresholds.shape,
    f"dtype={per_class_thresholds.dtype}",
    f"min={per_class_thresholds.min():.6f}",
    f"max={per_class_thresholds.max():.6f}",
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

print("[POSTPROCESS] Artifact shapes validated successfully.")


# ============================================================
# SIGMOID
# ============================================================

def sigmoid(x):
    print(
        f"[POSTPROCESS][sigmoid] Input shape={np.shape(x)}, "
        f"dtype={getattr(x, 'dtype', type(x).__name__)}"
    )

    x = np.clip(
        x,
        -30.0,
        30.0,
    )

    result = 1.0 / (
        1.0 + np.exp(-x)
    )

    print(
        f"[POSTPROCESS][sigmoid] Output shape={result.shape}, "
        f"min={result.min():.6f}, max={result.max():.6f}"
    )
    return result


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

    print(
        f"[POSTPROCESS][temperature] Input shape={np.shape(scores)}"
    )

    scores = np.asarray(
        scores,
        dtype=np.float32,
    )

    result = (
        scores
        / temperatures[None, :]
    ).astype(np.float32)

    print(
        f"[POSTPROCESS][temperature] Output shape={result.shape}, "
        f"min={result.min():.6f}, max={result.max():.6f}"
    )
    return result


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

    print(
        f"[POSTPROCESS][rank_scaling] Input shape={np.shape(probs)}"
    )

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

    result = (
        probs * scale
    ).astype(np.float32)

    print(
        f"[POSTPROCESS][rank_scaling] Output shape={result.shape}, "
        f"scale range=({scale.min():.6f}, {scale.max():.6f}), "
        f"output range=({result.min():.6f}, {result.max():.6f})"
    )
    return result


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

    print(
        f"[POSTPROCESS][file_confidence] Input shape={np.shape(probs)}"
    )

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

    result = (
        probs * scale[None, :]
    ).astype(np.float32)

    print(
        f"[POSTPROCESS][file_confidence] Output shape={result.shape}, "
        f"classes present in any window={int(np.count_nonzero(file_fraction))}/{file_fraction.size}, "
        f"scale range=({scale.min():.6f}, {scale.max():.6f})"
    )
    return result


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

    print(
        f"[POSTPROCESS][smoothing] Input shape={np.shape(probs)}"
    )

    probs = np.asarray(
        probs,
        dtype=np.float32,
    )

    if probs.shape[0] <= 1:
        print(
            "[POSTPROCESS][smoothing] One or fewer windows; "
            "returning an unchanged copy."
        )
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

    result = np.clip(
        smoothed,
        0.0,
        1.0,
    ).astype(np.float32)

    print(
        f"[POSTPROCESS][smoothing] Output shape={result.shape}, "
        f"mean neighbor delta={delta.mean():.6f}, "
        f"smooth-weight range=({smooth_weight.min():.6f}, "
        f"{smooth_weight.max():.6f})"
    )
    return result


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

    print(
        f"[POSTPROCESS][thresholds] Input shape={np.shape(probs)}"
    )

    probs = np.asarray(
        probs,
        dtype=np.float32,
    )

    result = probs.copy()

    mask = (
        result
        < per_class_thresholds[None, :]
    )

    suppressed_count = int(np.count_nonzero(mask))
    total_count = int(mask.size)
    result[mask] = 0.0

    print(
        f"[POSTPROCESS][thresholds] Suppressed {suppressed_count}/{total_count} "
        f"values ({(suppressed_count / total_count * 100.0) if total_count else 0.0:.2f}%), "
        f"remaining non-zero={int(np.count_nonzero(result))}"
    )
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

    print("\n[POSTPROCESS][proto] Starting Proto post-processing.")
    print(
        f"[POSTPROCESS][proto] Received scores shape={np.shape(corrected_scores)}, "
        f"dtype={getattr(corrected_scores, 'dtype', type(corrected_scores).__name__)}"
    )

    corrected_scores = np.asarray(
        corrected_scores,
        dtype=np.float32,
    )

    print(
        f"[POSTPROCESS][proto] Converted scores to float32; "
        f"shape={corrected_scores.shape}, "
        f"min={corrected_scores.min():.6f}, max={corrected_scores.max():.6f}"
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

    print("[POSTPROCESS][proto] Input shape validated.")

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

    print(
        f"[POSTPROCESS][proto] Before final clip: "
        f"min={probs.min():.6f}, max={probs.max():.6f}"
    )
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

    result = probs.astype(
        np.float32
    )

    print(
        f"[POSTPROCESS][proto] Completed. "
        f"Output shape={result.shape}, dtype={result.dtype}, "
        f"min={result.min():.6f}, max={result.max():.6f}, "
        f"non-zero={int(np.count_nonzero(result))}/{result.size}"
    )
    return result
