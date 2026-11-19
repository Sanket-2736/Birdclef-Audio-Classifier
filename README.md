# 🦅 WildEcho: BirdCLEF Audio Classifier

A sophisticated AI-powered wildlife audio classification system that detects and identifies bird species from 60-second audio recordings using a seven-stage deep learning pipeline.

## Overview

WildEcho combines **Perch** (Google's pretrained bird-specific audio model) with custom temporal modeling, prototype matching, and ensemble methods to achieve state-of-the-art bird species detection and classification.

**Key Stats:**
- 📊 **234 Bird Species** — Supports full BirdCLEF taxonomy
- 🎯 **0.9154 Macro ROC-AUC** — Excellent ranking performance
- ⚡ **~45 seconds** — Average processing time per 60-second recording
- 🌍 **Global Coverage** — Trained on Xeno-canto + BirdCLEF data

## 🏗️ Architecture

### Seven-Step Pipeline

```
60-second Audio
    ↓
[1] Data Preprocessing (12 × 5-second windows)
    ↓
[2] Perch Feature Extraction (1,536-D embeddings)
    ↓
[3] Temporal Modeling (bidirectional state-space + attention)
    ↓
[4] Prototype Classification (learnable species signatures)
    ↓
[5] Refinement Stages (MLP + ResidualSSM)
    ↓
[6] Calibration & Thresholding (per-class temps + thresholds)
    ↓
[7] Ensemble Fusion (Proto + SED branches, rank fusion)
    ↓
Species List (ranked by confidence with temporal localization)
```

### Components

| Component | Purpose | Performance |
|-----------|---------|-------------|
| **Perch Embeddings** | Frozen 1,536-D bird-specific acoustic features | Foundation of all predictions |
| **ProtoSSM** | Bidirectional temporal modeling with attention | Captures species patterns across 60s |
| **Prototype Layer** | 234 learnable species signatures | Interpretable, learnable per-species features |
| **MLP Refinement** | Context-aware score refinement | +2-3% F1 improvement |
| **ResidualSSM** | Error correction (second-pass) | Fixes false positives |
| **SED Ensemble** | 5 sound-event-detection models | Complementary spectrogram-based branch |
| **Calibration** | Per-class temperature scaling | Handles 234-class imbalance |

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+** (backend)
- **Node.js 16+** (frontend)
- **CUDA 11.8+** (optional, for GPU acceleration)
- **4GB RAM minimum** (8GB+ recommended)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/Scripts/activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings (database URL, etc.)

# Run migrations
alembic upgrade head

# Start server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Backend runs on:** `http://localhost:8000`
**API docs:** `http://localhost:8000/docs`

### Frontend Setup

```bash
cd frontend_fixed/frontend\ -\ Copy

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Update VITE_API_URL to match backend

# Start dev server
npm run dev
```

**Frontend runs on:** `http://localhost:5173`

### Quick Start (Docker - Optional)

```bash
# Build and run both services
docker-compose up --build

# Backend: http://localhost:8000
# Frontend: http://localhost:5173
```

## 📁 Project Structure

```
Birdclef-Audio-Classifier/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app
│   │   ├── config.py               # Configuration
│   │   ├── db.py                   # Database setup
│   │   ├── db_models.py            # SQLAlchemy models
│   │   ├── auth.py                 # JWT authentication
│   │   ├── routers/
│   │   │   ├── auth.py             # Auth endpoints
│   │   │   ├── recordings.py       # Recording management
│   │   │   └── predictions.py      # Prediction endpoints
│   │   ├── audio_utils.py          # Audio processing
│   │   ├── pipeline.py             # Main inference pipeline
│   │   ├── perch.py                # Perch embedding extraction
│   │   ├── proto_predict.py        # Prototype matching
│   │   ├── mlp_predict.py          # MLP refinement
│   │   ├── postprocess.py          # Result calibration
│   │   ├── model_loader.py         # Model initialization
│   │   └── utils/
│   │       ├── serialize.py        # JSON serialization
│   │       └── performance.py      # Metrics calculation
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
├── frontend_fixed/
│   └── frontend - Copy/
│       ├── src/
│       │   ├── pages/
│       │   │   ├── Home.jsx        # Landing page
│       │   │   ├── Analyze.jsx     # Main analysis page
│       │   │   ├── Results.jsx     # Results display
│       │   │   ├── HowItWorks.jsx  # 7-step pipeline explanation
│       │   │   ├── About.jsx       # About page
│       │   │   ├── Contact.jsx     # Contact form
│       │   │   ├── Dashboard.jsx   # User dashboard
│       │   │   ├── History.jsx     # Analysis history
│       │   │   ├── Login.jsx       # Login page
│       │   │   ├── Register.jsx    # Registration
│       │   │   └── NotFound.jsx    # 404 page
│       │   ├── components/
│       │   │   ├── WaveformHover.jsx     # Waveform display
│       │   │   ├── ExportBar.jsx        # Export controls
│       │   │   └── ...
│       │   └── App.jsx
│       ├── package.json
│       ├── vite.config.ts
│       ├── tailwind.config.js
│       └── .env.example
├── README.md (this file)
├── .gitignore
└── docker-compose.yml (optional)
```

## 🎯 Usage

### Via Web Interface

1. **Navigate to** `http://localhost:5173`
2. **Upload Audio:**
   - Drag-drop or click to select 60-second audio file
   - Supports: WAV, MP3, OGG, FLAC
3. **View Results:**
   - **Metadata:** Duration, sample rate, file size, location (if provided)
   - **Top Detections:** Top 3 species with confidence scores
   - **Full Table:** All 234 species ranked by confidence
   - **Timeline:** Which 5-second windows contained each species
   - **Statistics:** Average confidence, processing time

### Via API

```bash
# 1. Register/Login
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secure_pwd"}'

# 2. Upload recording
curl -X POST http://localhost:8000/api/v1/recordings/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@recording.wav"

# 3. Check status
curl http://localhost:8000/api/v1/recordings/{recording_id} \
  -H "Authorization: Bearer YOUR_TOKEN"

# 4. Get predictions when status='done'
curl http://localhost:8000/api/v1/recordings/{recording_id}/predictions \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Example Response

```json
{
  "recording_id": "222e9971-1bae-43d3-bdbe-87d91649ec1a",
  "status": "done",
  "predictions": [
    {
      "rank": 1,
      "species_code": "amcro",
      "species_name": "American Crow",
      "confidence": 0.873,
      "windows_detected": [0, 2, 4, 5, 6, 8, 10, 11],
      "frequency_range_hz": [200, 4000],
      "time_range_s": [0, 60]
    },
    {
      "rank": 2,
      "species_code": "grkis",
      "species_name": "Great Kiskadee",
      "confidence": 0.761,
      "windows_detected": [1, 3, 7, 9],
      "frequency_range_hz": [800, 5000],
      "time_range_s": [0, 60]
    }
  ],
  "processing_time_s": 45.2,
  "total_species_detected": 47
}
```

## 🎨 Frontend Pages

### Home Page (`/`)
- Landing page with project overview
- Quick start guide
- Key statistics

### Analyze Page (`/analyze`)
- Audio file upload (drag-drop)
- Real-time recording metadata display
- Processing stepper with status updates
- Analysis results:
  - Top 3 species highlight cards
  - Full detection table (all species)
  - Detection timeline (12 × 5-second windows)
  - Summary statistics

### Results Page (`/results`)
- Detailed breakdown per species
- Confidence distribution charts
- Waveform with temporal annotations
- Export options (CSV, JSON)

### How It Works (`/howitworks`)
- 7-step pipeline explanation
- Architecture diagrams
- Performance metrics
- Interactive step-by-step breakdown

### Dashboard (`/dashboard`)
- User analysis history
- Recorded statistics
- Previous uploads and results

### About Page (`/about`)
- Project background
- Team information
- References and citations

## 🔑 Key Features

### Metadata Display
- ⏱️ Recording duration
- 🎵 Sample rate (kHz)
- 💾 File size (MB)
- 📅 Upload timestamp
- 🎼 Audio format/codec
- 🆔 Unique recording ID
- 📍 GPS coordinates (if provided)

### Analysis Results
- 🎯 Species detection with confidence scores (0-100%)
- 📊 Detection timeline showing which 5-second windows contained each species
- 📈 Frequency range estimates per species
- ⏱️ Temporal localization (time-of-occurrence)
- 📉 Confidence distribution and statistics
- 🔗 Scientific names and taxonomy

### Advanced Features
- 🔐 JWT-based authentication
- 📝 Analysis history and dashboard
- 💾 Export results (CSV, JSON, PDF)
- 🌐 Multi-language support (extensible)
- ♿ WCAG 2.1 accessibility compliance
- 📱 Fully responsive design

## 📊 Performance Metrics

### Ranking Performance (Proto Branch)
| Metric | Value |
|--------|-------|
| Macro ROC-AUC | 0.9154 |
| Macro PR-AUC | 0.6475 |
| Interpretation | Excellent ranking; model distinguishes species well |

### Binary Classification Performance (Per-Class Thresholds)
| Metric | Value |
|--------|-------|
| Macro F1 | 0.0582 |
| Micro Precision | 0.0210 |
| Micro Recall | 0.6310 |
| Interpretation | High false positive rate due to 234-class imbalance; high recall for detections |

### Inference Performance
| Metric | Time |
|--------|------|
| Per 60-second recording | ~45 seconds |
| Per window (5 seconds) | ~3.75 seconds |
| Batch processing | Scales linearly |

## 🛠️ Development

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend_fixed/frontend\ -\ Copy
npm run test
```

### Code Style

```bash
# Backend: Black + Flake8
black app/
flake8 app/

# Frontend: ESLint + Prettier
npm run lint
npm run format
```

### Build for Production

```bash
# Backend
cd backend
pip install gunicorn
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker

# Frontend
cd frontend_fixed/frontend\ -\ Copy
npm run build
npm run preview  # Preview production build locally
```

## 🐛 Troubleshooting

### Backend Issues

**Error: CUDA not available**
```bash
# Use CPU-only version
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

**Error: Database connection failed**
- Check `.env` DATABASE_URL is correct
- Ensure PostgreSQL is running (or use SQLite for development)

**Error: Model files not found**
- Run `python app/model_loader.py` to download/initialize models
- Check `MODELS_DIR` path in config

### Frontend Issues

**Error: CORS policy blocked request**
- Backend must have `CORS_ORIGINS` configured
- Update `frontend/.env` VITE_API_URL to match backend

**Error: Waveform not rendering**
- Check browser console for errors
- Verify audio file is valid
- Try different audio format

## 🚢 Deployment

### Deploy to Heroku

```bash
# Backend
cd backend
heroku create birdclef-api
git push heroku main

# Frontend
cd frontend_fixed/frontend\ -\ Copy
vercel deploy --prod
```

### Deploy to AWS/GCP/Azure

See `deployment/` directory for Kubernetes manifests and IaC templates.

## 📚 Documentation

- **Backend API:** `http://localhost:8000/docs` (Swagger UI)
- **Frontend Storybook:** `npm run storybook`
- **Architecture:** See `docs/ARCHITECTURE.md`
- **API Reference:** See `docs/API.md`
- **Contributing:** See `CONTRIBUTING.md`

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/your-feature`)
3. Commit changes (`git commit -m 'Add your feature'`)
4. Push to branch (`git push origin feature/your-feature`)
5. Open Pull Request

See `CONTRIBUTING.md` for detailed guidelines.

## 📄 License

This project is licensed under the MIT License - see `LICENSE` file for details.

## 🙏 Acknowledgments

- **Perch Model** — Google AI for Soundscapes
- **BirdCLEF Competition** — Cornell Lab of Ornithology
- **Xeno-canto** — Global bird sound database
- **PyTorch Team** — Deep learning framework
- **FastAPI Team** — Modern web framework

## 📞 Support & Contact

- **Issues:** GitHub Issues
- **Discussions:** GitHub Discussions
- **Email:** support@wildecho.ai
- **Documentation:** https://wildecho-docs.readthedocs.io

## 🔄 Version History

### v1.0.0 (Current)
- ✅ 7-step pipeline with Perch + prototype matching
- ✅ Web UI with upload, metadata, results display
- ✅ JWT authentication and user accounts
- ✅ Analysis history and dashboard
- ✅ Export functionality (CSV, JSON)

### Planned (v1.1.0)
- 🔜 Real-time streaming analysis
- 🔜 Batch processing via CLI
- 🔜 Multi-language species names
- 🔜 Advanced filtering and search

---

**WildEcho** — *Listen to nature. Understand wildlife.* 🌍🦜🎵
