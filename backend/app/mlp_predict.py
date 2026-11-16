
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn


MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
MLP_PATH = MODELS_DIR / "mlp_artifacts_compatible.npz"


class VectorizedMLPProbes(nn.Module):
    """
    Runs all trained MLP probes together using batched matrix
    multiplication.

    Architecture: 70 -> 128 -> 64 -> 1
    """

    def __init__(self, artifacts):
        super().__init__()

        self.register_buffer(
            "W1", torch.from_numpy(artifacts["W1"].copy())
        )
        self.register_buffer(
            "b1", torch.from_numpy(artifacts["b1"].copy())
        )
        self.register_buffer(
            "W2", torch.from_numpy(artifacts["W2"].copy())
        )
        self.register_buffer(
            "b2", torch.from_numpy(artifacts["b2"].copy())
        )
        self.register_buffer(
            "W3", torch.from_numpy(artifacts["W3"].copy())
        )
        self.register_buffer(
            "b3", torch.from_numpy(artifacts["b3"].copy())
        )

    def forward(self, x):
        # Layer 1: 70 -> 128
        h = torch.bmm(x, self.W1)
        h = h + self.b1[:, None, :]
        h = torch.relu(h)

        # Layer 2: 128 -> 64
        h = torch.bmm(h, self.W2)
        h = h + self.b2[:, None, :]
        h = torch.relu(h)

        # Layer 3: 64 -> 1
        h = torch.bmm(h, self.W3)
        h = h + self.b3[:, None, :]

        return h.squeeze(-1)


def load_mlp_artifacts():
    """
    Load compatible MLP weights and preprocessing parameters.

    No sklearn pickle deserialization is required.
    """

    print("Loading MLP artifacts...")

    if not MLP_PATH.exists():
        raise FileNotFoundError(
            f"Compatible MLP artifact not found: {MLP_PATH}"
        )

    with np.load(MLP_PATH, allow_pickle=False) as data:
        artifacts = {
            key: data[key].copy()
            for key in data.files
        }

    expected_shapes = {
        "class_ids": (58,),
        "W1": (58, 70, 128),
        "b1": (58, 128),
        "W2": (58, 128, 64),
        "b2": (58, 64),
        "W3": (58, 64, 1),
        "b3": (58, 1),
        "scaler_mean": (1536,),
        "scaler_scale": (1536,),
        "pca_mean": (1536,),
        "pca_components": (64, 1536),
    }

    for key, expected_shape in expected_shapes.items():
        if key not in artifacts:
            raise KeyError(f"Missing MLP artifact: {key}")

        if artifacts[key].shape != expected_shape:
            raise ValueError(
                f"Invalid shape for {key}: "
                f"{artifacts[key].shape}; "
                f"expected {expected_shape}"
            )

    if not np.all(np.isfinite(artifacts["scaler_scale"])):
        raise ValueError("Scaler contains non-finite values")

    if np.any(artifacts["scaler_scale"] == 0):
        raise ValueError("Scaler contains zero scale values")

    artifacts["alpha_blend"] = float(
        artifacts["alpha_blend"].item()
    )

    print("MLP artifacts loaded")
    print("  Probe models:", len(artifacts["class_ids"]))
    print("  PCA components:", artifacts["pca_components"].shape[0])
    print("  Alpha blend:", artifacts["alpha_blend"])

    return artifacts


def build_sequential_features(scores_col, n_windows=12):
    """
    Build the sequential features used during MLP training.
    """

    N = len(scores_col)

    if N % n_windows != 0:
        raise ValueError(
            f"Number of scores ({N}) must be divisible "
            f"by n_windows ({n_windows})"
        )

    x = scores_col.reshape(-1, n_windows)

    prev = np.concatenate(
        [x[:, :1], x[:, :-1]],
        axis=1
    )

    next_ = np.concatenate(
        [x[:, 1:], x[:, -1:]],
        axis=1
    )

    mean = np.repeat(
        x.mean(axis=1),
        n_windows
    )

    max_ = np.repeat(
        x.max(axis=1),
        n_windows
    )

    std = np.repeat(
        x.std(axis=1),
        n_windows
    )

    return (
        prev.reshape(-1),
        next_.reshape(-1),
        mean,
        max_,
        std
    )


def apply_mlp_probes_vectorized(
    emb_test,
    scores_test,
    mlp_artifacts,
    alpha_blend=None,
):
    """
    Apply the 58 trained MLP probes using compatible NumPy
    artifacts and vectorized PyTorch inference.

    emb_test:
        (N, 1536)

    scores_test:
        (N, 234)

    Returns:
        (N, 234)
    """

    class_ids = mlp_artifacts["class_ids"].astype(np.int64)

    if len(class_ids) == 0:
        return scores_test.copy()

    emb_test = np.asarray(emb_test)
    scores_test = np.asarray(scores_test)

    if emb_test.ndim != 2 or emb_test.shape[1] != 1536:
        raise ValueError(
            f"Expected embeddings shape (N, 1536), "
            f"received {emb_test.shape}"
        )

    if scores_test.ndim != 2:
        raise ValueError(
            f"Expected 2D scores, received {scores_test.shape}"
        )

    if emb_test.shape[0] != scores_test.shape[0]:
        raise ValueError(
            "Embedding and score sample counts do not match"
        )

    N = len(scores_test)

    if N % 12 != 0:
        raise ValueError(
            f"Expected scores in groups of 12 windows; received {N}"
        )

    if np.any(class_ids < 0) or np.any(class_ids >= scores_test.shape[1]):
        raise ValueError("MLP class IDs are outside the score dimensions")

    # ---------------------------------------------------------
    # StandardScaler transformation
    # ---------------------------------------------------------

    scaler_mean = mlp_artifacts["scaler_mean"]
    scaler_scale = mlp_artifacts["scaler_scale"]

    # Preserve the input dtype and perform in-place operations,
    # matching sklearn's dense StandardScaler behavior.
    emb_s = np.array(emb_test, copy=True)

    emb_s -= scaler_mean
    emb_s /= scaler_scale

    # ---------------------------------------------------------
    # PCA transformation
    # ---------------------------------------------------------

    pca_mean = mlp_artifacts["pca_mean"]
    pca_components = mlp_artifacts["pca_components"]

    Z_test = emb_s @ pca_components.T
    Z_test -= pca_mean @ pca_components.T

    Z_test = Z_test.astype(np.float32, copy=False)

    # ---------------------------------------------------------
    # Raw class scores
    # ---------------------------------------------------------

    valid_classes = class_ids.tolist()

    V = len(valid_classes)

    raw = scores_test[:, valid_classes].T

    raw_view = raw.reshape(
        V,
        N // 12,
        12
    )

    # ---------------------------------------------------------
    # Sequential features
    # ---------------------------------------------------------

    prev = np.concatenate(
        [
            raw_view[:, :, :1],
            raw_view[:, :, :-1]
        ],
        axis=2
    ).reshape(V, N)

    nxt = np.concatenate(
        [
            raw_view[:, :, 1:],
            raw_view[:, :, -1:]
        ],
        axis=2
    ).reshape(V, N)

    mean = np.repeat(
        raw_view.mean(axis=2),
        12,
        axis=1
    )

    mx = np.repeat(
        raw_view.max(axis=2),
        12,
        axis=1
    )

    std = np.repeat(
        raw_view.std(axis=2),
        12,
        axis=1
    )

    scalar_feats = np.stack(
        [
            raw,
            prev,
            nxt,
            mean,
            mx,
            std,
        ],
        axis=-1
    ).astype(np.float32)

    # ---------------------------------------------------------
    # Combine PCA and scalar features
    # ---------------------------------------------------------

    Z_expanded = np.broadcast_to(
        Z_test,
        (
            V,
            N,
            Z_test.shape[1]
        )
    )

    X_all = np.concatenate(
        [
            Z_expanded.astype(np.float32),
            scalar_feats,
        ],
        axis=-1
    )

    # ---------------------------------------------------------
    # Vectorized MLP inference
    # ---------------------------------------------------------

    vec_probe = VectorizedMLPProbes(mlp_artifacts)
    vec_probe.eval()

    with torch.no_grad():
        preds = vec_probe(
            torch.from_numpy(
                np.ascontiguousarray(X_all, dtype=np.float32)
            )
        ).cpu().numpy()

    # ---------------------------------------------------------
    # Blend MLP predictions with original scores
    # ---------------------------------------------------------

    if alpha_blend is None:
        alpha_blend = mlp_artifacts["alpha_blend"]

    result = scores_test.copy()

    base_valid = scores_test[:, valid_classes]

    result[:, valid_classes] = (
        (1.0 - alpha_blend) * base_valid
        +
        alpha_blend * preds.T
    )

    return result
