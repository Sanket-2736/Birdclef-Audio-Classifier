import pickle
import numpy as np
from pathlib import Path

path = Path("models/mlp_artifacts.pkl")

with open(path, "rb") as f:
    artifacts = pickle.load(f)

probe_models = artifacts["probe_models"]
scaler = artifacts["scaler"]
pca = artifacts["pca"]

class_ids = np.array(sorted(probe_models.keys()), dtype=np.int64)
models = [probe_models[int(k)] for k in class_ids]

print("Number of fitted probes:", len(models))

# Extract the trained MLP weights
W1 = np.stack([m.coefs_[0] for m in models]).astype(np.float32)
b1 = np.stack([m.intercepts_[0] for m in models]).astype(np.float32)

W2 = np.stack([m.coefs_[1] for m in models]).astype(np.float32)
b2 = np.stack([m.intercepts_[1] for m in models]).astype(np.float32)

W3 = np.stack([m.coefs_[2] for m in models]).astype(np.float32)
b3 = np.stack([m.intercepts_[2] for m in models]).astype(np.float32)

# Export preprocessing parameters
np.savez_compressed(
    "models/mlp_artifacts_compatible.npz",
    class_ids=class_ids,
    W1=W1, b1=b1,
    W2=W2, b2=b2,
    W3=W3, b3=b3,
    scaler_mean=scaler.mean_.astype(np.float64),
    scaler_scale=scaler.scale_.astype(np.float64),
    pca_mean=pca.mean_.astype(np.float32),
    pca_components=pca.components_.astype(np.float32),
    alpha_blend=np.array(artifacts["alpha_blend"], dtype=np.float32)
)

print("\nExport successful!")
print("Class IDs:", class_ids.shape)
print("W1:", W1.shape)
print("W2:", W2.shape)
print("W3:", W3.shape)
print("Scaler:", scaler.mean_.shape)
print("PCA:", pca.components_.shape)
print("Alpha:", artifacts["alpha_blend"])
print("Saved: models/mlp_artifacts_compatible.npz")

