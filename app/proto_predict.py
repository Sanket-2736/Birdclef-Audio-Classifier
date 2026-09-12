import json
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

import sys

from .perch import PerchModel

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = BASE_DIR / "models"

PROTO_PATH = ARTIFACTS_DIR / "proto_model.pt"
CLASSES_PATH = ARTIFACTS_DIR / "classes.json"

# ============================================================
# CONSTANTS
# ============================================================

SR = 32_000
WINDOW_SEC = 5
WINDOW_SAMPLES = SR * WINDOW_SEC
FILE_SAMPLES = 60 * SR
N_WINDOWS = 12
N_CLASSES = 234
EMBEDDING_DIM = 1536


# ============================================================
# SELECTIVE SSM
# EXACT NOTEBOOK ARCHITECTURE
# ============================================================

class SelectiveSSM(nn.Module):
    def __init__(self, d_model, d_state=16, d_conv=4):
        super().__init__()

        self.d_model = d_model
        self.d_state = d_state

        self.in_proj = nn.Linear(
            d_model,
            2 * d_model,
            bias=False
        )

        self.conv1d = nn.Conv1d(
            d_model,
            d_model,
            d_conv,
            padding=d_conv - 1,
            groups=d_model
        )

        self.dt_proj = nn.Linear(
            d_model,
            d_model,
            bias=True
        )

        A = (
            torch.arange(
                1,
                d_state + 1,
                dtype=torch.float32
            )
            .unsqueeze(0)
            .expand(d_model, -1)
        )

        self.A_log = nn.Parameter(torch.log(A))

        self.D = nn.Parameter(
            torch.ones(d_model)
        )

        self.B_proj = nn.Linear(
            d_model,
            d_state,
            bias=False
        )

        self.C_proj = nn.Linear(
            d_model,
            d_state,
            bias=False
        )

        self.out_proj = nn.Linear(
            d_model,
            d_model,
            bias=False
        )

    def forward(self, x):

        B_sz, T, D = x.shape

        xz = self.in_proj(x)

        x_ssm, z = xz.chunk(
            2,
            dim=-1
        )

        x_conv = self.conv1d(
            x_ssm.transpose(1, 2)
        )[:, :, :T].transpose(1, 2)

        x_conv = F.silu(x_conv)

        dt = F.softplus(
            self.dt_proj(x_conv)
        )

        A = -torch.exp(self.A_log)

        B = self.B_proj(x_conv)
        C = self.C_proj(x_conv)

        h = torch.zeros(
            B_sz,
            D,
            self.d_state,
            device=x.device,
            dtype=x.dtype
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
            dim=1
        )

        return (
            y
            + x * self.D[None, None, :]
        )


# ============================================================
# LIGHT PROTO SSM
# EXACT NOTEBOOK ARCHITECTURE
# ============================================================

class LightProtoSSM(nn.Module):

    def __init__(
        self,
        d_input=1536,
        d_model=128,
        d_state=16,
        n_classes=234,
        n_windows=12,
        dropout=0.15,
        n_sites=20,
        meta_dim=16,
        use_cross_attn=True,
        cross_attn_heads=2
    ):

        super().__init__()

        self.n_classes = n_classes
        self.n_windows = n_windows
        self.use_cross_attn = use_cross_attn

        # ----------------------------------------------------
        # Input projection
        # ----------------------------------------------------

        self.input_proj = nn.Sequential(
            nn.Linear(
                d_input,
                d_model
            ),
            nn.LayerNorm(d_model),
            nn.GELU(),
            nn.Dropout(dropout)
        )

        # ----------------------------------------------------
        # Positional encoding
        # ----------------------------------------------------

        self.pos_enc = nn.Parameter(
            torch.randn(
                1,
                n_windows,
                d_model
            ) * 0.02
        )

        # ----------------------------------------------------
        # Metadata embeddings
        # ----------------------------------------------------

        self.site_emb = nn.Embedding(
            n_sites,
            meta_dim
        )

        self.hour_emb = nn.Embedding(
            24,
            meta_dim
        )

        self.meta_proj = nn.Linear(
            2 * meta_dim,
            d_model
        )

        # ----------------------------------------------------
        # Two bidirectional SSM blocks
        # ----------------------------------------------------

        self.ssm_fwd = nn.ModuleList([
            SelectiveSSM(
                d_model,
                d_state
            )
            for _ in range(2)
        ])

        self.ssm_bwd = nn.ModuleList([
            SelectiveSSM(
                d_model,
                d_state
            )
            for _ in range(2)
        ])

        self.ssm_merge = nn.ModuleList([
            nn.Linear(
                2 * d_model,
                d_model
            )
            for _ in range(2)
        ])

        self.ssm_norm = nn.ModuleList([
            nn.LayerNorm(d_model)
            for _ in range(2)
        ])

        self.drop = nn.Dropout(dropout)

        # ----------------------------------------------------
        # Cross attention
        # ----------------------------------------------------

        if use_cross_attn:

            self.cross_attn = nn.ModuleList([
                nn.MultiheadAttention(
                    d_model,
                    num_heads=cross_attn_heads,
                    dropout=dropout,
                    batch_first=True
                )
                for _ in range(2)
            ])

            self.cross_norm = nn.ModuleList([
                nn.LayerNorm(d_model)
                for _ in range(2)
            ])

        # ----------------------------------------------------
        # Prototype parameters
        # ----------------------------------------------------

        self.prototypes = nn.Parameter(
            torch.randn(
                n_classes,
                d_model
            ) * 0.02
        )

        self.proto_temp = nn.Parameter(
            torch.tensor(5.0)
        )

        self.class_bias = nn.Parameter(
            torch.zeros(n_classes)
        )

        self.fusion_alpha = nn.Parameter(
            torch.zeros(n_classes)
        )

    # ========================================================
    # FORWARD
    # ========================================================

    def forward(
        self,
        emb,
        perch_logits=None,
        site_ids=None,
        hours=None
    ):

        B, T, _ = emb.shape

        # Input projection + positional encoding
        h = (
            self.input_proj(emb)
            + self.pos_enc[:, :T, :]
        )

        # Metadata
        if (
            site_ids is not None
            and hours is not None
        ):

            meta = self.meta_proj(
                torch.cat(
                    [
                        self.site_emb(site_ids),
                        self.hour_emb(hours)
                    ],
                    dim=-1
                )
            )

            h = h + meta[:, None, :]

        # ----------------------------------------------------
        # SSM blocks
        # ----------------------------------------------------

        for i, (
            fwd,
            bwd,
            merge,
            norm
        ) in enumerate(
            zip(
                self.ssm_fwd,
                self.ssm_bwd,
                self.ssm_merge,
                self.ssm_norm
            )
        ):

            res = h

            h_f = fwd(h)

            h_b = bwd(
                h.flip(1)
            ).flip(1)

            h = self.drop(
                merge(
                    torch.cat(
                        [
                            h_f,
                            h_b
                        ],
                        dim=-1
                    )
                )
            )

            h = norm(
                h + res
            )

            # ------------------------------------------------
            # Cross attention
            # ------------------------------------------------

            if self.use_cross_attn:

                attn_out, _ = self.cross_attn[i](
                    h,
                    h,
                    h
                )

                h = self.cross_norm[i](
                    h + attn_out
                )

        # ----------------------------------------------------
        # Prototype similarity
        # ----------------------------------------------------

        h_n = F.normalize(
            h,
            dim=-1
        )

        p_n = F.normalize(
            self.prototypes,
            dim=-1
        )

        sim = (
            torch.matmul(
                h_n,
                p_n.T
            )
            * F.softplus(
                self.proto_temp
            )
            + self.class_bias[
                None,
                None,
                :
            ]
        )

        # ----------------------------------------------------
        # Fuse with Perch logits
        # ----------------------------------------------------

        if perch_logits is not None:

            alpha = torch.sigmoid(
                self.fusion_alpha
            )[None, None, :]

            out = (
                alpha * sim
                + (1 - alpha) * perch_logits
            )

        else:

            out = sim

        return out


# ============================================================
# LOAD CLASSES
# ============================================================

print("Loading classes...")

with open(
    CLASSES_PATH,
    "r",
    encoding="utf-8"
) as f:

    classes = json.load(f)

print(
    f"  Number of classes: {len(classes)}"
)


# ============================================================
# LOAD PROTO CHECKPOINT
# ============================================================

print("\nLoading ProtoSSM checkpoint...")

checkpoint = torch.load(
    PROTO_PATH,
    map_location="cpu",
    weights_only=False
)

print("Proto checkpoint loaded")

print(
    "  export type:",
    checkpoint.get(
        "export_type",
        "unknown"
    )
)

print(
    "  n_classes:",
    checkpoint["n_classes"]
)

print(
    "  n_windows:",
    checkpoint["n_windows"]
)

print(
    "  d_input:",
    checkpoint["d_input"]
)

print(
    "  d_model:",
    checkpoint["d_model"]
)

print(
    "  d_state:",
    checkpoint["d_state"]
)

print(
    "  n_sites:",
    checkpoint["n_sites"]
)

print(
    "  meta_dim:",
    checkpoint["meta_dim"]
)

print(
    "  cross attention:",
    checkpoint["use_cross_attn"]
)

print(
    "  attention heads:",
    checkpoint["cross_attn_heads"]
)


# ============================================================
# BUILD MODEL
# ============================================================

print("\nBuilding LightProtoSSM...")

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


# ============================================================
# LOAD WEIGHTS
# ============================================================

print("Loading ProtoSSM weights...")

missing, unexpected = model.load_state_dict(
    checkpoint["state_dict"],
    strict=True
)

print(
    "  Missing keys:",
    len(missing)
)

print(
    "  Unexpected keys:",
    len(unexpected)
)

model.eval()

print("ProtoSSM ready")


# ============================================================
# REAL PERCH → PROTOSSM TEST
# ============================================================

def run_real_test(audio_path):

    print("\n" + "=" * 60)
    print("REAL PERCH → PROTOSSM TEST")
    print("=" * 60)

    print("\nAudio:")
    print(audio_path)

    # --------------------------------------------------------
    # Load Perch
    # --------------------------------------------------------

    print("\nLoading Perch...")

    perch = PerchModel()

    # --------------------------------------------------------
    # Run Perch
    # --------------------------------------------------------

    print("\nRunning Perch inference...")

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

    # --------------------------------------------------------
    # Verify Perch output
    # --------------------------------------------------------

    print("\nPerch results:")

    print(
        "  embeddings:",
        embeddings.shape
    )

    print(
        "  scores:",
        perch_scores.shape
    )

    if embeddings.shape != (
        N_WINDOWS,
        EMBEDDING_DIM
    ):
        raise ValueError(
            f"Unexpected Perch embeddings shape: "
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

    # --------------------------------------------------------
    # Convert to batch format
    # --------------------------------------------------------

    emb_tensor = torch.from_numpy(
        embeddings
    ).unsqueeze(0)

    perch_tensor = torch.from_numpy(
        perch_scores
    ).unsqueeze(0)

    # --------------------------------------------------------
    # Temporary metadata
    # --------------------------------------------------------

    site_ids = torch.tensor(
        [0],
        dtype=torch.long
    )

    hour_ids = torch.tensor(
        [12],
        dtype=torch.long
    )

    # --------------------------------------------------------
    # ProtoSSM
    # --------------------------------------------------------

    print("\nRunning ProtoSSM...")

    with torch.no_grad():

        proto_output = model(
            emb_tensor,
            perch_logits=perch_tensor,
            site_ids=site_ids,
            hours=hour_ids
        )

    proto_output = (
        proto_output
        .squeeze(0)
        .cpu()
        .numpy()
    )

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("SUCCESS")
    print("=" * 60)

    print(
        "\nProtoSSM output:",
        proto_output.shape
    )

    print(
        "ProtoSSM min:",
        proto_output.min()
    )

    print(
        "ProtoSSM max:",
        proto_output.max()
    )

    print(
        "ProtoSSM mean:",
        proto_output.mean()
    )

    # --------------------------------------------------------
    # Top 5 classes per window
    # --------------------------------------------------------

    print("\nTop classes per window:")

    for window_idx in range(N_WINDOWS):

        scores = proto_output[
            window_idx
        ]

        top_indices = np.argsort(
            scores
        )[-5:][::-1]

        print(
            f"\nWindow {window_idx + 1}:"
        )

        for class_idx in top_indices:

            print(
                f"  {classes[class_idx]} "
                f"(class {class_idx}): "
                f"{scores[class_idx]:.4f}"
            )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    if len(sys.argv) != 2:

        print(
            "\nUsage:"
        )

        print(
            "  python -m app.proto_predict "
            "<path-to-audio>"
        )

        print(
            "\nExample:"
        )

        print(
            r"  python -m app.proto_predict test.ogg"
        )

        raise SystemExit(1)

    audio_path = sys.argv[1]

    run_real_test(
        audio_path
    )