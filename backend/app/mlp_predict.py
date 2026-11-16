
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn


print("[DEBUG] Initializing MLP probes module...")

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
MLP_PATH = MODELS_DIR / "mlp_artifacts_compatible.npz"

print(f"[DEBUG] Models directory: {MODELS_DIR}")
print(f"[DEBUG] MLP artifact path: {MLP_PATH}")


class VectorizedMLPProbes(nn.Module):
    """
    Runs all trained MLP probes together using batched matrix
    multiplication.

    Architecture: 70 -> 128 -> 64 -> 1
    """

    def __init__(self, artifacts):
        super().__init__()

        print("\n[DEBUG] Initializing VectorizedMLPProbes...")
        print("[DEBUG] Registering MLP weight and bias tensors...")

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

        print("[SUCCESS] MLP tensors registered.")

        print(f"[DEBUG] W1 shape: {self.W1.shape}")
        print(f"[DEBUG] b1 shape: {self.b1.shape}")
        print(f"[DEBUG] W2 shape: {self.W2.shape}")
        print(f"[DEBUG] b2 shape: {self.b2.shape}")
        print(f"[DEBUG] W3 shape: {self.W3.shape}")
        print(f"[DEBUG] b3 shape: {self.b3.shape}")

    def forward(self, x):

        print("\n[DEBUG] VectorizedMLPProbes forward pass started.")
        print(f"[DEBUG] Input tensor shape: {x.shape}")
        print(f"[DEBUG] Input tensor dtype: {x.dtype}")

        # Layer 1: 70 -> 128
        h = torch.bmm(x, self.W1)
        print(f"[DEBUG] After Layer 1 matrix multiplication: {h.shape}")

        h = h + self.b1[:, None, :]
        h = torch.relu(h)

        print("[DEBUG] Layer 1 ReLU activation completed.")

        # Layer 2: 128 -> 64
        h = torch.bmm(h, self.W2)
        print(f"[DEBUG] After Layer 2 matrix multiplication: {h.shape}")

        h = h + self.b2[:, None, :]
        h = torch.relu(h)

        print("[DEBUG] Layer 2 ReLU activation completed.")

        # Layer 3: 64 -> 1
        h = torch.bmm(h, self.W3)
        print(f"[DEBUG] After Layer 3 matrix multiplication: {h.shape}")

        h = h + self.b3[:, None, :]

        output = h.squeeze(-1)

        print(f"[SUCCESS] MLP forward pass completed.")
        print(f"[DEBUG] Output tensor shape: {output.shape}")

        return output


def load_mlp_artifacts():
    """
    Load compatible MLP weights and preprocessing parameters.

    No sklearn pickle deserialization is required.
    """

    print("\n" + "=" * 60)
    print("[DEBUG] LOADING MLP ARTIFACTS")
    print("=" * 60)

    print(f"[DEBUG] Artifact path: {MLP_PATH}")
    print(f"[DEBUG] Artifact exists: {MLP_PATH.exists()}")

    if not MLP_PATH.exists():
        print("[ERROR] Compatible MLP artifact not found.")

        raise FileNotFoundError(
            f"Compatible MLP artifact not found: {MLP_PATH}"
        )

    print("[DEBUG] Opening MLP NPZ artifact...")

    with np.load(MLP_PATH, allow_pickle=False) as data:

        print(f"[DEBUG] Available artifact keys: {data.files}")

        artifacts = {
            key: data[key].copy()
            for key in data.files
        }

    print("[SUCCESS] MLP artifact data loaded into memory.")

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

    print("\n[DEBUG] Validating artifact keys and shapes...")

    for key, expected_shape in expected_shapes.items():

        print(f"[DEBUG] Checking artifact: {key}")

        if key not in artifacts:

            print(f"[ERROR] Missing artifact: {key}")

            raise KeyError(f"Missing MLP artifact: {key}")

        actual_shape = artifacts[key].shape

        print(f"[DEBUG] {key} shape: {actual_shape}")

        if actual_shape != expected_shape:

            print(f"[ERROR] Invalid shape for {key}.")
            print(f"[ERROR] Expected: {expected_shape}")
            print(f"[ERROR] Received: {actual_shape}")

            raise ValueError(
                f"Invalid shape for {key}: "
                f"{artifacts[key].shape}; "
                f"expected {expected_shape}"
            )

        print(f"[SUCCESS] {key} shape validated.")

    print("\n[DEBUG] Validating scaler parameters...")

    if not np.all(np.isfinite(artifacts["scaler_scale"])):

        print("[ERROR] Scaler contains non-finite values.")

        raise ValueError("Scaler contains non-finite values")

    print("[SUCCESS] Scaler values are finite.")

    if np.any(artifacts["scaler_scale"] == 0):

        print("[ERROR] Scaler contains zero scale values.")

        raise ValueError("Scaler contains zero scale values")

    print("[SUCCESS] Scaler scale values are non-zero.")

    print("\n[DEBUG] Reading alpha blend parameter...")

    artifacts["alpha_blend"] = float(
        artifacts["alpha_blend"].item()
    )

    print("[SUCCESS] MLP artifacts loaded.")

    print("  Probe models:", len(artifacts["class_ids"]))
    print("  PCA components:", artifacts["pca_components"].shape[0])
    print("  Alpha blend:", artifacts["alpha_blend"])

    print("[DEBUG] MLP artifact loading completed.")

    return artifacts


def build_sequential_features(scores_col, n_windows=12):
    """
    Build the sequential features used during MLP training.
    """

    print("\n[DEBUG] Building sequential features...")

    N = len(scores_col)

    print(f"[DEBUG] Number of scores: {N}")
    print(f"[DEBUG] Number of windows: {n_windows}")

    if N % n_windows != 0:

        print("[ERROR] Number of scores is not divisible by n_windows.")

        raise ValueError(
            f"Number of scores ({N}) must be divisible "
            f"by n_windows ({n_windows})"
        )

    print("[DEBUG] Reshaping scores into sequential windows...")

    x = scores_col.reshape(-1, n_windows)

    print(f"[DEBUG] Reshaped scores shape: {x.shape}")

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

    print("[SUCCESS] Sequential features generated.")

    print(f"[DEBUG] Previous scores shape: {prev.shape}")
    print(f"[DEBUG] Next scores shape: {next_.shape}")
    print(f"[DEBUG] Mean features shape: {mean.shape}")
    print(f"[DEBUG] Maximum features shape: {max_.shape}")
    print(f"[DEBUG] Standard deviation features shape: {std.shape}")

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

    print("\n" + "=" * 60)
    print("[DEBUG] APPLYING VECTORIZED MLP PROBES")
    print("=" * 60)

    print("[DEBUG] Reading MLP class IDs...")

    class_ids = mlp_artifacts["class_ids"].astype(np.int64)

    print(f"[DEBUG] Number of MLP classes: {len(class_ids)}")

    if len(class_ids) == 0:

        print("[WARNING] No MLP classes found.")
        print("[DEBUG] Returning original scores copy.")

        return scores_test.copy()

    print("\n[DEBUG] Converting input arrays to NumPy...")

    emb_test = np.asarray(emb_test)
    scores_test = np.asarray(scores_test)

    print(f"[DEBUG] Embeddings shape: {emb_test.shape}")
    print(f"[DEBUG] Embeddings dtype: {emb_test.dtype}")

    print(f"[DEBUG] Scores shape: {scores_test.shape}")
    print(f"[DEBUG] Scores dtype: {scores_test.dtype}")

    # ---------------------------------------------------------
    # Input validation
    # ---------------------------------------------------------

    print("\n[DEBUG] Validating embedding dimensions...")

    if emb_test.ndim != 2 or emb_test.shape[1] != 1536:

        print("[ERROR] Invalid embedding dimensions.")

        raise ValueError(
            f"Expected embeddings shape (N, 1536), "
            f"received {emb_test.shape}"
        )

    print("[SUCCESS] Embedding dimensions validated.")

    print("\n[DEBUG] Validating score dimensions...")

    if scores_test.ndim != 2:

        print("[ERROR] Scores must be a 2D array.")

        raise ValueError(
            f"Expected 2D scores, received {scores_test.shape}"
        )

    print("[SUCCESS] Score dimensions validated.")

    print("\n[DEBUG] Checking sample counts...")

    if emb_test.shape[0] != scores_test.shape[0]:

        print("[ERROR] Embedding and score sample counts do not match.")

        raise ValueError(
            "Embedding and score sample counts do not match"
        )

    print("[SUCCESS] Sample counts match.")

    N = len(scores_test)

    print(f"[DEBUG] Total samples: {N}")

    print("\n[DEBUG] Validating window grouping...")

    if N % 12 != 0:

        print("[ERROR] Number of samples is not divisible by 12.")

        raise ValueError(
            f"Expected scores in groups of 12 windows; received {N}"
        )

    print(f"[SUCCESS] Window grouping validated: {N // 12} groups.")

    print("\n[DEBUG] Validating class IDs...")

    if np.any(class_ids < 0) or np.any(class_ids >= scores_test.shape[1]):

        print("[ERROR] MLP class IDs are outside score dimensions.")

        raise ValueError("MLP class IDs are outside the score dimensions")

    print("[SUCCESS] Class IDs validated.")

    # ---------------------------------------------------------
    # StandardScaler transformation
    # ---------------------------------------------------------

    print("\n[DEBUG] Starting StandardScaler transformation...")

    scaler_mean = mlp_artifacts["scaler_mean"]
    scaler_scale = mlp_artifacts["scaler_scale"]

    print(f"[DEBUG] Scaler mean shape: {scaler_mean.shape}")
    print(f"[DEBUG] Scaler scale shape: {scaler_scale.shape}")

    # Preserve the input dtype and perform in-place operations,
    # matching sklearn's dense StandardScaler behavior.
    emb_s = np.array(emb_test, copy=True)

    print(f"[DEBUG] Embeddings copied. Shape: {emb_s.shape}")
    print(f"[DEBUG] Embeddings dtype before scaling: {emb_s.dtype}")

    emb_s -= scaler_mean
    emb_s /= scaler_scale

    print("[SUCCESS] StandardScaler transformation completed.")
    print(f"[DEBUG] Scaled embeddings shape: {emb_s.shape}")

    # ---------------------------------------------------------
    # PCA transformation
    # ---------------------------------------------------------

    print("\n[DEBUG] Starting PCA transformation...")

    pca_mean = mlp_artifacts["pca_mean"]
    pca_components = mlp_artifacts["pca_components"]

    print(f"[DEBUG] PCA mean shape: {pca_mean.shape}")
    print(f"[DEBUG] PCA components shape: {pca_components.shape}")

    Z_test = emb_s @ pca_components.T

    print(f"[DEBUG] PCA projection shape: {Z_test.shape}")

    Z_test -= pca_mean @ pca_components.T

    print("[DEBUG] PCA mean adjustment completed.")

    Z_test = Z_test.astype(np.float32, copy=False)

    print("[SUCCESS] PCA transformation completed.")
    print(f"[DEBUG] PCA output shape: {Z_test.shape}")
    print(f"[DEBUG] PCA output dtype: {Z_test.dtype}")

    # ---------------------------------------------------------
    # Raw class scores
    # ---------------------------------------------------------

    print("\n[DEBUG] Extracting raw class scores...")

    valid_classes = class_ids.tolist()

    V = len(valid_classes)

    print(f"[DEBUG] Number of valid classes: {V}")

    raw = scores_test[:, valid_classes].T

    print(f"[DEBUG] Raw class scores shape: {raw.shape}")

    raw_view = raw.reshape(
        V,
        N // 12,
        12
    )

    print(f"[DEBUG] Raw score windows shape: {raw_view.shape}")

    # ---------------------------------------------------------
    # Sequential features
    # ---------------------------------------------------------

    print("\n[DEBUG] Generating sequential features...")

    prev = np.concatenate(
        [
            raw_view[:, :, :1],
            raw_view[:, :, :-1]
        ],
        axis=2
    ).reshape(V, N)

    print(f"[DEBUG] Previous score features: {prev.shape}")

    nxt = np.concatenate(
        [
            raw_view[:, :, 1:],
            raw_view[:, :, -1:]
        ],
        axis=2
    ).reshape(V, N)

    print(f"[DEBUG] Next score features: {nxt.shape}")

    mean = np.repeat(
        raw_view.mean(axis=2),
        12,
        axis=1
    )

    print(f"[DEBUG] Mean features: {mean.shape}")

    mx = np.repeat(
        raw_view.max(axis=2),
        12,
        axis=1
    )

    print(f"[DEBUG] Maximum features: {mx.shape}")

    std = np.repeat(
        raw_view.std(axis=2),
        12,
        axis=1
    )

    print(f"[DEBUG] Standard deviation features: {std.shape}")

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

    print("[SUCCESS] Sequential features generated.")
    print(f"[DEBUG] Scalar feature tensor shape: {scalar_feats.shape}")

    # ---------------------------------------------------------
    # Combine PCA and scalar features
    # ---------------------------------------------------------

    print("\n[DEBUG] Combining PCA and scalar features...")

    Z_expanded = np.broadcast_to(
        Z_test,
        (
            V,
            N,
            Z_test.shape[1]
        )
    )

    print(f"[DEBUG] Expanded PCA shape: {Z_expanded.shape}")

    X_all = np.concatenate(
        [
            Z_expanded.astype(np.float32),
            scalar_feats,
        ],
        axis=-1
    )

    print("[SUCCESS] Feature combination completed.")
    print(f"[DEBUG] Combined input shape: {X_all.shape}")
    print(f"[DEBUG] Combined input dtype: {X_all.dtype}")

    # ---------------------------------------------------------
    # Vectorized MLP inference
    # ---------------------------------------------------------

    print("\n[DEBUG] Starting vectorized MLP inference...")

    vec_probe = VectorizedMLPProbes(mlp_artifacts)

    vec_probe.eval()

    print("[DEBUG] MLP model switched to evaluation mode.")

    print("[DEBUG] Converting combined features to PyTorch tensor...")

    input_tensor = torch.from_numpy(
        np.ascontiguousarray(X_all, dtype=np.float32)
    )

    print(f"[DEBUG] PyTorch input shape: {input_tensor.shape}")
    print(f"[DEBUG] PyTorch input dtype: {input_tensor.dtype}")

    with torch.no_grad():

        print("[DEBUG] Running MLP forward pass...")

        preds = vec_probe(input_tensor).cpu().numpy()

    print("[SUCCESS] Vectorized MLP inference completed.")

    print(f"[DEBUG] Prediction shape: {preds.shape}")
    print(f"[DEBUG] Prediction dtype: {preds.dtype}")

    # ---------------------------------------------------------
    # Blend MLP predictions with original scores
    # ---------------------------------------------------------

    print("\n[DEBUG] Starting score blending...")

    if alpha_blend is None:

        print("[DEBUG] Using alpha_blend from MLP artifacts.")

        alpha_blend = mlp_artifacts["alpha_blend"]

    print(f"[DEBUG] Alpha blend value: {alpha_blend}")

    result = scores_test.copy()

    print(f"[DEBUG] Result initialized with shape: {result.shape}")

    base_valid = scores_test[:, valid_classes]

    print(f"[DEBUG] Original valid class scores shape: {base_valid.shape}")
    print(f"[DEBUG] MLP predictions for blending shape: {preds.T.shape}")

    result[:, valid_classes] = (
        (1.0 - alpha_blend) * base_valid
        +
        alpha_blend * preds.T
    )

    print("[SUCCESS] MLP score blending completed.")

    print(f"[DEBUG] Final result shape: {result.shape}")
    print(f"[DEBUG] Final result dtype: {result.dtype}")

    print("\n" + "=" * 60)
    print("[SUCCESS] VECTORIZED MLP PROBE PIPELINE COMPLETED")
    print("=" * 60)

    return result
