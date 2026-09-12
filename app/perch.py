from pathlib import Path

import numpy as np
import soundfile as sf
import onnxruntime as ort
import pickle


BASE_DIR = Path(__file__).resolve().parent.parent

PERCH_MODEL_PATH = (
    BASE_DIR / "models" / "sed" / "perch_v2.onnx"
)

MAPPING_PATH = (
    BASE_DIR / "models" / "perch_mapping.pkl"
)

SR = 32_000
WINDOW_SEC = 5
WINDOW_SAMPLES = SR * WINDOW_SEC
FILE_SAMPLES = 60 * SR
N_WINDOWS = 12
N_CLASSES = 234
EMBEDDING_DIM = 1536


class PerchModel:

    def __init__(self):

        print("Loading Perch ONNX...")

        self.session = ort.InferenceSession(
            str(PERCH_MODEL_PATH),
            providers=["CPUExecutionProvider"]
        )

        self.input_name = self.session.get_inputs()[0].name

        print("Perch loaded successfully")
        print("  input:", self.input_name)

        for output in self.session.get_outputs():
            print("  output:", output.name, output.shape)

        print()
        print("Loading Perch mapping...")

        with open(MAPPING_PATH, "rb") as f:
            mapping = pickle.load(f)

        self.BC_INDICES = mapping["BC_INDICES"]
        self.MAPPED_MASK = mapping["MAPPED_MASK"]
        self.MAPPED_POS = mapping["MAPPED_POS"]
        self.MAPPED_BC_IDX = mapping["MAPPED_BC_IDX"]
        self.proxy_map = mapping["proxy_map"]

        print("Perch mapping loaded")
        print("  BC indices:", len(self.BC_INDICES))
        print("  mapped classes:", len(self.MAPPED_POS))
        print("  proxy classes:", len(self.proxy_map))


    def read_60s(self, path):

        audio, sr = sf.read(
            path,
            dtype="float32"
        )

        # Stereo → mono
        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        if sr != SR:
            raise ValueError(
                f"Expected {SR} Hz audio, "
                f"but received {sr} Hz"
            )

        # Pad / truncate to exactly 60 seconds
        if len(audio) < FILE_SAMPLES:

            audio = np.pad(
                audio,
                (0, FILE_SAMPLES - len(audio))
            )

        else:

            audio = audio[:FILE_SAMPLES]

        return audio.astype(np.float32)


    def predict_raw(self, audio_path):

        audio = self.read_60s(audio_path)

        # 60 sec → 12 × 5 sec
        windows = audio.reshape(
            N_WINDOWS,
            WINDOW_SAMPLES
        )

        outputs = self.session.run(
            None,
            {
                self.input_name: windows
            }
        )

        output_names = [
            output.name
            for output in self.session.get_outputs()
        ]

        output_dict = dict(
            zip(output_names, outputs)
        )

        logits = np.asarray(
            output_dict["label"],
            dtype=np.float32
        )

        embeddings = np.asarray(
            output_dict["embedding"],
            dtype=np.float32
        )

        return logits, embeddings


    def map_to_competition_classes(self, logits):

        scores = np.zeros(
            (logits.shape[0], N_CLASSES),
            dtype=np.float32
        )

        # Direct BirdCLEF class mapping
        scores[:, self.MAPPED_POS] = (
            logits[:, self.MAPPED_BC_IDX]
        )

        # Genus proxy mapping
        for pos_idx, bc_arr in self.proxy_map.items():

            scores[:, pos_idx] = (
                logits[:, bc_arr].max(axis=1)
            )

        return scores


    def predict(self, audio_path):

        logits, embeddings = self.predict_raw(
            audio_path
        )

        scores = self.map_to_competition_classes(
            logits
        )

        return {
            "scores": scores,
            "embeddings": embeddings,
            "raw_logits": logits
        }


if __name__ == "__main__":

    import sys

    if len(sys.argv) != 2:

        print(
            "Usage:\n"
            "python -m app.perch <path-to-wav>"
        )

        raise SystemExit(1)

    audio_path = sys.argv[1]

    model = PerchModel()

    print()
    print("Running Perch inference...")
    print("Audio:", audio_path)

    result = model.predict(audio_path)

    print()
    print("SUCCESS")
    print()

    print(
        "Raw logits shape:",
        result["raw_logits"].shape
    )

    print(
        "Embeddings shape:",
        result["embeddings"].shape
    )

    print(
        "Competition scores shape:",
        result["scores"].shape
    )

    print()
    print(
        "Embedding dimension:",
        result["embeddings"].shape[-1]
    )

    print(
        "Number of competition classes:",
        result["scores"].shape[-1]
    )