from pathlib import Path

import torch

from .models import LightProtoSSM, ResidualSSM


BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"


def load_proto_model():
    checkpoint_path = MODELS_DIR / "proto_model.pt"

    checkpoint = torch.load(
        checkpoint_path,
        map_location="cpu",
        weights_only=False
    )

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

    model.load_state_dict(checkpoint["state_dict"])
    model.eval()

    return model, checkpoint["site2i"]


def load_residual_model():
    checkpoint_path = MODELS_DIR / "residual_model.pt"

    checkpoint = torch.load(
        checkpoint_path,
        map_location="cpu",
        weights_only=False
    )

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

    model.load_state_dict(checkpoint["state_dict"])
    model.eval()

    return model, checkpoint["correction_weight"]


if __name__ == "__main__":
    print("Loading ProtoSSM...")
    proto_model, site2i = load_proto_model()

    print("ProtoSSM loaded successfully")
    print("  parameters:", proto_model.count_parameters())
    print("  sites:", len(site2i))

    print()
    print("Loading ResidualSSM...")
    residual_model, correction_weight = load_residual_model()

    print("ResidualSSM loaded successfully")
    print("  parameters:", residual_model.count_parameters())
    print("  correction weight:", correction_weight)

    print()
    print("ALL PYTORCH MODELS LOADED SUCCESSFULLY")