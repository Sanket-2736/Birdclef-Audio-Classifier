from pathlib import Path
import json
import pickle
import numpy as np
import torch


BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS = BASE_DIR / "artifacts"


print("Loading artifacts...\n")


# ------------------------------------------------------------
# Classes
# ------------------------------------------------------------

with open(ARTIFACTS / "classes.json", "r") as f:
    classes = json.load(f)

print("✓ classes.json")
print("  Number of classes:", len(classes))


# ------------------------------------------------------------
# MLP
# ------------------------------------------------------------

with open(ARTIFACTS / "mlp_artifacts.pkl", "rb") as f:
    mlp = pickle.load(f)

print("✓ mlp_artifacts.pkl")

print("  Keys:", mlp.keys())


# ------------------------------------------------------------
# Perch mapping
# ------------------------------------------------------------

with open(ARTIFACTS / "perch_mapping.pkl", "rb") as f:
    perch_mapping = pickle.load(f)

print("✓ perch_mapping.pkl")

print("  Keys:", perch_mapping.keys())


# ------------------------------------------------------------
# Prior tables
# ------------------------------------------------------------

with open(ARTIFACTS / "prior_tables.pkl", "rb") as f:
    prior_tables = pickle.load(f)

print("✓ prior_tables.pkl")


# ------------------------------------------------------------
# Temperatures
# ------------------------------------------------------------

temperatures = np.load(
    ARTIFACTS / "temperatures.npy"
)

print("✓ temperatures.npy")
print("  Shape:", temperatures.shape)


# ------------------------------------------------------------
# Thresholds
# ------------------------------------------------------------

thresholds = np.load(
    ARTIFACTS / "per_class_thresholds.npy"
)

print("✓ per_class_thresholds.npy")
print("  Shape:", thresholds.shape)


# ------------------------------------------------------------
# Config
# ------------------------------------------------------------

with open(ARTIFACTS / "config.json", "r") as f:
    config = json.load(f)

print("✓ config.json")
print("  Config:", config)


# ------------------------------------------------------------
# ProtoSSM checkpoint
# ------------------------------------------------------------

proto_checkpoint = torch.load(
    ARTIFACTS / "proto_model.pt",
    map_location="cpu",
    weights_only=False,
)

print("✓ proto_model.pt")

print(
    "  Checkpoint keys:",
    proto_checkpoint.keys()
)


# ------------------------------------------------------------
# ResidualSSM checkpoint
# ------------------------------------------------------------

residual_checkpoint = torch.load(
    ARTIFACTS / "residual_model.pt",
    map_location="cpu",
    weights_only=False,
)

print("✓ residual_model.pt")

print(
    "  Checkpoint keys:",
    residual_checkpoint.keys()
)


print("\n================================")
print("ALL ARTIFACTS LOADED SUCCESSFULLY")
print("================================")