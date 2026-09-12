from pathlib import Path
import json
import numpy as np

from .first_pass_predict import predict_first_pass
from .sed_predict import predict_sed
from .final_blend import final_rank_blend


BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# LOAD CLASSES
# ============================================================

with open(BASE_DIR / "models" / "classes.json", "r") as f:
    CLASSES = json.load(f)


# ============================================================
# COMPLETE PIPELINE
# ============================================================

def predict_pipeline(
    audio_path,
    site_id=0,
    hour_id=12,
):
    """
    Complete BirdCLEF pipeline:

        Audio
          ↓
        ProtoSSM branch
          ↓
        SED branch
          ↓
        Final 60/40 rank blend
    """

    # --------------------------------------------------------
    # PROTO BRANCH
    # --------------------------------------------------------

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

    sed_result = predict_sed(audio_path)

    # Your sed_predict.py returns:
    #     (sed_probs, chunks)
    #
    # Handle that format explicitly.

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

    final_probs = final_rank_blend(
        proto_probs,
        sed_probs,
    )

    final_probs = np.asarray(
        final_probs,
        dtype=np.float32,
    )

    # --------------------------------------------------------
    # FILE-LEVEL SCORES
    # --------------------------------------------------------

    file_probs = final_probs.max(axis=0)

    top_idx = np.argsort(
        file_probs
    )[::-1][:10]

    top_predictions = []

    for idx in top_idx:
        top_predictions.append({
            "class_index": int(idx),
            "label": CLASSES[idx],
            "score": float(file_probs[idx]),
        })

    # --------------------------------------------------------
    # WINDOW PREDICTIONS
    # --------------------------------------------------------

    window_predictions = []

    for window_idx in range(final_probs.shape[0]):

        top_window_idx = np.argsort(
            final_probs[window_idx]
        )[::-1][:5]

        predictions = []

        for idx in top_window_idx:
            predictions.append({
                "class_index": int(idx),
                "label": CLASSES[idx],
                "score": float(
                    final_probs[window_idx, idx]
                ),
            })

        window_predictions.append({
            "window": window_idx + 1,
            "start_sec": window_idx * 5,
            "end_sec": (window_idx + 1) * 5,
            "predictions": predictions,
        })

    # --------------------------------------------------------
    # RETURN
    # --------------------------------------------------------

    return {
        "n_windows": int(final_probs.shape[0]),
        "n_classes": int(final_probs.shape[1]),
        "top_predictions": top_predictions,
        "window_predictions": window_predictions,
        "file_scores": file_probs.tolist(),
    }