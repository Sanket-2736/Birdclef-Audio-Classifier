
from pathlib import Path

import torch

from .models import LightProtoSSM, ResidualSSM


print("[DEBUG] Initializing PyTorch model loader...")

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"

print(f"[DEBUG] Base directory: {BASE_DIR}")
print(f"[DEBUG] Models directory: {MODELS_DIR}")


def load_proto_model():
    print("\n" + "=" * 60)
    print("[DEBUG] LOADING LIGHT PROTO SSM MODEL")
    print("=" * 60)

    checkpoint_path = MODELS_DIR / "proto_model.pt"

    print(f"[DEBUG] Checkpoint path: {checkpoint_path}")
    print(f"[DEBUG] Checkpoint exists: {checkpoint_path.exists()}")

    print("[DEBUG] Loading ProtoSSM checkpoint...")

    checkpoint = torch.load(
        checkpoint_path,
        map_location="cpu",
        weights_only=False
    )

    print("[SUCCESS] ProtoSSM checkpoint loaded.")
    print(f"[DEBUG] Checkpoint keys: {list(checkpoint.keys())}")

    print("\n[DEBUG] ProtoSSM configuration:")
    print(f"[DEBUG] d_input: {checkpoint['d_input']}")
    print(f"[DEBUG] d_model: {checkpoint['d_model']}")
    print(f"[DEBUG] d_state: {checkpoint['d_state']}")
    print(f"[DEBUG] n_classes: {checkpoint['n_classes']}")
    print(f"[DEBUG] n_windows: {checkpoint['n_windows']}")
    print(f"[DEBUG] dropout: {checkpoint['dropout']}")
    print(f"[DEBUG] n_sites: {checkpoint['n_sites']}")
    print(f"[DEBUG] meta_dim: {checkpoint['meta_dim']}")
    print(f"[DEBUG] use_cross_attn: {checkpoint['use_cross_attn']}")
    print(f"[DEBUG] cross_attn_heads: {checkpoint['cross_attn_heads']}")

    print("\n[DEBUG] Initializing LightProtoSSM architecture...")

    model = LightProtoSSM(
        d_input=checkpoint["d_input"],
        d_model=checkpoint["d_model"],
        d_state=checkpoint["d_state"],
        n_classes=checkpoint["n_classes"],
        n_windows=checkpoint["n_windows"],
        dropout=checkpoint["dropout"],
        n_sites=checkpoint["n_sites"],
        meta_dim=checkpoint["meta_dim"],
        use_cross_attn=checkpoint["use_cross_attn"],
        cross_attn_heads=checkpoint["cross_attn_heads"],
    )

    print("[SUCCESS] LightProtoSSM architecture initialized.")

    print("\n[DEBUG] Loading ProtoSSM state dictionary...")

    model.load_state_dict(checkpoint["state_dict"])

    print("[SUCCESS] ProtoSSM state dictionary loaded.")

    print("\n[DEBUG] Setting ProtoSSM to evaluation mode...")

    model.eval()

    print("[SUCCESS] ProtoSSM is now in evaluation mode.")

    print(f"[DEBUG] ProtoSSM parameter count: {model.count_parameters()}")

    site2i = checkpoint["site2i"]

    print(f"[DEBUG] Number of configured sites: {len(site2i)}")
    print("[SUCCESS] ProtoSSM loading completed.")

    return model, site2i


def load_residual_model():
    print("\n" + "=" * 60)
    print("[DEBUG] LOADING RESIDUAL SSM MODEL")
    print("=" * 60)

    checkpoint_path = MODELS_DIR / "residual_model.pt"

    print(f"[DEBUG] Checkpoint path: {checkpoint_path}")
    print(f"[DEBUG] Checkpoint exists: {checkpoint_path.exists()}")

    print("[DEBUG] Loading ResidualSSM checkpoint...")

    checkpoint = torch.load(
        checkpoint_path,
        map_location="cpu",
        weights_only=False
    )

    print("[SUCCESS] ResidualSSM checkpoint loaded.")
    print(f"[DEBUG] Checkpoint keys: {list(checkpoint.keys())}")

    print("\n[DEBUG] ResidualSSM configuration:")
    print(f"[DEBUG] d_input: {checkpoint['d_input']}")
    print(f"[DEBUG] d_scores: {checkpoint['d_scores']}")
    print(f"[DEBUG] d_model: {checkpoint['d_model']}")
    print(f"[DEBUG] d_state: {checkpoint['d_state']}")
    print(f"[DEBUG] n_classes: {checkpoint['n_classes']}")
    print(f"[DEBUG] n_windows: {checkpoint['n_windows']}")
    print(f"[DEBUG] dropout: {checkpoint['dropout']}")
    print(f"[DEBUG] n_sites: {checkpoint['n_sites']}")
    print(f"[DEBUG] meta_dim: {checkpoint['meta_dim']}")

    print("\n[DEBUG] Initializing ResidualSSM architecture...")

    model = ResidualSSM(
        d_input=checkpoint["d_input"],
        d_scores=checkpoint["d_scores"],
        d_model=checkpoint["d_model"],
        d_state=checkpoint["d_state"],
        n_classes=checkpoint["n_classes"],
        n_windows=checkpoint["n_windows"],
        dropout=checkpoint["dropout"],
        n_sites=checkpoint["n_sites"],
        meta_dim=checkpoint["meta_dim"],
    )

    print("[SUCCESS] ResidualSSM architecture initialized.")

    print("\n[DEBUG] Loading ResidualSSM state dictionary...")

    model.load_state_dict(checkpoint["state_dict"])

    print("[SUCCESS] ResidualSSM state dictionary loaded.")

    print("\n[DEBUG] Setting ResidualSSM to evaluation mode...")

    model.eval()

    print("[SUCCESS] ResidualSSM is now in evaluation mode.")

    correction_weight = checkpoint["correction_weight"]

    print(f"[DEBUG] ResidualSSM parameter count: {model.count_parameters()}")
    print(f"[DEBUG] Correction weight: {correction_weight}")

    print("[SUCCESS] ResidualSSM loading completed.")

    return model, correction_weight


if __name__ == "__main__":

    print("\n" + "=" * 60)
    print("[DEBUG] STARTING PYTORCH MODEL LOADING")
    print("=" * 60)

    print("\nLoading ProtoSSM...")

    proto_model, site2i = load_proto_model()

    print("\n[SUCCESS] ProtoSSM loaded successfully")
    print("  parameters:", proto_model.count_parameters())
    print("  sites:", len(site2i))

    print("\nLoading ResidualSSM...")

    residual_model, correction_weight = load_residual_model()

    print("\n[SUCCESS] ResidualSSM loaded successfully")
    print("  parameters:", residual_model.count_parameters())
    print("  correction weight:", correction_weight)

    print("\n" + "=" * 60)
    print("[SUCCESS] ALL PYTORCH MODELS LOADED SUCCESSFULLY")
    print("=" * 60)
