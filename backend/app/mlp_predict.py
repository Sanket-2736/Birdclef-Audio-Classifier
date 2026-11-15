import pickle
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn


MODELS_DIR = Path(__file__).resolve().parent.parent / "models"


class VectorizedMLPProbes(nn.Module):
    def __init__(self, probe_models):
        super().__init__()

        self.n_models = len(probe_models)

        if self.n_models == 0:
            return

        models = [probe_models[k] for k in sorted(probe_models.keys())]

        # Hidden layer 1
        self.W1 = nn.Parameter(
            torch.tensor(
                np.stack([m.coefs_[0] for m in models]),
                dtype=torch.float32
            ),
            requires_grad=False,
        )

        self.b1 = nn.Parameter(
            torch.tensor(
                np.stack([m.intercepts_[0] for m in models]),
                dtype=torch.float32
            ),
            requires_grad=False,
        )

        # Hidden layer 2
        self.W2 = nn.Parameter(
            torch.tensor(
                np.stack([m.coefs_[1] for m in models]),
                dtype=torch.float32
            ),
            requires_grad=False,
        )

        self.b2 = nn.Parameter(
            torch.tensor(
                np.stack([m.intercepts_[1] for m in models]),
                dtype=torch.float32
            ),
            requires_grad=False,
        )

        # Output layer
        self.W3 = nn.Parameter(
            torch.tensor(
                np.stack([m.coefs_[2] for m in models]),
                dtype=torch.float32
            ),
            requires_grad=False,
        )

        self.b3 = nn.Parameter(
            torch.tensor(
                np.stack([m.intercepts_[2] for m in models]),
                dtype=torch.float32
            ),
            requires_grad=False,
        )

    def forward(self, x):
        """
        x:
            (V, N, F)

        Trained MLP:
            70 -> 128 -> 64 -> 1

        Returns:
            (V, N)
        """

        # Layer 1: 70 -> 128
        h = torch.bmm(
            x,
            self.W1
        )

        h = h + self.b1[:, None, :]
        h = torch.relu(h)

        # Layer 2: 128 -> 64
        h = torch.bmm(
            h,
            self.W2
        )

        h = h + self.b2[:, None, :]
        h = torch.relu(h)

        # Layer 3: 64 -> 1
        h = torch.bmm(
            h,
            self.W3
        )

        h = h + self.b3[:, None, :]

        return h.squeeze(-1)

def build_sequential_features(scores_col, n_windows=12):
    """
    Build the exact sequential features used while training
    the MLP probes.

    Returns:
        prev
        next
        mean
        max
        std
    """

    N = len(scores_col)

    assert N % n_windows == 0

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


def load_mlp_artifacts():
    """
    Load the trained MLP probes and preprocessing artifacts.
    """

    path = MODELS_DIR / "mlp_artifacts.pkl"

    print("Loading MLP artifacts...")

    with open(path, "rb") as f:
        artifacts = pickle.load(f)

    probe_models = artifacts["probe_models"]
    scaler = artifacts["scaler"]
    pca = artifacts["pca"]
    alpha_blend = artifacts["alpha_blend"]

    print("MLP artifacts loaded")
    print(f"  Probe models: {len(probe_models)}")
    print(f"  PCA components: {pca.n_components_}")
    print(f"  Alpha blend: {alpha_blend}")

    return (
        probe_models,
        scaler,
        pca,
        alpha_blend
    )


def apply_mlp_probes_vectorized(
    emb_test,
    scores_test,
    probe_models,
    scaler,
    pca,
    alpha_blend=0.4,
):
    """
    Exact vectorized MLP inference used by the notebook.

    emb_test:
        (N, 1536)

    scores_test:
        (N, 234)

    Returns:
        (N, 234)
    """

    if len(probe_models) == 0:
        return scores_test.copy()

    # ---------------------------------------------------------
    # PCA features
    # ---------------------------------------------------------

    emb_s = scaler.transform(emb_test)

    Z_test = pca.transform(
        emb_s
    ).astype(np.float32)

    # ---------------------------------------------------------
    # Valid probe classes
    # ---------------------------------------------------------

    valid_classes = sorted(
        probe_models.keys()
    )

    V = len(valid_classes)
    N = len(scores_test)

    # ---------------------------------------------------------
    # Raw class scores
    # ---------------------------------------------------------

    raw = scores_test[:, valid_classes].T

    n_files = N // 12

    raw_view = raw.reshape(
        V,
        n_files,
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
    # Expand PCA features for every probe
    # ---------------------------------------------------------

    Z_expanded = np.broadcast_to(
        Z_test,
        (
            V,
            N,
            Z_test.shape[1]
        )
    )

    # 64 PCA + 6 scalar = 70 features
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

    vec_probe = VectorizedMLPProbes(
        probe_models
    )

    vec_probe.eval()

    with torch.no_grad():
        preds = vec_probe(
            torch.tensor(X_all)
        ).numpy()

    # ---------------------------------------------------------
    # Blend MLP predictions with original scores
    # ---------------------------------------------------------

    result = scores_test.copy()

    base_valid = scores_test[
        :,
        valid_classes
    ]

    result[
        :,
        valid_classes
    ] = (
        (1.0 - alpha_blend) * base_valid
        +
        alpha_blend * preds.T
    )

    return result