import json
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"

RESIDUAL_PATH = MODELS_DIR / "residual_model.pt"
CLASSES_PATH = MODELS_DIR / "classes.json"


# ============================================================
# CONFIG
# ============================================================

SR = 32_000
N_WINDOWS = 12
N_CLASSES = 234
EMBEDDING_DIM = 1536


# ============================================================
# SELECTIVE SSM
# ============================================================

class SelectiveSSM(nn.Module):

    def __init__(
        self,
        d_model,
        d_state=16,
        d_conv=4,
    ):
        super().__init__()

        self.d_model = d_model
        self.d_state = d_state

        self.in_proj = nn.Linear(
            d_model,
            2 * d_model,
            bias=False,
        )

        self.conv1d = nn.Conv1d(
            d_model,
            d_model,
            d_conv,
            padding=d_conv - 1,
            groups=d_model,
        )

        self.dt_proj = nn.Linear(
            d_model,
            d_model,
            bias=True,
        )

        A = torch.arange(
            1,
            d_state + 1,
            dtype=torch.float32,
        ).unsqueeze(0).expand(
            d_model,
            -1,
        )

        self.A_log = nn.Parameter(
            torch.log(A)
        )

        self.D = nn.Parameter(
            torch.ones(d_model)
        )

        self.B_proj = nn.Linear(
            d_model,
            d_state,
            bias=False,
        )

        self.C_proj = nn.Linear(
            d_model,
            d_state,
            bias=False,
        )

        self.out_proj = nn.Linear(
            d_model,
            d_model,
            bias=False,
        )

    def forward(self, x):

        B_sz, T, D = x.shape

        xz = self.in_proj(x)

        x_ssm, z = xz.chunk(
            2,
            dim=-1,
        )

        x_conv = self.conv1d(
            x_ssm.transpose(1, 2)
        )[:, :, :T].transpose(1, 2)

        x_conv = F.silu(
            x_conv
        )

        dt = F.softplus(
            self.dt_proj(x_conv)
        )

        A = -torch.exp(
            self.A_log
        )

        B = self.B_proj(
            x_conv
        )

        C = self.C_proj(
            x_conv
        )

        h = torch.zeros(
            B_sz,
            D,
            self.d_state,
            dtype=x.dtype,
            device=x.device,
        )

        ys = []

        for t in range(T):

            dA = torch.exp(
                A[None]
                * dt[:, t, :, None]
            )

            dB = (
                dt[:, t, :, None]
                * B[:, t, None, :]
            )

            h = (
                h * dA
                + x[:, t, :, None] * dB
            )

            ys.append(
                (h * C[:, t, None, :]).sum(-1)
            )

        y = torch.stack(
            ys,
            dim=1,
        )

        return (
            y
            + x * self.D[None, None, :]
        )


# ============================================================
# RESIDUAL SSM
# ============================================================

class ResidualSSM(nn.Module):

    def __init__(
        self,
        d_input=1536,
        d_scores=234,
        d_model=64,
        d_state=8,
        n_classes=234,
        n_windows=12,
        dropout=0.1,
        n_sites=20,
        meta_dim=8,
    ):
        super().__init__()

        self.n_classes = n_classes

        self.input_proj = nn.Sequential(
            nn.Linear(
                d_input + d_scores,
                d_model,
            ),
            nn.LayerNorm(d_model),
            nn.GELU(),
            nn.Dropout(dropout),
        )

        self.site_emb = nn.Embedding(
            n_sites,
            meta_dim,
        )

        self.hour_emb = nn.Embedding(
            24,
            meta_dim,
        )

        self.meta_proj = nn.Linear(
            2 * meta_dim,
            d_model,
        )

        self.pos_enc = nn.Parameter(
            torch.randn(
                1,
                n_windows,
                d_model,
            ) * 0.02
        )

        self.ssm_fwd = SelectiveSSM(
            d_model,
            d_state,
        )

        self.ssm_bwd = SelectiveSSM(
            d_model,
            d_state,
        )

        self.ssm_merge = nn.Linear(
            2 * d_model,
            d_model,
        )

        self.ssm_norm = nn.LayerNorm(
            d_model
        )

        self.ssm_drop = nn.Dropout(
            dropout
        )

        self.output_head = nn.Linear(
            d_model,
            n_classes,
        )

        # IMPORTANT:
        # Same as training notebook.
        # Residual corrections initially start at zero.
        nn.init.zeros_(
            self.output_head.weight
        )

        nn.init.zeros_(
            self.output_head.bias
        )

    def forward(
        self,
        emb,
        first_pass,
        site_ids=None,
        hours=None,
    ):

        B, T, _ = emb.shape

        x = torch.cat(
            [
                emb,
                first_pass,
            ],
            dim=-1,
        )

        h = (
            self.input_proj(x)
            + self.pos_enc[:, :T, :]
        )

        if (
            site_ids is not None
            and hours is not None
        ):

            site_ids = site_ids.clamp(
                0,
                self.site_emb.num_embeddings - 1,
            )

            hours = hours.clamp(
                0,
                23,
            )

            meta = self.meta_proj(
                torch.cat(
                    [
                        self.site_emb(site_ids),
                        self.hour_emb(hours),
                    ],
                    dim=-1,
                )
            )

            h = (
                h
                + meta.unsqueeze(1)
            )

        res = h

        h_f = self.ssm_fwd(h)

        h_b = self.ssm_bwd(
            h.flip(1)
        ).flip(1)

        h = self.ssm_drop(
            self.ssm_merge(
                torch.cat(
                    [
                        h_f,
                        h_b,
                    ],
                    dim=-1,
                )
            )
        )

        h = self.ssm_norm(
            h + res
        )

        return self.output_head(h)


# ============================================================
# LOAD MODEL
# ============================================================

print("\nLoading ResidualSSM checkpoint...")

checkpoint = torch.load(
    RESIDUAL_PATH,
    map_location="cpu",
    weights_only=False,
)

print("Residual checkpoint loaded")

print(
    "  correction weight:",
    checkpoint["correction_weight"],
)

print(
    "  n_classes:",
    checkpoint["n_classes"],
)

print(
    "  n_windows:",
    checkpoint["n_windows"],
)

print(
    "  d_input:",
    checkpoint["d_input"],
)

print(
    "  d_scores:",
    checkpoint["d_scores"],
)

print(
    "  d_model:",
    checkpoint["d_model"],
)

print(
    "  d_state:",
    checkpoint["d_state"],
)


# ============================================================
# BUILD MODEL
# ============================================================

residual_model = ResidualSSM(
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


# ============================================================
# LOAD WEIGHTS
# ============================================================

missing, unexpected = residual_model.load_state_dict(
    checkpoint["state_dict"],
    strict=True,
)

print(
    "  Missing keys:",
    len(missing),
)

print(
    "  Unexpected keys:",
    len(unexpected),
)

residual_model.eval()

CORRECTION_WEIGHT = float(
    checkpoint["correction_weight"]
)

print("ResidualSSM ready")


# ============================================================
# APPLY RESIDUAL CORRECTION
# ============================================================

def apply_residual_correction(
    embeddings,
    first_pass,
    site_id=0,
    hour_id=12,
    recording_id=None,
):
    """
    Apply trained ResidualSSM correction with performance logging.

    Parameters
    ----------
    embeddings : np.ndarray
        Shape (12, 1536)
    first_pass : np.ndarray
        Shape (12, 234)
    site_id : int
        Site ID
    hour_id : int
        Hour of day
    recording_id : str, optional
        Recording ID for logging context

    Returns
    -------
    corrected_scores : np.ndarray
        Shape (12, 234)
    residual_correction : np.ndarray
        Shape (12, 234)
    """
    from .utils import log_stage

    with log_stage("Residual Input Preparation", recording_id=recording_id):
        embeddings = np.asarray(
            embeddings,
            dtype=np.float32,
        )

        first_pass = np.asarray(
            first_pass,
            dtype=np.float32,
        )

        if embeddings.shape != (
            N_WINDOWS,
            EMBEDDING_DIM,
        ):
            raise ValueError(
                f"Unexpected embeddings shape: "
                f"{embeddings.shape}"
            )

        if first_pass.shape != (
            N_WINDOWS,
            N_CLASSES,
        ):
            raise ValueError(
                f"Unexpected first_pass shape: "
                f"{first_pass.shape}"
            )

    with log_stage("Residual Tensor Conversion", recording_id=recording_id):
        emb_tensor = torch.from_numpy(
            embeddings
        ).float().unsqueeze(0)

        first_pass_tensor = torch.from_numpy(
            first_pass
        ).float().unsqueeze(0)

        site_tensor = torch.tensor(
            [site_id],
            dtype=torch.long,
        )

        hour_tensor = torch.tensor(
            [hour_id % 24],
            dtype=torch.long,
        )

    with log_stage("ResidualSSM Forward Pass", recording_id=recording_id):
        with torch.no_grad():
            correction = residual_model(
                emb_tensor,
                first_pass_tensor,
                site_ids=site_tensor,
                hours=hour_tensor,
            )

    with log_stage("Residual Post-processing", recording_id=recording_id):
        correction = (
            correction
            .squeeze(0)
            .cpu()
            .numpy()
            .astype(np.float32)
        )

        corrected_scores = (
            first_pass
            + CORRECTION_WEIGHT * correction
        )

    return (
        corrected_scores.astype(np.float32),
        correction,
    )