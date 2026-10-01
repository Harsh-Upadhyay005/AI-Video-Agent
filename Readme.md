<div align="center">

# 🎬 AI Video Agent

### Transform any video, audio, or document into searchable knowledge — instantly.

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org)
[![Whisper](https://img.shields.io/badge/Whisper-412991?style=for-the-badge&logo=openai&logoColor=white)](https://github.com/openai/whisper)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-FF6F00?style=for-the-badge&logo=databricks&logoColor=white)](https://www.trychroma.com)
[![Mistral AI](https://img.shields.io/badge/Mistral_AI-5A67D8?style=for-the-badge&logo=ai&logoColor=white)](https://mistral.ai)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com)

[Live Demo](#-quick-start) · [Architecture](#-architecture) · [API Docs](#-api-reference) · [Roadmap](#-feature-roadmap)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Feature Roadmap](#-feature-roadmap--future-ideas)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Environment Variables](#-environment-variables)
- [API Reference](#-api-reference)
- [Frontend](#-frontend)
- [Docker Deployment](#-docker-deployment)
- [Testing](#-testing)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🧠 Overview

**AI Video Agent** is a full-stack, production-ready application that transforms YouTube videos, audio files, PDF documents, and live voice dictation into structured, searchable knowledge using a **RAG (Retrieval-Augmented Generation)** pipeline.

### What It Does

| Input | Processing | Output |
|-------|-----------|--------|
| 🎥 YouTube URLs | Download → Audio extraction → STT | Indexed transcript |
| 🎙️ Audio files (MP3/WAV/M4A/FLAC/OGG/AAC) | Chunking → STT → Embedding | Searchable vector DB |
| 📹 Video files (MP4/AVI/MOV/MKV/WebM) | Audio extraction → STT → Embedding | Structured summaries |
| 📄 PDF documents | Text extraction → Embedding | Action items & Q&A |
| 🎤 Live voice dictation | Browser Speech API → AI cleanup | Clean executive prose |

### How It Works

```
User Input ──► Ingestion Pipeline (no LLM) ──► Vector Store (ChromaDB)
                                                       │
User Question ──► RAG Retrieval ──► Mistral LLM ──► Answer
```

> **Key Design Principle**: LLM is **never** used during content ingestion. It's only invoked when the user asks a question — keeping ingestion fast and cost-effective.

---

## 🚀 Feature Roadmap & Future Ideas

### ✅ Existing Features

| Feature | Description |
|---------|-------------|
| 🎥 YouTube Analysis | Paste any YouTube URL to auto-download, transcribe, and index |
| 📁 File Upload | Drag-and-drop support for 12+ audio/video/document formats |
| 🗣️ Dual STT Engines | **Faster Whisper** (local, 4-8x faster) + **Sarvam AI** (Hindi/Hinglish) |
| 📄 PDF Ingestion | Extract text from PDFs with metadata-aware chunking |
| 🔍 Hybrid RAG Search | Dense vector search (ChromaDB) + sparse BM25 + cross-encoder reranking |
| 💬 Interactive Chat | Real-time Q&A with conversation memory and intelligent query routing |
| 🧹 Dictation Lab | Live mic recording with AI-powered text cleanup via Mistral LLM |
| 📊 Smart Query Routing | Auto-detects "summarize" vs. "specific question" vs. "extraction" intent |
| 🌐 Multilingual | English + Hinglish (Hindi-English code-switching) support |
| 🔐 Authentication | Clerk-based frontend auth + Supabase JWT backend validation |
| ☁️ Cloud Storage | Optional Supabase cloud storage for uploaded files and results |
| 🐳 Docker Ready | Multi-stage Dockerfile + docker-compose with health checks |
| ⚡ SSE Progress | Real-time Server-Sent Events for long-running analysis jobs |
| 🧪 Test Suite | pytest-based backend tests with coverage |

### 🔮 Features You Can Add

Below are high-impact features that naturally extend the current architecture, ordered by implementation difficulty:

#### 🟢 Easy (1-3 days)

| Feature | Description | Where to Start |
|---------|-------------|----------------|
| 📝 **Transcript Export** | Export transcripts as SRT/VTT subtitles, DOCX, or plain text | Add export endpoint in `api/routes/analysis.py`, generate subtitle format from timestamped chunks |
| 🌙 **Dark Mode Toggle** | Full dark/light theme switching for the frontend | Add theme context in `frontend/src/contexts/`, toggle in `Header.tsx` |
| 📌 **Bookmark Answers** | Let users pin/bookmark important chat answers for later reference | Add a bookmarks array in `InteractiveChat.tsx`, persist to localStorage |
| 🔔 **Email Notifications** | Notify users via email when long analysis jobs complete | Add a notifications service in `core/`, use SendGrid or Resend SDK |
| 📋 **Copy Transcript** | One-click copy of the full transcript from the analysis result | Add a copy button in `AnalysisResultCard.tsx` |
| 🏷️ **Custom Tags & Labels** | Let users tag analyses with labels (e.g., "Meeting", "Lecture") | Add tags field in `AnalysisResultCard`, persist in Supabase |

#### 🟡 Medium (3-7 days)

| Feature | Description | Where to Start |
|---------|-------------|----------------|
| ⏱️ **Timestamp Navigation** | Click on specific timestamps in transcript to jump to that moment | Modify `core/transcriber.py` to output word-level timestamps, render clickable spans |
| 🗂️ **Analysis History Dashboard** | Persistent history of all past analyses with search/filter | Create new `AnalysisHistory.tsx` component, new Supabase table, API endpoints in `api/routes/` |
| 🔄 **Real-time Collaboration** | Multiple users can chat about the same document simultaneously | Add WebSocket support via `fastapi-websockets`, shared session rooms |
| 🌍 **Multi-Language Expansion** | Add Spanish, French, German, Japanese, etc. via Whisper lang codes | Extend `core/stt_service.py` language routing, add UI language dropdown |
| 📊 **Analytics Dashboard** | Show usage stats: videos processed, questions asked, avg response time | Add metrics middleware in `api/main.py`, create `AnalyticsDashboard.tsx` |
| 🔗 **Share Analysis Links** | Generate shareable public/private links for analysis results | Add share token generation in backend, public view route in frontend |
| 🎯 **Speaker Diarization** | Identify who said what in multi-speaker recordings | Integrate `pyannote-audio` or `NeMo` in `core/stt_service.py`, label chunks per speaker |
| 📰 **Automated Meeting Minutes** | Auto-generate structured meeting minutes with attendees, decisions, next steps | New `core/minutes_generator.py` using RAG retrieval + structured LLM prompts |

#### 🔴 Advanced (1-2 weeks+)

| Feature | Description | Where to Start |
|---------|-------------|----------------|
| 🎥 **Video Frame Analysis** | Extract and analyze key frames/slides from video using vision models | Add `core/vision_service.py` with GPT-4V or LLaVA, extract frames with ffmpeg |
| 📡 **Live Stream Ingestion** | Process live YouTube streams or Zoom calls in real-time | Add streaming pipeline in `core/audio_pipeline.py` with chunked processing |
| 🤖 **Multi-Model LLM Support** | Switch between GPT-4, Claude, Gemini, Llama alongside Mistral | Abstract `core/llm_service.py` to support multiple providers via LiteLLM |
| 🧩 **Plugin System** | Let users install custom analysis plugins (sentiment analysis, entity extraction, etc.) | Create `core/plugins/` directory with plugin registry and hooks |
| 📱 **Mobile App** | React Native or Flutter companion app with offline mode | Separate mobile project consuming the existing FastAPI backend |
| 🔌 **Slack/Teams Integration** | Bot that auto-summarizes meeting recordings posted in channels | Add `integrations/slack_bot.py` using Slack Bolt SDK |
| 🧬 **Knowledge Graph** | Build entity relationship graphs from analyzed content | Add `core/knowledge_graph.py` using Neo4j or NetworkX |
| 🎓 **Quiz Generator** | Auto-generate quizzes from educational video content | New `core/quiz_service.py` that uses RAG + structured LLM output |
| 🔐 **Role-Based Access Control** | Admin/viewer/editor roles with granular permissions per analysis | Extend `core/auth_middleware.py` with role hierarchy |
| 📈 **Batch Processing** | Upload a folder of 50+ files and process them all with a single click | Add batch queue in `api/routes/analysis.py`, use Celery or `asyncio.TaskGroup` |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     FRONTEND (React + Vite)                  │
│  ┌──────────┐ ┌─────────────┐ ┌──────────┐ ┌─────────────┐  │
│  │WisprHero │ │AudioVideo   │ │PDF       │ │Interactive  │  │
│  │  (Home)  │ │ Analyzer    │ │Analyzer  │ │   Chat      │  │
│  └──────────┘ └─────────────┘ └──────────┘ └─────────────┘  │
│  ┌──────────────────┐  ┌─────────────┐  ┌────────────────┐  │
│  │DictationPlayground│  │FeatureShow │  │ AuthPage       │  │
│  │  (Live Mic+AI)   │  │   case     │  │ (Clerk Auth)   │  │
│  └──────────────────┘  └─────────────┘  └────────────────┘  │
└──────────────────────────┬───────────────────────────────────┘
                           │ HTTP / SSE
┌──────────────────────────▼───────────────────────────────────┐
│                    BACKEND (FastAPI)                          │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐   │
│  │ /api/v1/    │  │ /api/v1/chat │  │ /api/v1/upload    │   │
│  │   analyze   │  │              │  │                   │   │
│  └──────┬──────┘  └──────┬───────┘  └────────┬──────────┘   │
│         │                │                    │              │
│  ┌──────▼──────────────────────────────────────▼──────────┐  │
│  │                PIPELINE ORCHESTRATOR                    │  │
│  │  Source Detection → Ingestion → Validation → RAG Index │  │
│  └──────┬──────────────────┬──────────────────┬──────────┘  │
│         │                  │                  │              │
│  ┌──────▼─────┐  ┌────────▼───────┐  ┌──────▼──────────┐  │
│  │ STT Service│  │ PDF Pipeline   │  │ RAG Engine      │  │
│  │ (Whisper / │  │ (PyPDF2)       │  │ (ChromaDB +     │  │
│  │  Sarvam)   │  │                │  │  BM25 + Rerank) │  │
│  └────────────┘  └────────────────┘  └──────┬──────────┘  │
│                                              │              │
│                                    ┌─────────▼──────────┐   │
│                                    │  LLM Service       │   │
│                                    │  (Mistral AI)      │   │
│                                    │  Lazy Init on Query│   │
│                                    └────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### Pipeline Flow

1. **Ingestion** (No LLM) — Content is downloaded/extracted and transcribed
2. **Indexing** (No LLM) — Text is chunked, embedded, and stored in ChromaDB
3. **Querying** (LLM used) — User questions trigger RAG retrieval → Mistral LLM answers

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|-----------|---------|
| **FastAPI** | Async REST API with auto-docs, SSE streaming |
| **faster-whisper** | CTranslate2-optimized local speech-to-text (4-8x faster) |
| **Sarvam AI** | Hindi/Hinglish speech-to-text API |
| **Mistral AI** | LLM for question answering and text analysis |
| **ChromaDB** | Vector database for semantic search |
| **sentence-transformers** | `all-MiniLM-L6-v2` embedding model |
| **rank-bm25** | Sparse retrieval for hybrid search |
| **LangChain** | LLM orchestration and prompt management |
| **yt-dlp** | YouTube video/audio downloader |
| **PyPDF2** | PDF text extraction |
| **Supabase** | Auth (JWT), cloud storage, PostgreSQL |

### Frontend
| Technology | Purpose |
|-----------|---------|
| **React 18** | UI framework with TypeScript |
| **Vite** | Lightning-fast build tooling |
| **TailwindCSS** | Utility-first styling |
| **Framer Motion** | Animations and transitions |
| **Clerk** | Authentication provider |
| **Lucide React** | Icon library |
| **React Markdown** | Markdown rendering in chat |

---

## ⚡ Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **FFmpeg** (for audio processing)
- **Mistral AI API Key** ([get one here](https://console.mistral.ai/))

### 1. Clone the Repository

```bash
git clone https://github.com/Harsh-Upadhyay005/AI-Video-Agent.git
cd AI-Video-Agent
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your API keys:
# MISTRAL_API_KEY=your_key_here       (required)
# SARVAM_API_KEY=your_key_here        (optional, for Hinglish)
```

### 4. Start Backend Server

```bash
# Using uvicorn directly
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Or using the start script (Windows)
start.bat
```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

### 5. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy example env
cp .env.example .env
# Edit frontend/.env:
# VITE_API_URL=http://localhost:8000
# VITE_CLERK_PUBLISHABLE_KEY=pk_test_your_key_here

# Start dev server
npm run dev
```

The frontend will be available at `http://localhost:5173`.

---

## 🔐 Environment Variables

### Backend (`.env` in project root)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MISTRAL_API_KEY` | ✅ | — | Mistral AI API key for LLM operations |
| `SARVAM_API_KEY` | ❌ | — | Sarvam AI key (required for Hinglish transcription) |
| `ENVIRONMENT` | ❌ | `development` | `development` / `staging` / `production` |
| `WHISPER_MODEL` | ❌ | `small` | Whisper model: `tiny`, `base`, `small`, `medium`, `large` |
| `WHISPER_DEVICE` | ❌ | `auto` | `auto` / `cpu` / `cuda` |
| `WHISPER_COMPUTE_TYPE` | ❌ | `int8` | `int8` / `float16` / `float32` |
| `VECTOR_DB_DIR` | ❌ | `vector_db` | ChromaDB persistence directory |
| `EMBEDDING_MODEL` | ❌ | `all-MiniLM-L6-v2` | Sentence-transformers embedding model |
| `MAX_UPLOAD_SIZE_MB` | ❌ | `500` | Maximum upload file size |
| `CORS_ORIGINS` | ❌ | `localhost:5173` | Comma-separated allowed CORS origins |
| `LOG_LEVEL` | ❌ | `INFO` | Logging level |
| `SUPABASE_URL` | ❌ | — | Supabase project URL (for cloud storage) |
| `SUPABASE_ANON_KEY` | ❌ | — | Supabase anonymous key |

### Frontend (`frontend/.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_URL` | ❌ | `http://localhost:8000` | Backend API URL |
| `VITE_CLERK_PUBLISHABLE_KEY` | ✅ | — | Clerk authentication key |
| `VITE_SUPABASE_URL` | ❌ | — | Supabase URL for client-side auth |
| `VITE_SUPABASE_ANON_KEY` | ❌ | — | Supabase anonymous key |

---

## 📡 API Reference

### Analysis Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/v1/analyze` | Start async analysis (returns job_id) | Optional |
| `POST` | `/api/v1/analyze/sync` | Synchronous analysis (blocks until done) | Optional |
| `POST` | `/api/v1/upload` | Upload file + start analysis | Optional |
| `GET` | `/api/v1/progress/{job_id}` | SSE stream of progress updates | No |
| `GET` | `/api/v1/status/{job_id}` | Poll job status | No |

### Chat Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/v1/chat` | Ask question about analyzed content | Optional |
| `DELETE` | `/api/v1/chat/session/{id}` | Clear chat session | No |
| `GET` | `/api/v1/chat/storage/health` | RAG storage health status | No |

### Health & System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Basic health check |
| `GET` | `/health/detailed` | Detailed system health |
| `GET` | `/` | API info |

### Example: Analyze a YouTube Video

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"source": "https://youtube.com/watch?v=VIDEO_ID", "language": "english"}'
```

### Example: Chat with Content

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the key decisions?", "session_id": "JOB_ID"}'
```

---

## 🎨 Frontend

The frontend is a premium React + Vite SPA with:

### Pages & Components

| Component | Description |
|-----------|-------------|
| `WisprHero` | Animated hero section with SVG waveform marquee |
| `DictationPlayground` | **Live** mic recording (Web Speech API) + AI-powered text cleanup via Mistral |
| `AudioVideoAnalyzer` | YouTube URL input + drag-and-drop file upload |
| `PDFAnalyzer` | PDF document upload and analysis |
| `InteractiveChat` | RAG-powered Q&A with markdown rendering, preset questions |
| `AnalysisResultCard` | Displays transcript, summary, action items, key decisions |
| `FeatureShowcase` | Feature grid with icons and descriptions |
| `AuthPage` | Clerk-powered sign-in/sign-up |
| `UserProfile` | User profile management with data export |

### Dictation Lab (Now Active! 🎙️)

The Dictation Lab is fully functional:

1. **Click "Record Mic"** — uses the browser's Web Speech API for real-time speech-to-text
2. **Speak naturally** — your words appear live in the text area (including filler words)
3. **Click "AI Cleanup"** — sends your raw dictation to the Mistral LLM backend, which returns:
   - 📝 Executive Summary
   - ✅ Action Items
   - 🎯 Key Decision
4. **Or use presets** — switch between sample dictation texts
5. **Works offline** — if the backend is down, a local fallback provides basic text cleanup

> **Browser Support**: Chrome, Edge, and Safari support the Speech Recognition API. Firefox has limited support.

---

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f ai-video-agent

# Stop
docker-compose down
```

### Manual Docker Build

```bash
docker build -t ai-video-agent .
docker run -p 8000:8000 --env-file .env ai-video-agent
```

### Resource Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 2 GB | 4-8 GB |
| GPU | None (CPU works) | NVIDIA GPU (10-50x faster STT) |
| Storage | 2 GB | 10+ GB (for models + vector DB) |

---

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=core --cov=api --cov-report=html

# Run specific test file
pytest tests/test_api.py -v

# Run with verbose output
pytest -v --tb=short
```

### Test Coverage

| Module | Tests |
|--------|-------|
| `test_api.py` | API endpoint integration tests |
| `test_audio_processor.py` | Audio processing unit tests |
| `test_config.py` | Configuration validation tests |
| `test_security.py` | Security module tests |
| `test_summarizer.py` | Summarization tests |
| `test_validators.py` | Input validation tests |

---

## 📁 Project Structure

```
AI-Video-Agent/
├── api/                          # FastAPI application
│   ├── main.py                   # App entry, middleware, lifespan
│   └── routes/
│       ├── analysis.py           # /analyze, /upload, /progress endpoints
│       ├── chat.py               # /chat endpoint with RAG
│       ├── health.py             # Health check endpoints
│       └── account.py            # Account management
├── core/                         # Core business logic
│   ├── audio_pipeline.py         # Audio/video ingestion pipeline
│   ├── pdf_pipeline.py           # PDF ingestion pipeline
│   ├── stt_service.py            # Speech-to-text (Whisper + Sarvam)
│   ├── rag_engine.py             # RAG chain with hybrid search
│   ├── llm_service.py            # Mistral LLM orchestration
│   ├── vector_store.py           # ChromaDB + BM25 + reranking
│   ├── query_router.py           # Intelligent query classification
│   ├── whole_content_processor.py# Map-reduce summarization
│   ├── analysis_service.py       # Analysis extraction service
│   ├── config.py                 # Configuration management
│   ├── auth_middleware.py        # JWT authentication
│   ├── security.py               # Security checks
│   ├── validators.py             # Input validation
│   ├── reranker.py               # Cross-encoder reranking
│   ├── mistral_client.py         # Mistral API client with retry
│   ├── supabase_client.py        # Supabase integration
│   ├── supabase_database.py      # Database operations
│   ├── supabase_storage.py       # Cloud file storage
│   ├── rag_storage.py            # RAG chain persistence
│   ├── resource_manager.py       # System resource management
│   ├── health_check.py           # System health monitoring
│   └── logger.py                 # Structured logging
├── utils/                        # Utility modules
│   ├── audio_processor.py        # FFmpeg audio processing
│   ├── document_chunker.py       # Text chunking strategies
│   ├── file_manager.py           # File upload management
│   └── pdf_processor.py          # PDF text extraction
├── frontend/                     # React + Vite frontend
│   └── src/
│       ├── App.tsx               # Main app with routing
│       ├── api/client.js         # Backend API client (SSE polling)
│       ├── components/           # UI components (15 files)
│       ├── contexts/             # Auth context
│       ├── lib/                  # Clerk + Supabase clients
│       └── types/                # TypeScript type definitions
├── tests/                        # Test suite
├── docs/                         # Documentation
├── main.py                       # CLI entry point + pipeline orchestrator
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Multi-stage production build
├── docker-compose.yml            # Container orchestration
├── start.bat                     # Windows start script
└── .env.example                  # Environment template
```

---

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m 'Add amazing feature'`
4. **Push** to the branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

### Development Tips

- Backend auto-reloads with `--reload` flag on uvicorn
- Frontend auto-reloads with Vite HMR
- API docs available at `http://localhost:8000/docs` (Swagger) and `http://localhost:8000/redoc`
- Check `logs/` directory for detailed backend logs

---

## 📄 License

This project is open source. See the repository for license details.

---

<div align="center">

**Built with ❤️ by [Harsh Upadhyay](https://github.com/Harsh-Upadhyay005)**

⭐ Star this repo if you find it useful!

</div>
