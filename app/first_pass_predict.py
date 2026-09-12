from pathlib import Path
import json
import pickle
import sys

import numpy as np
import torch

from .perch import PerchModel
from .proto_predict import LightProtoSSM
from .mlp_predict import apply_mlp_probes_vectorized

from .perch import PerchModel
from .proto_predict import LightProtoSSM
from .mlp_predict import apply_mlp_probes_vectorized
from .residual_predict import apply_residual_correction
from .postprocess import postprocess_proto_scores


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"

PROTO_PATH = MODELS_DIR / "proto_model.pt"
MLP_PATH = MODELS_DIR / "mlp_artifacts.pkl"
PRIOR_PATH = MODELS_DIR / "prior_tables.pkl"
CLASSES_PATH = MODELS_DIR / "classes.json"


# ============================================================
# CONFIG
# ============================================================

SR = 32000
WINDOW_SEC = 5
WINDOW_SAMPLES = 160000
FILE_SAMPLES = 60 * SR

N_WINDOWS = 12
N_CLASSES = 234
EMBEDDING_DIM = 1536

ENSEMBLE_WEIGHT = 0.5
LAMBDA_PRIOR = 0.4

TTA_SHIFTS = [0, 1, -1, 2, -2]


# ============================================================
# LOAD CLASSES
# ============================================================

print("Loading classes...")

with open(CLASSES_PATH, "r") as f:
    classes = json.load(f)

print("  Number of classes:", len(classes))


# ============================================================
# LOAD PRIOR TABLES
# ============================================================

print("\nLoading prior tables...")

with open(PRIOR_PATH, "rb") as f:
    prior_tables = pickle.load(f)

print("Prior tables loaded")


# ============================================================
# LOAD MLP ARTIFACTS
# ============================================================

print("\nLoading MLP artifacts...")

with open(MLP_PATH, "rb") as f:
    mlp_artifacts = pickle.load(f)

probe_models = mlp_artifacts["probe_models"]
mlp_scaler = mlp_artifacts["scaler"]
mlp_pca = mlp_artifacts["pca"]
mlp_alpha = mlp_artifacts["alpha_blend"]

print("MLP artifacts loaded")
print("  probe models:", len(probe_models))
print("  PCA components:", mlp_pca.n_components)
print("  alpha blend:", mlp_alpha)

from pathlib import Path
import json
import pickle
import sys

import numpy as np
import torch

from .perch import PerchModel
from .proto_predict import LightProtoSSM
from .mlp_predict import apply_mlp_probes_vectorized


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"


# ============================================================
# CONFIG
# ============================================================

SR = 32000
WINDOW_SEC = 5
WINDOW_SAMPLES = 160000
FILE_SAMPLES = 60 * SR
N_WINDOWS = 12
N_CLASSES = 234
EMBEDDING_DIM = 1536

ENSEMBLE_WEIGHT = 0.5
LAMBDA_PRIOR = 0.4

TTA_SHIFTS = [0, 1, -1, 2, -2]


# ============================================================
# LOAD PRIOR TABLES
# ============================================================

print("Loading prior tables...")

with open(MODELS_DIR / "prior_tables.pkl", "rb") as f:
    prior_tables = pickle.load(f)

print("Prior tables loaded")


# ============================================================
# LOAD MLP ARTIFACTS
# ============================================================

print("\nLoading MLP artifacts...")

with open(MLP_PATH, "rb") as f:
    mlp_artifacts = pickle.load(f)

probe_models = mlp_artifacts["probe_models"]
mlp_scaler = mlp_artifacts["scaler"]
mlp_pca = mlp_artifacts["pca"]
mlp_alpha = mlp_artifacts["alpha_blend"]

print("MLP artifacts loaded")
print("  probe models:", len(probe_models))
print("  PCA components:", mlp_pca.n_components)
print("  alpha blend:", mlp_alpha)


# ============================================================
# LOAD PRIOR TABLES
# ============================================================

print("\nLoading prior tables...")

with open(PRIOR_PATH, "rb") as f:
    prior_tables = pickle.load(f)

print("Prior tables loaded")

if isinstance(prior_tables, dict):
    print("  keys:", list(prior_tables.keys()))
else:
    print("  type:", type(prior_tables))


# ============================================================
# PRIOR APPLICATION
# ============================================================

def apply_prior(
    scores,
    sites,
    hours,
    tables,
    lambda_prior=0.4,
):
    """
    Exact notebook prior implementation.

    Adds a scaled prior logit to raw Perch scores.
    """

    eps = 1e-4
    n = len(scores)

    out = scores.copy()

    # Start from global average
    p = np.tile(
        tables["global_p"],
        (n, 1)
    )

    # Override with hour-level estimate
    for i, h in enumerate(hours):
        h = int(h)

        if h in tables["hour_to_i"]:
            j = tables["hour_to_i"][h]
            nh = tables["hour_n"][j]

            # Shrink toward global if little data
            w = nh / (nh + 8.0)

            p[i] = (
                w * tables["hour_p"][j]
                + (1.0 - w) * tables["global_p"]
            )

    # Override with site-level estimate
    for i, s in enumerate(sites):
        s = str(s)

        if s in tables["site_to_i"]:
            j = tables["site_to_i"][s]
            ns = tables["site_n"][j]

            # Shrink toward current prior
            w = ns / (ns + 8.0)

            p[i] = (
                w * tables["site_p"][j]
                + (1.0 - w) * p[i]
            )

    # Convert prior probability to logit
    p = np.clip(
        p,
        eps,
        1.0 - eps
    )

    logit_prior = (
        np.log(p)
        - np.log1p(-p)
    )

    # Add scaled prior to raw Perch logits
    out += lambda_prior * logit_prior

    return out.astype(np.float32)
# ============================================================
# TTA WINDOW SHIFT
# ============================================================

def shift_windows(embeddings, scores, shift):
    """
    Shift the 12-window sequence circularly.

    The model sees the shifted sequence and the output is
    shifted back to the original window positions.
    """

    if shift == 0:
        return embeddings, scores

    emb_shifted = np.roll(
        embeddings,
        shift,
        axis=0
    )

    scores_shifted = np.roll(
        scores,
        shift,
        axis=0
    )

    return emb_shifted, scores_shifted


# ============================================================
# PROTOSSM TTA
# ============================================================

def run_tta_proto(
    model,
    embeddings,
    perch_scores,
    site_ids,
    hour_ids,
):
    """
    Run ProtoSSM using the notebook TTA shifts:
        [0, 1, -1, 2, -2]

    Returns:
        (12, 234)
    """

    all_outputs = []

    for shift in TTA_SHIFTS:

        emb_shifted, scores_shifted = shift_windows(
            embeddings,
            perch_scores,
            shift
        )

        emb_tensor = torch.from_numpy(
            emb_shifted
        ).float().unsqueeze(0)

        scores_tensor = torch.from_numpy(
            scores_shifted
        ).float().unsqueeze(0)

        with torch.no_grad():

            output = model(
                emb_tensor,
                perch_logits=scores_tensor,
                site_ids=site_ids,
                hours=hour_ids
            )

        output = (
            output
            .squeeze(0)
            .cpu()
            .numpy()
        )

        # Undo the input shift so each prediction corresponds
        # to the original window position.
        if shift != 0:

            output = np.roll(
                output,
                -shift,
                axis=0
            )

        all_outputs.append(output)

    return np.mean(
        np.stack(all_outputs, axis=0),
        axis=0
    ).astype(np.float32)


# ============================================================
# LOAD PROTOSSM
# ============================================================

print("\nLoading ProtoSSM checkpoint...")

proto_checkpoint = torch.load(
    PROTO_PATH,
    map_location="cpu",
    weights_only=False
)

proto_model = LightProtoSSM(
    d_input=proto_checkpoint["d_input"],
    d_model=proto_checkpoint["d_model"],
    d_state=proto_checkpoint["d_state"],
    n_classes=proto_checkpoint["n_classes"],
    n_windows=proto_checkpoint["n_windows"],
    dropout=proto_checkpoint["dropout"],
    n_sites=proto_checkpoint["n_sites"],
    meta_dim=proto_checkpoint["meta_dim"],
    use_cross_attn=proto_checkpoint["use_cross_attn"],
    cross_attn_heads=proto_checkpoint["cross_attn_heads"],
)

missing, unexpected = proto_model.load_state_dict(
    proto_checkpoint["state_dict"],
    strict=True
)

print("ProtoSSM loaded")
print("  Missing keys:", len(missing))
print("  Unexpected keys:", len(unexpected))

proto_model.eval()


# ============================================================
# FIRST-PASS PIPELINE
# ============================================================

def predict_first_pass(
    audio_path,
    site_id=0,
    hour_id=12,
):
    """
    Complete first-pass pipeline:

        Audio
          ↓
        Perch
          ↓
        Prior adjustment
          ↓
        MLP probes
          ↓
        ProtoSSM TTA
          ↓
        0.5 Proto + 0.5 adjusted Perch

    Returns:
        dict
    """

    print("\n" + "=" * 60)
    print("FIRST-PASS PIPELINE")
    print("=" * 60)

    print("\nAudio:")
    print(audio_path)

    # --------------------------------------------------------
    # PERCH
    # --------------------------------------------------------

    print("\nRunning Perch...")

    perch = PerchModel()

    perch_result = perch.predict(
        audio_path
    )

    embeddings = np.asarray(
        perch_result["embeddings"],
        dtype=np.float32
    )

    perch_scores = np.asarray(
        perch_result["scores"],
        dtype=np.float32
    )

    if embeddings.shape != (
        N_WINDOWS,
        EMBEDDING_DIM
    ):
        raise ValueError(
            f"Unexpected embeddings shape: "
            f"{embeddings.shape}"
        )

    if perch_scores.shape != (
        N_WINDOWS,
        N_CLASSES
    ):
        raise ValueError(
            f"Unexpected Perch scores shape: "
            f"{perch_scores.shape}"
        )

    print("Perch:")
    print("  embeddings:", embeddings.shape)
    print("  scores:", perch_scores.shape)

    # --------------------------------------------------------
    # PRIOR
    # --------------------------------------------------------

    print("\nApplying prior adjustment...")

    adjusted_scores = apply_prior(
        perch_scores,
        sites=np.array(
            [site_id] * N_WINDOWS
        ),
        hours=np.array(
            [hour_id] * N_WINDOWS
        ),
        tables=prior_tables,
        lambda_prior=LAMBDA_PRIOR,
    )

    print(
        "  adjusted scores:",
        adjusted_scores.shape
    )

    # --------------------------------------------------------
    # MLP
    # --------------------------------------------------------

    print("\nRunning MLP probes...")

    mlp_scores = apply_mlp_probes_vectorized(
        embeddings,
        adjusted_scores,
        probe_models,
        mlp_scaler,
        mlp_pca,
        alpha_blend=mlp_alpha
    )

    print(
        "  MLP output:",
        mlp_scores.shape
    )

    # --------------------------------------------------------
    # METADATA
    # --------------------------------------------------------

    site_ids = torch.tensor(
        [site_id],
        dtype=torch.long
    )

    hour_ids = torch.tensor(
        [hour_id % 24],
        dtype=torch.long
    )

    # --------------------------------------------------------
    # PROTOSSM TTA
    # --------------------------------------------------------

    print(
        "\nRunning ProtoSSM TTA..."
    )

    proto_scores = run_tta_proto(
        proto_model,
        embeddings,
        perch_scores,
        site_ids,
        hour_ids
    )

    print(
        "  ProtoSSM output:",
        proto_scores.shape
    )

    # --------------------------------------------------------
    # FINAL FIRST PASS
    # --------------------------------------------------------

    first_pass = (
        ENSEMBLE_WEIGHT * proto_scores
        + (1.0 - ENSEMBLE_WEIGHT) * mlp_scores
    )

    first_pass = np.asarray(
        first_pass,
        dtype=np.float32
    )

    print("\nFirst-pass output:")
    print("  shape:", first_pass.shape)
    print("  min:", first_pass.min())
    print("  max:", first_pass.max())
    print("  mean:", first_pass.mean())

    # --------------------------------------------------------
    # RESIDUAL SSM
    # --------------------------------------------------------

    print("\nRunning ResidualSSM...")

    corrected_scores, residual_correction = (
        apply_residual_correction(
            embeddings=embeddings,
            first_pass=first_pass,
            site_id=site_id,
            hour_id=hour_id,
        )
    )

    print(
        "  residual correction:",
        residual_correction.shape
    )

    print(
        "  corrected scores:",
        corrected_scores.shape
    )

    print(
        "  correction min:",
        residual_correction.min()
    )

    print(
        "  correction max:",
        residual_correction.max()
    )

    print(
        "  corrected min:",
        corrected_scores.min()
    )

    print(
        "  corrected max:",
        corrected_scores.max()
    )

    # --------------------------------------------------------
    # POST-PROCESSING
    # --------------------------------------------------------

    print("\nRunning Proto post-processing...")

    proto_probs = postprocess_proto_scores(
        corrected_scores
    )

    print(
        "  Proto probabilities:",
        proto_probs.shape
    )

    print(
        "  probability min:",
        proto_probs.min()
    )

    print(
        "  probability max:",
        proto_probs.max()
    )

    print(
        "  probability mean:",
        proto_probs.mean()
    )

    # --------------------------------------------------------
    # TOP CLASSES
    # --------------------------------------------------------

    print("\nTop classes per window:")

    for window_idx in range(N_WINDOWS):

        top_indices = np.argsort(
            first_pass[window_idx]
        )[-5:][::-1]

        print(
            f"\nWindow {window_idx + 1}:"
        )

        for class_idx in top_indices:

            print(
                f"  {classes[class_idx]} "
                f"(class {class_idx}): "
                f"{first_pass[window_idx, class_idx]:.4f}"
            )

    print("\n" + "=" * 60)
    print("SUCCESS")
    print("=" * 60)

    return {
        "embeddings": embeddings,
        "perch_scores": perch_scores,
        "adjusted_scores": adjusted_scores,
        "mlp_scores": mlp_scores,
        "proto_scores": proto_scores,
        "first_pass": first_pass,
        "residual_correction": residual_correction,
        "corrected_scores": corrected_scores,
        "proto_probs": proto_probs,
    }


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":

    if len(sys.argv) != 2:

        print(
            "\nUsage:"
        )

        print(
            "  python -m app.first_pass_predict "
            "<path-to-audio>"
        )

        print(
            "\nExample:"
        )

        print(
            "  python -m app.first_pass_predict test.ogg"
        )

        raise SystemExit(1)

    audio_path = sys.argv[1]

    predict_first_pass(
        audio_path
    )