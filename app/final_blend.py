from pathlib import Path

import json
import numpy as np
import pandas as pd


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS = BASE_DIR / "models"

N_CLASSES = 234

PROTO_WEIGHT = 0.60
SED_WEIGHT = 0.40

EPS = 1e-5


# ============================================================
# LOAD CLASSES
# ============================================================

with open(ARTIFACTS / "classes.json", "r") as f:
    CLASSES = json.load(f)

if len(CLASSES) != N_CLASSES:
    raise RuntimeError(
        f"Expected {N_CLASSES} classes, got {len(CLASSES)}"
    )


# ============================================================
# RANK BLEND
# ============================================================

def final_rank_blend(
    proto_probs,
    sed_probs,
):
    """
    Exact notebook final blend.

    Parameters
    ----------
    proto_probs : np.ndarray
        Shape (12, 234)

    sed_probs : np.ndarray
        Shape (12, 234)

    Returns
    -------
    pred : np.ndarray
        Shape (12, 234)
    """

    proto_probs = np.asarray(
        proto_probs,
        dtype=np.float32,
    )

    sed_probs = np.asarray(
        sed_probs,
        dtype=np.float32,
    )

    if proto_probs.shape != sed_probs.shape:
        raise ValueError(
            f"Shape mismatch: "
            f"Proto={proto_probs.shape}, "
            f"SED={sed_probs.shape}"
        )

    if proto_probs.shape[1] != N_CLASSES:
        raise ValueError(
            f"Expected {N_CLASSES} classes, "
            f"got {proto_probs.shape[1]}"
        )

    # --------------------------------------------------------
    # Clip probabilities
    # --------------------------------------------------------

    p_proto = np.clip(
        proto_probs,
        EPS,
        1.0 - EPS,
    )

    p_sed = np.clip(
        sed_probs,
        EPS,
        1.0 - EPS,
    )

    # --------------------------------------------------------
    # Percentile ranks
    # Exact notebook:
    #
    # pd.DataFrame(...).rank(axis=0, pct=True)
    # --------------------------------------------------------

    rank_proto = (
        pd.DataFrame(p_proto)
        .rank(axis=0, pct=True)
        .to_numpy(np.float32)
    )

    rank_sed = (
        pd.DataFrame(p_sed)
        .rank(axis=0, pct=True)
        .to_numpy(np.float32)
    )

    # --------------------------------------------------------
    # Standard 60 / 40 blend
    # --------------------------------------------------------

    pred = (
        rank_proto * PROTO_WEIGHT
        + rank_sed * SED_WEIGHT
    )

    # ========================================================
    # FAKE-ONLY GATE
    # ========================================================

    fake_only = (
        (p_proto > 0.50)
        & (p_sed < 0.05)
    )

    pred = np.where(
        fake_only,
        (1.0 - 0.08) * pred
        + 0.08 * rank_proto,
        pred,
    )

    # ========================================================
    # PROTO TEMPORAL CONTINUITY
    # ========================================================

    offs = np.arange(
        -3,
        4,
        dtype=np.float32,
    )

    proto_kernel = (
        1.0
        + (offs / 1.20) ** 2 / 2.0
    ) ** (-1.5)

    proto_kernel = (
        proto_kernel
        / proto_kernel.sum()
    ).astype(np.float32)

    # --------------------------------------------------------
    # Group rows by file
    #
    # For API one file = 12 windows, so this will simply
    # operate over all 12 windows.
    # --------------------------------------------------------

    pa_ctx = p_proto.copy()

    xp = np.pad(
        p_proto,
        ((3, 3), (0, 0)),
        mode="edge",
    )

    pa_ctx = sum(
        proto_kernel[i]
        * xp[i:i + len(p_proto)]
        for i in range(7)
    )

    xctx = (
        pd.DataFrame(pa_ctx)
        .rank(axis=0, pct=True)
        .to_numpy(np.float32)
    )

    # --------------------------------------------------------
    # Proto continuity gate
    # --------------------------------------------------------

    proto_cont = (
        (xctx > 0.88)
        & (rank_proto > 0.75)
        & (p_sed < 0.12)
        & (~fake_only)
    )

    pred = np.where(
        proto_cont,
        (1.0 - 0.15) * pred
        + 0.15 * np.maximum(
            rank_proto,
            xctx,
        ),
        pred,
    )

    # ========================================================
    # SED-ONLY GATE
    # ========================================================

    sed_only = (
        (rank_sed > 0.95)
        & (rank_proto < 0.80)
        & (~fake_only)
        & (~proto_cont)
    )

    pred = np.where(
        sed_only,
        (1.0 - 0.12) * pred
        + 0.12 * rank_sed,
        pred,
    )

    # --------------------------------------------------------
    # Final clipping
    # --------------------------------------------------------

    pred = np.clip(
        pred,
        0.0,
        1.0,
    ).astype(np.float32)

    return pred


# ============================================================
# CLI TEST
# ============================================================

if __name__ == "__main__":

    import sys

    if len(sys.argv) != 3:
        print(
            "Usage:"
        )
        print(
            "python -m app.final_blend "
            "proto.npy sed.npy"
        )
        raise SystemExit(1)

    proto_path = Path(sys.argv[1])
    sed_path = Path(sys.argv[2])

    proto = np.load(proto_path)
    sed = np.load(sed_path)

    print("Proto:", proto.shape)
    print("SED:  ", sed.shape)

    final = final_rank_blend(
        proto,
        sed,
    )

    print(
        "Final:",
        final.shape,
    )

    print(
        "min:",
        final.min(),
    )

    print(
        "max:",
        final.max(),
    )

    print(
        "mean:",
        final.mean(),
    )

    print(
        "\nFINAL BLEND SUCCESS"
    )