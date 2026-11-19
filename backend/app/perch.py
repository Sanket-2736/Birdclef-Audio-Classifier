
from pathlib import Path

import numpy as np
import soundfile as sf
import onnxruntime as ort
import pickle


print("[DEBUG] Initializing Perch model module...")

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

print(f"[DEBUG] Base directory: {BASE_DIR}")
print(f"[DEBUG] Perch ONNX path: {PERCH_MODEL_PATH}")
print(f"[DEBUG] Mapping path: {MAPPING_PATH}")
print(f"[DEBUG] Sample rate: {SR}")
print(f"[DEBUG] Window duration: {WINDOW_SEC} seconds")
print(f"[DEBUG] Window samples: {WINDOW_SAMPLES}")
print(f"[DEBUG] Total file samples: {FILE_SAMPLES}")
print(f"[DEBUG] Number of windows: {N_WINDOWS}")
print(f"[DEBUG] Number of classes: {N_CLASSES}")
print(f"[DEBUG] Embedding dimension: {EMBEDDING_DIM}")


class _CompatUnpickler(pickle.Unpickler):
    """Unpickler that handles numpy 2.x pickles on numpy 1.x."""

    def find_class(self, module, name):

        print(
            f"[DEBUG] Resolving pickle class: "
            f"module={module}, name={name}"
        )

        if module.startswith("numpy._core"):
            module = module.replace("numpy._core", "numpy.core")
            print(f"[DEBUG] Adjusted NumPy module path: {module}")

        return super().find_class(module, name)


class PerchModel:

    def __init__(self):

        print("\n" + "=" * 60)
        print("[DEBUG] INITIALIZING PERCH MODEL")
        print("=" * 60)

        print(f"[DEBUG] ONNX model exists: {PERCH_MODEL_PATH.exists()}")
        print(f"[DEBUG] Mapping file exists: {MAPPING_PATH.exists()}")

        print("\n[DEBUG] Loading Perch ONNX...")

        self.session = ort.InferenceSession(
            str(PERCH_MODEL_PATH),
            providers=["CPUExecutionProvider"]
        )

        print("[SUCCESS] Perch ONNX session initialized.")

        print("[DEBUG] Available ONNX providers:")
        print(self.session.get_providers())

        inputs = self.session.get_inputs()

        print(f"[DEBUG] Number of ONNX inputs: {len(inputs)}")

        for input_info in inputs:
            print(
                f"[DEBUG] Input: {input_info.name}, "
                f"shape: {input_info.shape}, "
                f"type: {input_info.type}"
            )

        self.input_name = self.session.get_inputs()[0].name

        print(f"[DEBUG] Selected input name: {self.input_name}")

        print("[DEBUG] ONNX output information:")

        for output in self.session.get_outputs():
            print(
                f"  output: {output.name}, "
                f"shape: {output.shape}"
            )

        print("\n[DEBUG] Loading Perch mapping...")

        with open(MAPPING_PATH, "rb") as f:

            try:
                print("[DEBUG] Attempting standard pickle loading...")

                mapping = pickle.load(f)

                print("[SUCCESS] Standard pickle loading successful.")

            except ModuleNotFoundError:

                print(
                    "[WARNING] Standard pickle loading failed "
                    "due to missing module."
                )

                print("[DEBUG] Retrying with compatibility unpickler...")

                f.seek(0)

                mapping = _CompatUnpickler(f).load()

                print("[SUCCESS] Compatibility unpickling successful.")

        print(f"[DEBUG] Mapping keys: {list(mapping.keys())}")

        self.BC_INDICES = mapping["BC_INDICES"]
        self.MAPPED_MASK = mapping["MAPPED_MASK"]
        self.MAPPED_POS = mapping["MAPPED_POS"]
        self.MAPPED_BC_IDX = mapping["MAPPED_BC_IDX"]
        self.proxy_map = mapping["proxy_map"]

        print("\n[SUCCESS] Perch mapping loaded.")

        print("  BC indices:", len(self.BC_INDICES))
        print("  mapped classes:", len(self.MAPPED_POS))
        print("  proxy classes:", len(self.proxy_map))

        print(f"[DEBUG] MAPPED_MASK shape: {self.MAPPED_MASK.shape}")
        print(f"[DEBUG] MAPPED_POS shape: {self.MAPPED_POS.shape}")
        print(f"[DEBUG] MAPPED_BC_IDX shape: {self.MAPPED_BC_IDX.shape}")

        print("[SUCCESS] Perch model initialization completed.")

    def read_60s(self, path):

        print("\n[DEBUG] Reading audio file...")
        print(f"[DEBUG] Audio path: {path}")

        audio, sr = sf.read(
            path,
            dtype="float32"
        )

        print("[SUCCESS] Audio file loaded.")
        print(f"[DEBUG] Original audio shape: {audio.shape}")
        print(f"[DEBUG] Original sample rate: {sr}")
        print(f"[DEBUG] Original audio dtype: {audio.dtype}")

        # Stereo → mono
        if audio.ndim > 1:

            print("[DEBUG] Stereo audio detected.")
            print("[DEBUG] Converting stereo audio to mono...")

            audio = audio.mean(axis=1)

            print(f"[DEBUG] Mono audio shape: {audio.shape}")

        else:

            print("[DEBUG] Mono audio detected.")

        print("\n[DEBUG] Validating sample rate...")

        if sr != SR:

            print("[ERROR] Audio sample rate mismatch.")
            print(f"[ERROR] Expected: {SR} Hz")
            print(f"[ERROR] Received: {sr} Hz")

            raise ValueError(
                f"Expected {SR} Hz audio, "
                f"but received {sr} Hz"
            )

        print("[SUCCESS] Sample rate validated.")

        print("\n[DEBUG] Checking audio duration...")

        print(f"[DEBUG] Current samples: {len(audio)}")
        print(f"[DEBUG] Expected samples: {FILE_SAMPLES}")

        # Pad / truncate to exactly 60 seconds
        if len(audio) < FILE_SAMPLES:

            padding_samples = FILE_SAMPLES - len(audio)

            print("[DEBUG] Audio is shorter than 60 seconds.")
            print(f"[DEBUG] Padding with {padding_samples} samples.")

            audio = np.pad(
                audio,
                (0, FILE_SAMPLES - len(audio))
            )

            print(f"[DEBUG] Padded audio shape: {audio.shape}")

        else:

            if len(audio) > FILE_SAMPLES:
                print("[DEBUG] Audio exceeds 60 seconds.")
                print("[DEBUG] Truncating audio to 60 seconds.")
            else:
                print("[DEBUG] Audio is exactly 60 seconds.")

            audio = audio[:FILE_SAMPLES]

            print(f"[DEBUG] Truncated audio shape: {audio.shape}")

        audio = audio.astype(np.float32)

        print("[SUCCESS] Audio preprocessing completed.")
        print(f"[DEBUG] Final audio shape: {audio.shape}")
        print(f"[DEBUG] Final audio dtype: {audio.dtype}")

        return audio

    def predict_raw(self, audio_path):

        print("\n" + "=" * 60)
        print("[DEBUG] STARTING RAW PERCH INFERENCE")
        print("=" * 60)

        print(f"[DEBUG] Input audio: {audio_path}")

        audio = self.read_60s(audio_path)

        # 60 sec → 12 × 5 sec
        print("\n[DEBUG] Splitting audio into windows...")

        windows = audio.reshape(
            N_WINDOWS,
            WINDOW_SAMPLES
        )

        print("[SUCCESS] Audio windowing completed.")
        print(f"[DEBUG] Windows shape: {windows.shape}")
        print(f"[DEBUG] Windows dtype: {windows.dtype}")

        print("\n[DEBUG] Running ONNX inference...")

        outputs = self.session.run(
            None,
            {
                self.input_name: windows
            }
        )

        print("[SUCCESS] ONNX inference completed.")
        print(f"[DEBUG] Number of returned outputs: {len(outputs)}")

        output_names = [
            output.name
            for output in self.session.get_outputs()
        ]

        print(f"[DEBUG] ONNX output names: {output_names}")

        output_dict = dict(
            zip(output_names, outputs)
        )

        print("[DEBUG] ONNX output dictionary created.")

        for name, output in output_dict.items():
            print(
                f"[DEBUG] Output '{name}' shape: {output.shape}"
            )
            print(
                f"[DEBUG] Output '{name}' dtype: {output.dtype}"
            )

        print("\n[DEBUG] Extracting logits...")

        logits = np.asarray(
            output_dict["label"],
            dtype=np.float32
        )

        print(f"[DEBUG] Logits shape: {logits.shape}")
        print(f"[DEBUG] Logits dtype: {logits.dtype}")

        print("\n[DEBUG] Extracting embeddings...")

        embeddings = np.asarray(
            output_dict["embedding"],
            dtype=np.float32
        )

        print(f"[DEBUG] Embeddings shape: {embeddings.shape}")
        print(f"[DEBUG] Embeddings dtype: {embeddings.dtype}")

        print("[SUCCESS] Raw Perch outputs extracted.")

        return logits, embeddings

    def map_to_competition_classes(self, logits):

        print("\n" + "=" * 60)
        print("[DEBUG] MAPPING PERCH OUTPUTS TO COMPETITION CLASSES")
        print("=" * 60)

        print(f"[DEBUG] Input logits shape: {logits.shape}")

        scores = np.zeros(
            (logits.shape[0], N_CLASSES),
            dtype=np.float32
        )

        print(f"[DEBUG] Initialized score matrix: {scores.shape}")

        # Direct BirdCLEF class mapping
        print("\n[DEBUG] Applying direct BirdCLEF class mapping...")

        print(f"[DEBUG] Mapped positions: {len(self.MAPPED_POS)}")
        print(f"[DEBUG] BirdCLEF indices: {len(self.MAPPED_BC_IDX)}")

        scores[:, self.MAPPED_POS] = (
            logits[:, self.MAPPED_BC_IDX]
        )

        print("[SUCCESS] Direct class mapping completed.")

        # Genus proxy mapping
        print("\n[DEBUG] Applying genus proxy mapping...")

        for pos_idx, bc_arr in self.proxy_map.items():

            print(
                f"[DEBUG] Mapping proxy position {pos_idx} "
                f"using {len(bc_arr)} source classes."
            )

            scores[:, pos_idx] = (
                logits[:, bc_arr].max(axis=1)
            )

        print("[SUCCESS] Genus proxy mapping completed.")

        print(f"[DEBUG] Final competition scores shape: {scores.shape}")
        print(f"[DEBUG] Final competition scores dtype: {scores.dtype}")

        return scores

    def predict(self, audio_path):

        print("\n" + "=" * 60)
        print("[DEBUG] PERCH PREDICTION PIPELINE STARTED")
        print("=" * 60)

        print(f"[DEBUG] Audio path: {audio_path}")

        print("\n[DEBUG] Running raw Perch prediction...")

        logits, embeddings = self.predict_raw(
            audio_path
        )

        print("[SUCCESS] Raw Perch prediction completed.")

        print(f"[DEBUG] Logits shape: {logits.shape}")
        print(f"[DEBUG] Embeddings shape: {embeddings.shape}")

        print("\n[DEBUG] Mapping logits to competition classes...")

        scores = self.map_to_competition_classes(
            logits
        )

        print("[SUCCESS] Competition class mapping completed.")

        print("\n[DEBUG] Preparing prediction result...")

        result = {
            "scores": scores,
            "embeddings": embeddings,
            "raw_logits": logits
        }

        print("[SUCCESS] Perch prediction pipeline completed.")

        print(f"[DEBUG] Scores shape: {result['scores'].shape}")
        print(f"[DEBUG] Embeddings shape: {result['embeddings'].shape}")
        print(f"[DEBUG] Raw logits shape: {result['raw_logits'].shape}")

        return result


if __name__ == "__main__":

    import sys

    print("\n" + "=" * 60)
    print("[DEBUG] PERCH STANDALONE EXECUTION")
    print("=" * 60)

    if len(sys.argv) != 2:

        print("[ERROR] Invalid command-line arguments.")

        print(
            "Usage:\n"
            "python -m app.perch <path-to-wav>"
        )

        raise SystemExit(1)

    audio_path = sys.argv[1]

    print(f"[DEBUG] Provided audio path: {audio_path}")

    model = PerchModel()

    print("\n[DEBUG] Running Perch inference...")
    print("Audio:", audio_path)

    result = model.predict(audio_path)

    print("\n" + "=" * 60)
    print("[SUCCESS] PERCH INFERENCE COMPLETED")
    print("=" * 60)

    print("\n[DEBUG] Final output information:")

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

    print("\n[DEBUG] Output dimensions:")

    print(
        "Embedding dimension:",
        result["embeddings"].shape[-1]
    )

    print(
        "Number of competition classes:",
        result["scores"].shape[-1]
    )

    print("\n[SUCCESS] ALL PERCH OPERATIONS FINISHED")
