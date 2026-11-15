from pathlib import Path
import re

import numpy as np
import soundfile as sf
import librosa
import onnxruntime as ort
from scipy.ndimage import gaussian_filter1d


# ============================================================
# PATHS / CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
SED_DIR = MODELS_DIR / "sed"

SR = 32000

WINDOW_SEC = 5
WINDOW_SAMPLES = SR * WINDOW_SEC
N_WINDOWS = 12

N_CLASSES = 234

# Exact notebook SED settings
N_MELS_SED = 256
N_FFT_SED = 2048
HOP_SED = 512
FMIN_SED = 20
FMAX_SED = 16000
TOP_DB_SED = 80


# ============================================================
# SIGMOID
# ============================================================

def sigmoid_sed(x):
    return (
        1.0
        / (1.0 + np.exp(-np.clip(x, -50, 50)))
    ).astype(np.float32)


# ============================================================
# FIND SED MODELS
# ============================================================

def find_sed_dir():
    if not SED_DIR.exists():
        raise FileNotFoundError(
            f"SED directory not found: {SED_DIR}"
        )

    fold0 = SED_DIR / "sed_fold0.onnx"

    if not fold0.exists():
        raise FileNotFoundError(
            f"sed_fold0.onnx not found in {SED_DIR}"
        )

    return SED_DIR


# ============================================================
# ONNX SESSION
# ============================================================

def make_sed_session(path):
    so = ort.SessionOptions()

    so.intra_op_num_threads = 4
    so.inter_op_num_threads = 1
    so.graph_optimization_level = (
        ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    )

    return ort.InferenceSession(
        str(path),
        sess_options=so,
        providers=["CPUExecutionProvider"],
    )


# ============================================================
# AUDIO → 12 × 5 SEC CHUNKS
# ============================================================

def file_to_sed_chunks(path):
    y, sr0 = sf.read(
        str(path),
        dtype="float32",
        always_2d=False,
    )

    # Stereo → mono
    if y.ndim == 2:
        y = y.mean(axis=1)

    # Exact notebook behavior:
    # SED branch resamples to 32 kHz.
    if sr0 != SR:
        y = librosa.resample(
            y,
            orig_sr=sr0,
            target_sr=SR,
        )

    n = 60 * SR

    # Pad / truncate to exactly 60 seconds
    if len(y) < n:
        y = np.pad(
            y,
            (0, n - len(y)),
        )
    else:
        y = y[:n]

    # 60 sec → 12 × 5 sec
    chunks = y.reshape(
        N_WINDOWS,
        WINDOW_SAMPLES,
    )

    ends = (
        np.arange(1, N_WINDOWS + 1)
        * WINDOW_SEC
    )

    return chunks, ends


# ============================================================
# AUDIO → MEL
# ============================================================

def audio_to_mel(chunks):
    mels = []

    for x in chunks:

        s = librosa.feature.melspectrogram(
            y=x,
            sr=SR,
            n_fft=N_FFT_SED,
            hop_length=HOP_SED,
            n_mels=N_MELS_SED,
            fmin=FMIN_SED,
            fmax=FMAX_SED,
            power=2.0,
        )

        # Power → dB
        s = librosa.power_to_db(
            s,
            top_db=TOP_DB_SED,
        )

        # Per-chunk standardization
        s = (
            s - s.mean()
        ) / (
            s.std() + 1e-6
        )

        mels.append(s)

    # (12, 256, T)
    # → (12, 1, 256, T)
    return np.stack(mels)[:, None].astype(
        np.float32
    )


# ============================================================
# LOAD ALL 5 SED FOLDS
# ============================================================

print("Loading SED models...")

sed_dir = find_sed_dir()

sed_fold_paths = sorted(
    sed_dir.glob("sed_fold*.onnx"),
    key=lambda p: int(
        re.search(
            r"sed_fold(\d+)",
            p.name,
        ).group(1)
    ),
)

if len(sed_fold_paths) != 5:
    raise RuntimeError(
        f"Expected 5 SED folds, "
        f"found {len(sed_fold_paths)} "
        f"in {sed_dir}"
    )

sed_sessions = [
    make_sed_session(path)
    for path in sed_fold_paths
]

print(f"SED directory: {sed_dir}")
print(
    "SED folds:",
    [p.name for p in sed_fold_paths],
)

# Inspect input/output once
first_session = sed_sessions[0]

print(
    "SED input:",
    first_session.get_inputs()[0].name,
    first_session.get_inputs()[0].shape,
)

for i, output in enumerate(
    first_session.get_outputs()
):
    print(
        f"SED output {i}:",
        output.name,
        output.shape,
    )

print("SED models ready")


# ============================================================
# SINGLE FILE SED PREDICTION
# ============================================================

def predict_sed(path):
    """
    Run the complete 5-fold SED ensemble.

    Returns
    -------
    sed_probs : np.ndarray
        Shape: (12, 234)
    ends : np.ndarray
        End time of each 5-sec window.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Audio file not found: {path}"
        )

    print("\n" + "=" * 60)
    print("SED PIPELINE")
    print("=" * 60)

    print(f"\nAudio: {path}")

    # --------------------------------------------------------
    # Audio
    # --------------------------------------------------------

    chunks, ends = file_to_sed_chunks(
        path
    )

    print(
        "Chunks:",
        chunks.shape,
    )

    # --------------------------------------------------------
    # Mel
    # --------------------------------------------------------

    mel = audio_to_mel(chunks)

    print(
        "Mel:",
        mel.shape,
    )

    # --------------------------------------------------------
    # 5-fold ensemble
    # --------------------------------------------------------

    p_sum = np.zeros(
        (
            len(chunks),
            N_CLASSES,
        ),
        dtype=np.float32,
    )

    for fold_idx, sess in enumerate(
        sed_sessions
    ):

        input_name = (
            sess.get_inputs()[0].name
        )

        outs = sess.run(
            None,
            {
                input_name: mel
            },
        )

        # Exact notebook outputs
        clip_logits = outs[0]
        frame_max = outs[1].max(
            axis=1
        )

        # 50% clip + 50% frame
        fold_prob = (
            0.5 * sigmoid_sed(
                clip_logits
            )
            +
            0.5 * sigmoid_sed(
                frame_max
            )
        )

        p_sum += fold_prob

        print(
            f"  Fold {fold_idx}: "
            f"{fold_prob.shape}"
        )

    # Average 5 folds
    p_mean = (
        p_sum
        / len(sed_sessions)
    )

    # --------------------------------------------------------
    # Gaussian temporal smoothing
    # --------------------------------------------------------

    if len(p_mean) > 1:

        p_mean = gaussian_filter1d(
            p_mean,
            sigma=0.65,
            axis=0,
            mode="nearest",
        ).astype(
            np.float32
        )

    # --------------------------------------------------------
    # Final clipping
    # --------------------------------------------------------

    p_mean = np.clip(
        p_mean,
        0.0,
        1.0,
    ).astype(
        np.float32
    )

    print(
        "\nSED output:",
        p_mean.shape,
    )

    print(
        "min:",
        p_mean.min(),
    )

    print(
        "max:",
        p_mean.max(),
    )

    print(
        "mean:",
        p_mean.mean(),
    )

    return p_mean, ends


# ============================================================
# CLI TEST
# ============================================================

if __name__ == "__main__":

    import sys

    if len(sys.argv) != 2:
        print(
            "Usage:"
        )
        print(
            "python -m app.sed_predict test.ogg"
        )
        raise SystemExit(1)

    audio_path = sys.argv[1]

    sed_probs, ends = predict_sed(
        audio_path
    )

    print("\n" + "=" * 60)
    print("TOP SED CLASSES")
    print("=" * 60)

    # Load class names
    import json

    with open(
        BASE_DIR
        / "models"
        / "classes.json",
        "r",
    ) as f:
        classes = json.load(f)

    for w in range(N_WINDOWS):

        top_idx = np.argsort(
            sed_probs[w]
        )[::-1][:5]

        print(
            f"\nWindow {w + 1}:"
        )

        for idx in top_idx:

            print(
                f"  {classes[idx]} "
                f"(class {idx}): "
                f"{sed_probs[w, idx]:.4f}"
            )

    print(
        "\n" + "=" * 60
    )
    print("SED SUCCESS")
    print("=" * 60)