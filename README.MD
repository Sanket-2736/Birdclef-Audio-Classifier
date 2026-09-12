# 🐦 BirdCLEF Audio Classifier

An end-to-end bird sound classification API built with **FastAPI**, **Google Perch**, **ProtoSSM**, **MLP probes**, **ResidualSSM**, and a **multi-fold SED ensemble**.

The system accepts an audio recording and predicts the most likely bird species/classes present in the recording.

It is designed around the BirdCLEF-style inference pipeline, processing audio as a sequence of 5-second windows and combining multiple model branches to produce the final predictions.

---

## ✨ Features

- 🎵 Audio upload through a FastAPI REST API
- 🐦 234 target bird classes
- ⏱️ 60-second audio processing
- 🔪 Automatic splitting into 12 × 5-second windows
- 🧠 Google Perch embeddings
- 📊 Perch classifier logits
- 🔬 ProtoSSM sequence model
- 🤖 MLP probe models
- 🔄 ResidualSSM correction model
- 🌎 Site and hour metadata support
- 📈 Temperature scaling
- 🎯 Per-class thresholding
- 📊 Rank-aware post-processing
- 🔊 Multi-fold SED ensemble
- 🧩 Proto + SED final rank blending
- 🚀 FastAPI inference endpoint
- 🧹 Temporary audio-file cleanup after prediction

---

# 🏗️ System Architecture

The prediction pipeline consists of two main branches:

```text
                         Audio File
                             │
                             ▼
                    Audio Preprocessing
                             │
                    ┌────────┴────────┐
                    │                 │
                    ▼                 ▼
              Proto Branch         SED Branch
                    │                 │
                    ▼                 ▼
             Perch ONNX Model    Mel Spectrogram
                    │                 │
             ┌──────┴──────┐          │
             │             │          ▼
             ▼             ▼      5 SED ONNX Folds
        Perch Scores    Perch        │
                     Embeddings      ▼
             │             │       SED Scores
             │             ▼
             │          ProtoSSM
             │             │
             ▼             ▼
             MLP         Proto Scores
              │              │
              └──────┬───────┘
                     ▼
              First Pass Scores
                     │
                     ▼
                ResidualSSM
                     │
                     ▼
              Corrected Scores
                     │
                     ▼
            Temperature Scaling
                     │
                     ▼
                  Sigmoid
                     │
                     ▼
             Post Processing
                     │
                     ▼
               Proto Probabilities
                     │
                     └──────────────┐
                                    │
                                    ▼
                              Rank Blending
                                    ▲
                                    │
                              SED Probabilities
                                    │
                                    ▼
                            Final Predictions
```

---

# 📁 Project Structure

```text
birdclef-audio-classifier/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── pipeline.py
│   │
│   ├── first_pass_predict.py
│   ├── proto_predict.py
│   ├── residual_predict.py
│   ├── mlp_predict.py
│   │
│   ├── perch.py
│   ├── sed_predict.py
│   ├── postprocess.py
│   ├── final_blend.py
│   │
│   ├── model_loader.py
│   ├── models.py
│   └── test_artifacts.py
│
├── models/
│   ├── classes.json
│   ├── config.json
│   ├── mlp_artifacts.pkl
│   ├── per_class_thresholds.npy
│   ├── perch_mapping.pkl
│   ├── prior_tables.pkl
│   ├── proto_model.pt
│   ├── residual_model.pt
│   ├── temperatures.npy
│   │
│   └── sed/
│       ├── perch_v2.onnx
│       ├── sed_fold0.onnx
│       ├── sed_fold1.onnx
│       ├── sed_fold2.onnx
│       ├── sed_fold3.onnx
│       └── sed_fold4.onnx
│
├── uploads/
│
├── .gitignore
├── requirements.txt
└── README.md
```

---

# 🧠 Model Pipeline

## 1. Audio Preprocessing

The API accepts an audio file and converts it into a standard representation.

The target configuration is:

```text
Sample rate:       32,000 Hz
Audio duration:    60 seconds
Window duration:   5 seconds
Number of windows: 12
Samples/window:    160,000
```

Therefore:

```text
60 sec / 5 sec = 12 windows
```

Each audio file is represented as:

```text
(12, 160000)
```

where each row corresponds to one 5-second audio window.

If an input recording is shorter than 60 seconds, it is padded.

If it is longer than 60 seconds, it is truncated.

---

# 🐦 Perch Feature Extraction

The system uses Google's Perch bird-vocalization model through ONNX/TensorFlow Hub-compatible model artifacts.

The Perch model produces:

```text
Embedding dimension: 1536
```

The ONNX model exposes outputs including:

```text
embedding
spatial_embedding
spectrogram
label
```

The primary embedding used by the Proto branch is the 1536-dimensional Perch embedding.

For 12 audio windows:

```text
Perch embeddings:

(12, 1536)
```

Perch classifier outputs are also mapped to the project's 234 target classes.

---

# 🗺️ Perch Class Mapping

The Perch classifier does not directly correspond one-to-one with every target class.

The project therefore uses:

```text
models/perch_mapping.pkl
```

The mapping contains:

```text
BC_INDICES
MAPPED_MASK
MAPPED_POS
MAPPED_BC_IDX
proxy_map
```

The current mapping contains:

```text
234 target classes
203 directly mapped classes
3 proxy classes
```

The mapping is applied before feeding the Perch predictions into the downstream prediction pipeline.

---

# 🔬 ProtoSSM

The primary sequence model is a lightweight state-space model called `LightProtoSSM`.

It operates on sequential Perch embeddings:

```text
12 windows × 1536 embedding dimensions
```

The main configuration is:

```text
Input dimension:       1536
Model dimension:       128
State dimension:       16
Classes:               234
Windows:               12
Dropout:               0.15
Sites:                 20
Metadata dimension:    16
```

The architecture contains:

* Input projection
* Layer normalization
* GELU activation
* Positional encoding
* Site embeddings
* Hour embeddings
* Bidirectional SelectiveSSM blocks
* Cross-attention
* Prototype-based classification

---

# 🧬 SelectiveSSM

The sequence modeling component uses a custom Selective State Space Model.

Each SSM block processes the 12-window sequence while maintaining a hidden state.

The architecture uses both:

```text
Forward SSM
Backward SSM
```

The two outputs are merged and combined with residual connections.

This allows the model to capture temporal relationships between bird vocalizations occurring in different parts of the recording.

---

# 🎯 Prototype Classification

ProtoSSM maintains a learned prototype for each of the 234 target classes.

The model normalizes both:

```text
Window representation
Class prototypes
```

and calculates their similarity.

The resulting similarity scores are combined with Perch logits.

The model contains a learnable fusion parameter:

```text
fusion_alpha
```

which determines how Perch logits and prototype similarity contribute to the ProtoSSM output.

---

# 🤖 MLP Probe Branch

The system also contains trained MLP probe models.

The MLP branch uses:

```text
64 PCA components
+
5 sequential/statistical features
=
69/70 feature representation depending on preprocessing configuration
```

The sequential features include:

* Previous-window score
* Current-window score
* Next-window score
* Mean score
* Maximum score
* Standard deviation

The MLP architecture uses:

```text
128 hidden units
64 hidden units
1 output unit
```

with:

```text
ReLU activation
Early stopping
Learning rate: 5e-4
Alpha: 0.005
```

The trained probe models and preprocessing objects are stored in:

```text
models/mlp_artifacts.pkl
```

The artifact contains:

```text
probe_models
scaler
pca
alpha_blend
```

---

# 🔄 First-Pass Prediction

The Proto branch combines the ProtoSSM and MLP outputs.

The main ensemble weighting is:

```text
ProtoSSM: 50%
MLP/Perch-adjusted branch: 50%
```

Conceptually:

```text
First Pass
    =
0.5 × ProtoSSM
+
0.5 × MLP-adjusted Perch scores
```

The result is then passed to the ResidualSSM correction stage.

---

# 🔁 ResidualSSM

ResidualSSM learns a correction to the first-pass predictions.

It receives:

```text
Perch embeddings
+
First-pass scores
```

The configuration is:

```text
Input embedding dimension: 1536
Score dimension:            234
Model dimension:            64
State dimension:              8
Classes:                    234
Windows:                     12
```

It uses:

```text
Forward SelectiveSSM
Backward SelectiveSSM
Residual connection
Output head
```

The output layer is initialized to zero, allowing the model to learn residual corrections around the first-pass prediction.

The trained model is stored as:

```text
models/residual_model.pt
```

The correction is applied with a weight of:

```text
0.30
```

Therefore:

```text
Corrected Scores
=
First Pass Scores
+
0.30 × Residual Correction
```

---

# 🌡️ Temperature Scaling

After residual correction, the scores are divided by a learned temperature vector.

The temperatures are stored in:

```text
models/temperatures.npy
```

There is one temperature value for each target class:

```text
Shape: (234,)
```

The transformation is:

```text
scaled_score = corrected_score / temperature
```

The scaled scores are then passed through the sigmoid function.

---

# 📊 Probability Post-Processing

The Proto branch applies several post-processing operations.

## File Confidence Scaling

The system evaluates the strongest predictions across the 12 windows and adjusts file-level confidence.

## Rank-Aware Scaling

Predictions are adjusted according to their relative rank within each class.

## Adaptive Delta Smoothing

Neighboring window predictions are smoothed using an adaptive temporal strategy.

## Per-Class Thresholds

Finally, learned class-specific thresholds are applied.

The thresholds are stored in:

```text
models/per_class_thresholds.npy
```

with:

```text
Shape: (234,)
```

---

# 🔊 SED Branch

The second prediction branch is a Sound Event Detection ensemble.

The SED branch converts each 5-second window into a mel spectrogram.

Configuration:

```text
Sample rate: 32,000 Hz
Mel bins:    256
FFT:         2048
Hop length:  512
Fmin:        20 Hz
Fmax:        16,000 Hz
Top dB:      80
```

The resulting mel representation is approximately:

```text
(12, 1, 256, 313)
```

---

# 🧩 SED Ensemble

Five ONNX models are used:

```text
sed_fold0.onnx
sed_fold1.onnx
sed_fold2.onnx
sed_fold3.onnx
sed_fold4.onnx
```

Each fold produces:

```text
Clip logits
Frame-level outputs
```

The clip-level and frame-level predictions are combined.

The five folds are then averaged.

Temporal Gaussian smoothing is applied with:

```text
sigma = 0.65
```

The final SED output has:

```text
12 windows × 234 classes
```

---

# ⚖️ Final Proto + SED Blend

The final prediction is produced using rank-based blending.

The configured weights are:

```text
Proto branch: 60%
SED branch:   40%
```

Therefore:

```text
Final Rank Score
=
0.60 × Proto Rank
+
0.40 × SED Rank
```

The pipeline additionally handles:

* Proto-only high-confidence cases
* Proto-continuity cases
* SED-only high-confidence cases

The final prediction therefore combines both:

```text
Temporal prototype-based classification
+
Sound event detection
```

---

# 🌳 Metadata

The Proto and ResidualSSM models can use:

```text
Site ID
Hour ID
```

The current API accepts:

```text
site_id: 0–19
hour_id: 0–23
```

Default values are:

```text
site_id = 0
hour_id = 12
```

These metadata values are converted into learned embeddings and incorporated into the sequence models.

---

# 🚀 Getting Started

## 1. Clone the repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd birdclef-audio-classifier
```

---

## 2. Create a virtual environment

### Windows

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

# 📦 Install Dependencies

Install the required packages:

```bash
pip install -r requirements.txt
```

The project requires Python packages including:

```text
FastAPI
Uvicorn
PyTorch
ONNX Runtime
NumPy
Pandas
SciPy
Librosa
SoundFile
scikit-learn
TensorFlow Hub
```

The exact versions should be kept in `requirements.txt`.

---

# 🔍 Verify Model Artifacts

Before starting the API, verify that the required artifacts can be loaded:

```powershell
python -m app.test_artifacts
```

A successful verification should confirm the presence and loading of:

```text
classes.json
mlp_artifacts.pkl
perch_mapping.pkl
prior_tables.pkl
temperatures.npy
per_class_thresholds.npy
config.json
proto_model.pt
residual_model.pt
```

and the SED models.

---

# ▶️ Run the API

Start the FastAPI server with:

```powershell
uvicorn app.main:app --reload
```

The API will normally be available at:

```text
http://127.0.0.1:8000
```

---

# 📚 API Documentation

FastAPI automatically provides interactive API documentation.

Open:

```text
http://127.0.0.1:8000/docs
```

You can use Swagger UI to upload an audio file and test the `/predict` endpoint.

---

# 🔮 Prediction API

## Endpoint

```http
POST /predict
```

### Request

The endpoint accepts:

```text
audio
site_id
hour_id
```

Example:

```text
audio: bird_recording.ogg
site_id: 0
hour_id: 12
```

---

# 📤 Example Request

Using `curl`:

```bash
curl -X POST "http://127.0.0.1:8000/predict" \
  -F "audio=@test.ogg" \
  -F "site_id=0" \
  -F "hour_id=12"
```

On Windows PowerShell:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/predict" `
  -F "audio=@test.ogg" `
  -F "site_id=0" `
  -F "hour_id=12"
```

---

# 📥 Response

The API returns:

```json
{
  "n_windows": 12,
  "n_classes": 234,
  "top_predictions": [
    {
      "class_index": 123,
      "label": "example_bird",
      "score": 1.0
    }
  ],
  "window_predictions": [],
  "file_scores": []
}
```

---

# 🏆 Top Predictions

`top_predictions` contains the strongest predictions for the complete audio file.

Example:

```json
"top_predictions": [
  {
    "class_index": 45,
    "label": "whtdov",
    "score": 1.0
  },
  {
    "class_index": 102,
    "label": "yebela1",
    "score": 0.947
  }
]
```

The file-level score is calculated from the strongest prediction across the 12 windows.

---

# 🪟 Window-Level Predictions

The API also returns predictions for each 5-second window.

Each window contains:

```json
{
  "window": 1,
  "start_sec": 0,
  "end_sec": 5,
  "predictions": [
    {
      "class_index": 10,
      "label": "example_bird",
      "score": 0.91
    }
  ]
}
```

For a 60-second recording:

```text
Window 1  → 0–5 sec
Window 2  → 5–10 sec
Window 3  → 10–15 sec
...
Window 12 → 55–60 sec
```

---

# 📊 Output Dimensions

For every audio file:

```text
Number of windows = 12
Number of classes = 234
```

The complete prediction matrix therefore has:

```text
(12, 234)
```

dimensions.

---

# ⚙️ Configuration

The main configuration is stored in:

```text
models/config.json
```

Current configuration:

```json
{
  "sample_rate": 32000,
  "window_seconds": 5,
  "window_samples": 160000,
  "file_seconds": 60,
  "n_windows": 12,
  "n_classes": 234,
  "ensemble_weight": 0.5,
  "proto_rank_weight": 0.6,
  "sed_rank_weight": 0.4,
  "sonotype_mirroring": false,
  "rare_taxon_suppression": false
}
```

---

# 🧪 Testing

## Test artifact loading

```powershell
python -m app.test_artifacts
```

## Test SED prediction

```powershell
python -m app.sed_predict test.ogg
```

The expected output shape is:

```text
(12, 234)
```

## Test the API

Start the server:

```powershell
uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/docs
```

Upload an audio recording and execute `/predict`.

---

# 🛠️ Technologies Used

| Technology   | Purpose                              |
| ------------ | ------------------------------------ |
| Python       | Core programming language            |
| FastAPI      | REST API                             |
| Uvicorn      | ASGI server                          |
| PyTorch      | ProtoSSM and ResidualSSM             |
| ONNX Runtime | Perch and SED inference              |
| Google Perch | Bird audio embeddings/classification |
| Librosa      | Audio processing                     |
| SoundFile    | Audio loading                        |
| NumPy        | Numerical processing                 |
| Pandas       | Ranking and data processing          |
| SciPy        | Temporal smoothing                   |
| scikit-learn | PCA, scaling and MLP probes          |

---

# 📦 Model Artifacts

The `models/` directory contains the trained inference artifacts.

### ProtoSSM

```text
models/proto_model.pt
```

### ResidualSSM

```text
models/residual_model.pt
```

### MLP probes

```text
models/mlp_artifacts.pkl
```

### Perch mapping

```text
models/perch_mapping.pkl
```

### Prior tables

```text
models/prior_tables.pkl
```

### Temperature calibration

```text
models/temperatures.npy
```

### Per-class thresholds

```text
models/per_class_thresholds.npy
```

### Class labels

```text
models/classes.json
```

### Configuration

```text
models/config.json
```

### SED models

```text
models/sed/
```

---

# ⚠️ Model File Size

Some model artifacts can be large.

If the repository exceeds GitHub's normal file-size limits, use **Git LFS** for large:

```text
*.pt
*.onnx
*.pkl
```

For example:

```bash
git lfs install
git lfs track "*.pt"
git lfs track "*.onnx"
git lfs track "*.pkl"
```

Then commit the generated `.gitattributes` file.

Do not commit:

```text
.venv/
uploads/
.env
temporary audio files
Python cache files
```

---

# 🔐 Environment Variables

If environment variables are required in future versions, store them in:

```text
.env
```

Never commit the actual `.env` file.

Instead provide:

```text
.env.example
```

Example:

```env
MODEL_DIR=models
UPLOAD_DIR=uploads
```

---

# 🧹 Temporary Files

Uploaded audio files are stored temporarily during prediction.

The API removes the temporary file after processing.

This prevents the `uploads/` directory from continuously accumulating recordings.

The directory should therefore remain excluded from Git:

```gitignore
uploads/
```

---

# 🚧 Current Limitations

* The model currently expects a 60-second inference pipeline.
* Input audio is normalized to 32 kHz.
* Predictions are limited to 234 target classes.
* Site IDs currently use numeric values.
* Hour IDs use the range 0–23.
* CPU inference can be significantly slower than GPU inference.
* Large ONNX/PyTorch artifacts may require Git LFS or external model storage.
* Model loading and inference performance should be optimized further for high-concurrency production deployment.

---

# 🔮 Future Improvements

Potential improvements include:

* [ ] Load Perch only once during API startup
* [ ] Optimize model inference for concurrent requests
* [ ] Add GPU support
* [ ] Add Docker deployment
* [ ] Add automated tests
* [ ] Add CI/CD with GitHub Actions
* [ ] Add health-check endpoint
* [ ] Add model versioning
* [ ] Move large model artifacts to dedicated model storage
* [ ] Add authentication
* [ ] Add request size limits
* [ ] Add structured logging
* [ ] Add inference-time monitoring
* [ ] Add batch prediction support
* [ ] Add audio visualization
* [ ] Add frontend interface for uploading recordings

---

# 📈 Performance Considerations

For production deployment, model initialization should happen once rather than loading large models for every request.

The recommended architecture is:

```text
                    FastAPI Startup
                          │
              ┌───────────┴───────────┐
              │                       │
        Load Perch               Load SED
              │                       │
              └───────────┬───────────┘
                          │
                          ▼
                   Ready for requests
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
          Request 1    Request 2    Request 3
```

This avoids repeatedly loading large ONNX/PyTorch models.

---

# 🧪 Reproducibility

The model artifacts used by the API should match the configuration in:

```text
models/config.json
```

Important parameters include:

```text
sample_rate
window_seconds
window_samples
file_seconds
n_windows
n_classes
proto_rank_weight
sed_rank_weight
```

Changing these values without retraining or validating the corresponding models may produce incorrect results.

---

# 📄 License

Add the appropriate license for your project here.

Example:

```text
MIT License
```

Before publishing, verify that the licenses of all pretrained models and datasets used by the project allow the intended redistribution.

---

# 🙏 Acknowledgements

This project builds on bird-audio classification techniques and pretrained bird-vocalization representations.

Special acknowledgement to:

* Google Perch / Bird Vocalization Classifier
* BirdCLEF
* PyTorch
* ONNX Runtime
* FastAPI
* Librosa
* scikit-learn

---

# 👨‍💻 Author

**Mr. Engineer**

BirdCLEF Audio Classification API

---

# ⭐ Project Summary

This project provides a complete bird sound inference pipeline:

```text
Audio
  ↓
60-second normalization
  ↓
12 × 5-second windows
  ↓
Perch embeddings + logits
  ↓
ProtoSSM + MLP
  ↓
First-pass prediction
  ↓
ResidualSSM correction
  ↓
Temperature scaling
  ↓
Probability post-processing
  ↓
SED 5-fold ensemble
  ↓
Proto + SED rank blending
  ↓
234-class predictions
  ↓
FastAPI JSON response
```

The result is a deployable bird-audio classification API capable of producing both **file-level** and **5-second window-level** predictions.

---

## ⚠️ Important: Git LFS Setup

Your current repository contains trained model artifacts (`.pt`, `.onnx`, `.pkl` files). Before your first `git push`, check the file sizes:

```powershell
Get-ChildItem models/ -Recurse | Sort-Object Length -Descending
```

If any files exceed 50 MB, **use Git LFS** to avoid repository bloat:

```bash
git lfs install
git lfs track "*.pt" "*.onnx" "*.pkl" "*.npy"
git add .gitattributes
git commit -m "Configure Git LFS for large model artifacts"
```

This ensures your repository remains clean and pushes don't fail due to large file size limits.
