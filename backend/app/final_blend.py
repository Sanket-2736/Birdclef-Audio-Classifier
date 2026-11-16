
from pathlib import Path

import json
import numpy as np
import pandas as pd


print("\n[DEBUG] Initializing Final Rank Blend module...")


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS = BASE_DIR / "models"

N_CLASSES = 234

PROTO_WEIGHT = 0.60
SED_WEIGHT = 0.40

EPS = 1e-5

print(f"[DEBUG] BASE_DIR: {BASE_DIR}")
print(f"[DEBUG] ARTIFACTS: {ARTIFACTS}")
print(f"[DEBUG] Expected classes: {N_CLASSES}")
print(f"[DEBUG] Proto weight: {PROTO_WEIGHT}")
print(f"[DEBUG] SED weight: {SED_WEIGHT}")
print(f"[DEBUG] EPS: {EPS}")


# ============================================================
# LOAD CLASSES
# ============================================================

print("\n[DEBUG] Loading classes.json...")

classes_path = ARTIFACTS / "classes.json"

print(f"[DEBUG] Classes file path: {classes_path}")

with open(classes_path, "r") as f:
    CLASSES = json.load(f)

print("[SUCCESS] Classes loaded successfully.")
print(f"[DEBUG] Total classes loaded: {len(CLASSES)}")

if len(CLASSES) != N_CLASSES:
    print("[ERROR] Class count mismatch!")
    print(f"[ERROR] Expected: {N_CLASSES}")
    print(f"[ERROR] Actual: {len(CLASSES)}")

    raise RuntimeError(
        f"Expected {N_CLASSES} classes, got {len(CLASSES)}"
    )

print("[SUCCESS] Class count validation passed.")


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

    print("\n" + "=" * 65)
    print("[DEBUG] FINAL RANK BLEND STARTED")
    print("=" * 65)

    # --------------------------------------------------------
    # Input information
    # --------------------------------------------------------

    print("\n[DEBUG] Step 1: Inspecting input arrays...")

    print(f"[DEBUG] Proto input type: {type(proto_probs)}")
    print(f"[DEBUG] SED input type: {type(sed_probs)}")

    # --------------------------------------------------------
    # Convert to NumPy arrays
    # --------------------------------------------------------

    print("\n[DEBUG] Step 2: Converting inputs to float32 arrays...")

    proto_probs = np.asarray(
        proto_probs,
        dtype=np.float32,
    )

    sed_probs = np.asarray(
        sed_probs,
        dtype=np.float32,
    )

    print("[SUCCESS] Input conversion completed.")

    print(f"[DEBUG] Proto shape: {proto_probs.shape}")
    print(f"[DEBUG] SED shape: {sed_probs.shape}")

    print(f"[DEBUG] Proto dtype: {proto_probs.dtype}")
    print(f"[DEBUG] SED dtype: {sed_probs.dtype}")

    print(
        f"[DEBUG] Proto range: "
        f"{proto_probs.min():.6f} to {proto_probs.max():.6f}"
    )

    print(
        f"[DEBUG] SED range: "
        f"{sed_probs.min():.6f} to {sed_probs.max():.6f}"
    )

    # --------------------------------------------------------
    # Shape validation
    # --------------------------------------------------------

    print("\n[DEBUG] Step 3: Validating input shapes...")

    if proto_probs.shape != sed_probs.shape:

        print("[ERROR] Proto and SED shapes do not match!")
        print(f"[ERROR] Proto: {proto_probs.shape}")
        print(f"[ERROR] SED: {sed_probs.shape}")

        raise ValueError(
            f"Shape mismatch: "
            f"Proto={proto_probs.shape}, "
            f"SED={sed_probs.shape}"
        )

    print("[SUCCESS] Input shapes match.")

    if proto_probs.shape[1] != N_CLASSES:

        print("[ERROR] Unexpected number of classes!")
        print(f"[ERROR] Expected: {N_CLASSES}")
        print(f"[ERROR] Received: {proto_probs.shape[1]}")

        raise ValueError(
            f"Expected {N_CLASSES} classes, "
            f"got {proto_probs.shape[1]}"
        )

    print("[SUCCESS] Class dimension validation passed.")

    # --------------------------------------------------------
    # Clip probabilities
    # --------------------------------------------------------

    print("\n[DEBUG] Step 4: Clipping probabilities...")
    print(f"[DEBUG] Clipping range: [{EPS}, {1.0 - EPS}]")

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

    print("[SUCCESS] Probability clipping completed.")

    print(
        f"[DEBUG] Proto clipped range: "
        f"{p_proto.min():.6f} to {p_proto.max():.6f}"
    )

    print(
        f"[DEBUG] SED clipped range: "
        f"{p_sed.min():.6f} to {p_sed.max():.6f}"
    )

    # --------------------------------------------------------
    # Percentile ranks
    # --------------------------------------------------------

    print("\n[DEBUG] Step 5: Calculating percentile ranks...")

    print("[DEBUG] Calculating Proto percentile ranks...")

    rank_proto = (
        pd.DataFrame(p_proto)
        .rank(axis=0, pct=True)
        .to_numpy(np.float32)
    )

    print("[SUCCESS] Proto percentile ranks calculated.")
    print(f"[DEBUG] Proto rank shape: {rank_proto.shape}")

    print("[DEBUG] Calculating SED percentile ranks...")

    rank_sed = (
        pd.DataFrame(p_sed)
        .rank(axis=0, pct=True)
        .to_numpy(np.float32)
    )

    print("[SUCCESS] SED percentile ranks calculated.")
    print(f"[DEBUG] SED rank shape: {rank_sed.shape}")

    print(
        f"[DEBUG] Proto rank range: "
        f"{rank_proto.min():.6f} to {rank_proto.max():.6f}"
    )

    print(
        f"[DEBUG] SED rank range: "
        f"{rank_sed.min():.6f} to {rank_sed.max():.6f}"
    )

    # --------------------------------------------------------
    # Standard 60 / 40 blend
    # --------------------------------------------------------

    print("\n[DEBUG] Step 6: Performing standard 60:40 blend...")

    print(f"[DEBUG] Proto contribution: {PROTO_WEIGHT * 100}%")
    print(f"[DEBUG] SED contribution: {SED_WEIGHT * 100}%")

    pred = (
        rank_proto * PROTO_WEIGHT
        + rank_sed * SED_WEIGHT
    )

    print("[SUCCESS] Initial rank blending completed.")

    print(
        f"[DEBUG] Initial prediction range: "
        f"{pred.min():.6f} to {pred.max():.6f}"
    )

    print(f"[DEBUG] Initial prediction mean: {pred.mean():.6f}")

    # ========================================================
    # FAKE-ONLY GATE
    # ========================================================

    print("\n[DEBUG] Step 7: Applying FAKE-ONLY GATE...")

    fake_only = (
        (p_proto > 0.50)
        & (p_sed < 0.05)
    )

    fake_only_count = np.sum(fake_only)

    print(f"[DEBUG] Fake-only detections: {fake_only_count}")
    print(
        f"[DEBUG] Fake-only percentage: "
        f"{(fake_only_count / fake_only.size) * 100:.4f}%"
    )

    pred = np.where(
        fake_only,
        (1.0 - 0.08) * pred
        + 0.08 * rank_proto,
        pred,
    )

    print("[SUCCESS] Fake-only gate applied.")

    print(
        f"[DEBUG] Prediction mean after fake-only gate: "
        f"{pred.mean():.6f}"
    )

    # ========================================================
    # PROTO TEMPORAL CONTINUITY
    # ========================================================

    print("\n[DEBUG] Step 8: Applying PROTO TEMPORAL CONTINUITY...")

    print("[DEBUG] Creating temporal offsets...")

    offs = np.arange(
        -3,
        4,
        dtype=np.float32,
    )

    print(f"[DEBUG] Temporal offsets: {offs}")

    print("[DEBUG] Calculating prototype temporal kernel...")

    proto_kernel = (
        1.0
        + (offs / 1.20) ** 2 / 2.0
    ) ** (-1.5)

    proto_kernel = (
        proto_kernel
        / proto_kernel.sum()
    ).astype(np.float32)

    print("[SUCCESS] Temporal kernel generated.")

    print(f"[DEBUG] Kernel values: {proto_kernel}")
    print(f"[DEBUG] Kernel sum: {proto_kernel.sum():.6f}")

    # --------------------------------------------------------
    # Group rows by file
    # --------------------------------------------------------

    print("\n[DEBUG] Preparing prototype temporal context...")

    print(f"[DEBUG] Original Proto shape: {p_proto.shape}")

    pa_ctx = p_proto.copy()

    xp = np.pad(
        p_proto,
        ((3, 3), (0, 0)),
        mode="edge",
    )

    print(f"[DEBUG] Padded Proto shape: {xp.shape}")

    print("[DEBUG] Applying temporal kernel across windows...")

    pa_ctx = sum(
        proto_kernel[i]
        * xp[i:i + len(p_proto)]
        for i in range(7)
    )

    print("[SUCCESS] Temporal context calculation completed.")

    print(f"[DEBUG] Temporal context shape: {pa_ctx.shape}")

    print(
        f"[DEBUG] Temporal context range: "
        f"{pa_ctx.min():.6f} to {pa_ctx.max():.6f}"
    )

    print("[DEBUG] Calculating temporal context percentile ranks...")

    xctx = (
        pd.DataFrame(pa_ctx)
        .rank(axis=0, pct=True)
        .to_numpy(np.float32)
    )

    print("[SUCCESS] Temporal context ranks calculated.")
    print(f"[DEBUG] Context rank shape: {xctx.shape}")

    # --------------------------------------------------------
    # Proto continuity gate
    # --------------------------------------------------------

    print("\n[DEBUG] Applying Proto continuity gate conditions...")

    proto_cont = (
        (xctx > 0.88)
        & (rank_proto > 0.75)
        & (p_sed < 0.12)
        & (~fake_only)
    )

    proto_cont_count = np.sum(proto_cont)

    print(f"[DEBUG] Proto continuity detections: {proto_cont_count}")

    print(
        f"[DEBUG] Proto continuity percentage: "
        f"{(proto_cont_count / proto_cont.size) * 100:.4f}%"
    )

    print("[DEBUG] Updating predictions using continuity gate...")

    pred = np.where(
        proto_cont,
        (1.0 - 0.15) * pred
        + 0.15 * np.maximum(
            rank_proto,
            xctx,
        ),
        pred,
    )

    print("[SUCCESS] Proto continuity gate applied.")

    print(
        f"[DEBUG] Prediction mean after continuity gate: "
        f"{pred.mean():.6f}"
    )

    # ========================================================
    # SED-ONLY GATE
    # ========================================================

    print("\n[DEBUG] Step 9: Applying SED-ONLY GATE...")

    sed_only = (
        (rank_sed > 0.95)
        & (rank_proto < 0.80)
        & (~fake_only)
        & (~proto_cont)
    )

    sed_only_count = np.sum(sed_only)

    print(f"[DEBUG] SED-only detections: {sed_only_count}")

    print(
        f"[DEBUG] SED-only percentage: "
        f"{(sed_only_count / sed_only.size) * 100:.4f}%"
    )

    print("[DEBUG] Updating predictions using SED-only gate...")

    pred = np.where(
        sed_only,
        (1.0 - 0.12) * pred
        + 0.12 * rank_sed,
        pred,
    )

    print("[SUCCESS] SED-only gate applied.")

    print(
        f"[DEBUG] Prediction mean after SED-only gate: "
        f"{pred.mean():.6f}"
    )

    # --------------------------------------------------------
    # Final clipping
    # --------------------------------------------------------

    print("\n[DEBUG] Step 10: Applying final clipping...")

    pred = np.clip(
        pred,
        0.0,
        1.0,
    ).astype(np.float32)

    print("[SUCCESS] Final clipping completed.")

    # --------------------------------------------------------
    # Final statistics
    # --------------------------------------------------------

    print("\n" + "-" * 55)
    print("[DEBUG] FINAL BLEND STATISTICS")
    print("-" * 55)

    print(f"[DEBUG] Final shape: {pred.shape}")
    print(f"[DEBUG] Final dtype: {pred.dtype}")
    print(f"[DEBUG] Minimum score: {pred.min():.6f}")
    print(f"[DEBUG] Maximum score: {pred.max():.6f}")
    print(f"[DEBUG] Mean score: {pred.mean():.6f}")
    print(f"[DEBUG] Standard deviation: {pred.std():.6f}")

    print(f"[DEBUG] Fake-only gate count: {fake_only_count}")
    print(f"[DEBUG] Proto continuity count: {proto_cont_count}")
    print(f"[DEBUG] SED-only gate count: {sed_only_count}")

    print("\n[SUCCESS] FINAL RANK BLEND COMPLETED.")
    print("=" * 65 + "\n")

    return pred


# ============================================================
# CLI TEST
# ============================================================

if __name__ == "__main__":

    import sys

    print("\n" + "=" * 65)
    print("[DEBUG] FINAL BLEND CLI TEST STARTED")
    print("=" * 65)

    print(f"[DEBUG] Command-line arguments: {sys.argv}")

    if len(sys.argv) != 3:

        print("[ERROR] Incorrect number of command-line arguments.")

        print("Usage:")

        print(
            "python -m app.final_blend "
            "proto.npy sed.npy"
        )

        raise SystemExit(1)

    proto_path = Path(sys.argv[1])
    sed_path = Path(sys.argv[2])

    print("\n[DEBUG] Proto file path:", proto_path)
    print("[DEBUG] SED file path:", sed_path)

    print("\n[DEBUG] Checking input files...")

    if not proto_path.exists():
        print(f"[ERROR] Proto file not found: {proto_path}")

    if not sed_path.exists():
        print(f"[ERROR] SED file not found: {sed_path}")

    print("[DEBUG] Loading Proto predictions...")

    proto = np.load(proto_path)

    print("[SUCCESS] Proto predictions loaded.")
    print("[DEBUG] Proto:", proto.shape)

    print("\n[DEBUG] Loading SED predictions...")

    sed = np.load(sed_path)

    print("[SUCCESS] SED predictions loaded.")
    print("[DEBUG] SED: ", sed.shape)

    print("\n[DEBUG] Calling final_rank_blend()...")

    final = final_rank_blend(
        proto,
        sed,
    )

    print("[SUCCESS] final_rank_blend() returned successfully.")

    print("\n[DEBUG] Final prediction summary:")

    print("Final:", final.shape)

    print("min:", final.min())

    print("max:", final.max())

    print("mean:", final.mean())

    print("\nFINAL BLEND SUCCESS")

    print("=" * 65)
