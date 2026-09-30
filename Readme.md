<div align="center">

# 🎬 videoQuery • AI Video Agent
### Intelligent Multi-Modal Video, Audio & Document Intelligence Platform

**Transform YouTube videos, audio recordings, and PDF documents into structured transcripts, executive summaries, and interactive RAG-powered conversations.**

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Clerk](https://img.shields.io/badge/Clerk-Authentication-6C47FF?style=for-the-badge&logo=clerk&logoColor=white)](https://clerk.com)
[![Whisper](https://img.shields.io/badge/OpenAI-Whisper-412991?style=for-the-badge&logo=openai&logoColor=white)](https://github.com/openai/whisper)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-FF6F61?style=for-the-badge)](https://www.trychroma.com)

[Explore Features](#-key-features) • [Architecture](#-architecture) • [Quick Start](#-quick-start) • [Environment Setup](#-configuration) • [Documentation](#-documentation)

</div>

---

## 🌟 Overview

**videoQuery (AI Video Agent)** is a full-stack, enterprise-grade multi-modal AI platform designed to eliminate hours of manual note-taking and video reviews. By pairing local speech-to-text models with modern vector search and Large Language Models, videoQuery transcribes media in seconds, indexes knowledge into ChromaDB, and allows users to converse directly with video or document content using Retrieval-Augmented Generation (RAG).

---

## ✨ Key Features

### 🎥 Multi-Format Media Ingestion
- **YouTube Ingestion**: Download and extract high-bitrate audio directly from YouTube links via `yt-dlp`.
- **Local Audio/Video Upload**: Supports MP3, MP4, WAV, M4A, FLAC, OGG, AAC, MOV, MKV, WebM, and AVI (up to 500MB).
- **PDF Document Processing**: Upload whitepapers, research articles, or meeting decks for automated text extraction and vector indexing.

### 🎙️ Dual-Engine Speech-to-Text
- **OpenAI Whisper (Local)**: High-accuracy transcription running on CPU or NVIDIA CUDA GPU (`tiny`, `base`, `small`, `medium`, `large-v3`).
- **Sarvam AI Engine**: State-of-the-art Hindi and Hinglish (code-switched speech) transcription for bilingual audio.

### 🧠 Intelligent Vector RAG Engine
- **Query Routing**: Automatically classifies queries into `LOCAL_QA` (specific timestamps/sections), `GLOBAL_SUMMARY` (macro insights), or `TOPIC_EXTRACTION`.
- **ChromaDB Integration**: Local high-speed vector embeddings generated via `sentence-transformers/all-MiniLM-L6-v2`.
- **Executive Synthesis**: Powered by Mistral AI (`mistral-small-latest`) to generate summaries, action items, key decisions, and timestamped answers.

### 🔐 Clerk Authentication & Studio Security
- **Protected Video Studio**: Access to media analyzers is guarded by Clerk authentication.
- **Project-Themed UI**: Beautiful authentication videoQuerys customized with the project's cream (`#FDFCF0`) and lavender (`#D9CCF5`) design tokens.
- **Top Navigation User Button**: Seamless profile management and sign-out controls built directly into the header.

### 📱 Premium, Fully Responsive UX
- **Fluid Design System**: Baskervville editorial serif typography combined with Inter body text and dynamic soundwave animations.
- **Dictation Playground**: Live benchmark simulation showing 120x speedup over manual video review.
- **Mobile-First Responsive Layout**: Optimized across smartphones, tablets, laptops, and ultra-wide displays.

---

## 🏗️ Architecture

```
                    ┌───────────────────────────────────┐
                    │      React 18 + Vite Frontend     │
                    │  (Tailwind CSS + Clerk Auth SDK)  │
                    └─────────────────┬─────────────────┘
                                      │ REST API / JSON
                                      ▼
                    ┌───────────────────────────────────┐
                    │       FastAPI Backend Server      │
                    │      (Input Validation & CORS)    │
                    └───────┬───────────────────┬───────┘
                            │                   │
             Media Ingest   ▼                   ▼   Documents
    ┌───────────────────────────────┐   ┌───────────────────────────────┐
    │       Audio / Video Engine    │   │         PDF Processor         │
    │  - yt-dlp (YouTube stream)    │   │  - PyPDF2 text extraction     │
    │  - FFmpeg (16kHz mono audio)  │   │  - Page-level segmentation    │
    │  - OpenAI Whisper / Sarvam AI │   └───────────────┬───────────────┘
    └───────────────┬───────────────┘                   │
                    │                                   │
                    ▼                                   ▼
    ┌ ────────────────┐
    │              Chunking & ChromaDB Vector Store                     │
    │     (sentence-transformers/all-MiniLM-L6-v2 Embeddings)           │
    └─────────────────────────────────┬─────────────────────────────────┘
                                      │
                                      ▼
    ┌ ────────────────┐
    │               RAG Engine & Intelligent Query Router               │
    │      - LOCAL_QA (Top-8 Vector Chunk Retrieval)                    │
    │      - GLOBAL_SUMMARY (Precomputed Macro Metadata)                │
    │      - LLM Synthesis via Mistral AI                               │
    └─────────────────────────────────┬─────────────────────────────────┘
                                      │
                                      ▼
                    ┌───────────────────────────────────┐
                    │   Interactive Streaming Q&A Chat  │
                    └───────────────────────────────────┘
```

---

## 📁 Project Structure

```
AI Video Agent/
├── api/                       # FastAPI routes, schemas, and endpoints
│   ├── main.py                # Server entrypoint and CORS middleware
│   └── routes/                # Endpoint handlers (analysis, chat, health)
├── core/                      # Application core logic & AI services
│   ├── transcriber.py         # Whisper & Sarvam AI transcription
│   ├── rag_engine.py          # Vector retrieval and query router
│   ├── vector_store.py        # ChromaDB embeddings manager
│   ├── global_metadata.py     # Macro summaries and concept storage
│   ├── global_analyzer.py     # Hierarchical map-reduce analyzer
│   ├── pdf_processor.py       # PDF document parser
│   ├── supabase_client.py     # Optional cloud storage client
│   └── validators.py          # Security & file sanity checks
├── frontend/                  # Modern React + Vite application
│   ├── src/
│   │   ├── components/        # UI components (Header, Studio, Chat, Auth)
│   │   ├── contexts/          # State and auth context providers
│   │   ├── lib/               # Clerk & Supabase configurations
│   │   ├── types/             # TypeScript interface definitions
│   │   ├── App.tsx            # Main application router and state
│   │   └── index.css          # Design system, animations & utilities
│   ├── package.json           # Frontend dependencies
│   ├── vite.config.ts         # Vite bundler configuration
│   └── tailwind.config.js     # Tailwind CSS theme extension
├── docs/                      # Technical feature guides & SQL schemas
│   ├── ARCHITECTURE_DIAGRAM.md
│   ├── ENHANCED_RAG_GUIDE.md
│   ├── FILE_UPLOAD_FEATURE.md
│   ├── PDF_SUPPORT_GUIDE.md
│   ├── SUPABASE_SETUP_GUIDE.md
│   ├── YOUTUBE_DOWNLOAD_TROUBLESHOOTING.md
│   └── supabase_setup.sql
├── tests/                     # Automated Pytest test suite
│   ├── test_api.py
│   ├── test_validators.py
│   └── conftest.py
├── requirements.txt           # Python backend dependencies
├── .env.example               # Root environment variable template
└── README.md                  # Project documentation
```

---

## 🚀 Quick Start

### Prerequisites
- **Python**: Version `3.9` or higher
- **Node.js**: Version `18.x` or higher
- **FFmpeg**: Required for audio normalization and video slicing ([Download FFmpeg](https://ffmpeg.org/download.html))

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/Harsh-Upadhyay005/AI-Video-Agent.git
cd "AI Video Agent"
```

---

### Step 2: Set Up Backend Environment

```bash
# Create and activate Python virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\activate

# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Create your `.env` file from the template:
```bash
cp .env.example .env
```

---

### Step 3: Set Up Frontend & Clerk Auth

```bash
cd frontend
npm install
```

Create your `frontend/.env` file:
```bash
cp .env.example .env
```

Add your Clerk publishable key from your [Clerk Dashboard](https://dashboard.clerk.com):
```env
VITE_API_URL=http://localhost:8000
VITE_CLERK_PUBLISHABLE_KEY=pk_test_your_clerk_publishable_key_here
```

---

### Step 4: Run the Application

#### Terminal 1 — Start FastAPI Backend:
```bash
# In the project root (with .venv active)
python -m uvicorn api.main:app --reload --port 8000
```
*API will be live at `http://localhost:8000` (Interactive Swagger Docs at `http://localhost:8000/docs`).*

#### Terminal 2 — Start React Frontend:
```bash
cd frontend
npm run dev
```
*Frontend will launch at `http://localhost:5173`.*

---

## ⚙️ Configuration Reference

### Backend (`.env`)
| Variable | Required | Description | Default |
|:---|:---:|:---|:---|
| `MISTRAL_API_KEY` | **Yes** | API key from [Mistral AI Console](https://console.mistral.ai/) | — |
| `MISTRAL_MODEL` | No | LLM model name | `mistral-small-latest` |
| `WHISPER_MODEL` | No | Whisper model size (`tiny`, `base`, `small`, `medium`, `large-v3`) | `small` |
| `WHISPER_DEVICE` | No | Execution device (`auto`, `cpu`, `cuda`) | `auto` |
| `WHISPER_COMPUTE_TYPE` | No | Model quantization (`int8`, `float16`, `float32`) | `int8` |
| `SARVAM_API_KEY` | Optional | API key from [Sarvam AI](https://sarvam.ai/) for Hinglish speech | — |
| `SUPABASE_URL` | Optional | Supabase project URL for cloud file storage | — |
| `SUPABASE_ANON_KEY` | Optional | Supabase public anonymous key | — |
| `MAX_UPLOAD_SIZE_MB` | No | Maximum file upload limit in megabytes | `500` |

### Frontend (`frontend/.env`)
| Variable | Required | Description |
|:---|:---:|:---|
| `VITE_API_URL` | **Yes** | Backend FastAPI server URL (`http://localhost:8000`) |
| `VITE_CLERK_PUBLISHABLE_KEY` | **Yes** | Publishable key from [Clerk Dashboard](https://dashboard.clerk.com) (`pk_test_...`) |

---

## 📡 API Endpoints Overview

| Method | Endpoint | Description |
|:---|:---|:---|
| `GET` | `/api/health/ping` | Health check & connectivity probe |
| `POST` | `/api/v1/analyze` | Start asynchronous analysis for YouTube URL |
| `GET` | `/api/v1/status/{job_id}` | Poll progress and retrieve completed analysis |
| `POST` | `/api/v1/upload` | Multipart file upload and analysis (Audio/Video/PDF) |
| `POST` | `/api/v1/chat` | Send question to vector RAG engine with session context |
| `DELETE`| `/api/v1/chat/session/{id}` | Clear conversation session cache |

---

## 📚 Technical Documentation

Explore detailed documentation in the [`docs/`](docs/) directory:
- 🏛️ **[System Architecture](docs/ARCHITECTURE_DIAGRAM.md)**: Deep dive into component interaction and data videoQuerys.
- 🔍 **[Enhanced RAG Guide](docs/ENHANCED_RAG_GUIDE.md)**: Query routing strategies and map-reduce summarization.
- 📁 **[File Upload Engine](docs/FILE_UPLOAD_FEATURE.md)**: Handling multi-format audio and video processing pipelines.
- 📄 **[PDF Analysis Guide](docs/PDF_SUPPORT_GUIDE.md)**: Document segmentation and text extraction architecture.
- ☁️ **[Supabase Cloud Setup](docs/SUPABASE_SETUP_GUIDE.md)**: Setting up permanent cloud storage buckets and metadata schemas.
- 🛠️ **[YouTube Troubleshooting](docs/YOUTUBE_DOWNLOAD_TROUBLESHOOTING.md)**: Resolving common `yt-dlp` stream extraction errors.

---

## 🧪 Testing

Run unit and integration tests using pytest:

```bash
# Run all tests
pytest

# Run tests with output verbosity
pytest -v -s

# Run specific validator test
pytest tests/test_validators.py
```

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

<div align="center">

**Built with precision using OpenAI Whisper, Mistral AI, ChromaDB, and React.**

⭐ If you find this project helpful, give it a star on GitHub!

</div>
