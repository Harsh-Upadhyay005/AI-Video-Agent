# 🎥 AI Video Agent

**Transform video/audio content into actionable insights using AI.**

Automatically transcribe, summarize, and chat with your video/audio files (YouTube, MP3, MP4, PDF) using OpenAI Whisper, Mistral AI, and RAG technology.

---

## ✨ Features

- 🎬 **Multiple Input Sources**: YouTube URLs, MP3/MP4 files, PDF documents
- 🗣️ **Multi-Language**: English and Hinglish (Hindi+English) support
- 📝 **Auto-Transcription**: OpenAI Whisper + Sarvam AI for accurate transcription
- 🤖 **AI Analysis**: Auto-generate summaries, action items, and key decisions
- 💬 **RAG Chat**: Ask questions about your content with intelligent query routing
- ☁️ **Cloud Storage**: Optional Supabase integration for permanent file storage
- 🎨 **Modern UI**: Beautiful React frontend with real-time progress tracking

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+ (for frontend)
- FFmpeg (for audio processing)

### 1. Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Install frontend packages
cd frontend
npm install
cd ..
```

### 2. Configure Environment

```bash
# Copy example environment file
copy .env.example .env

# Edit .env and add your API keys:
# - MISTRAL_API_KEY (required)
# - SARVAM_API_KEY (for Hinglish)
# - SUPABASE_URL & SUPABASE_ANON_KEY (optional, for cloud storage)
```

### 3. Start the Application

```bash
# Start backend
python -m uvicorn api.main:app --reload

# In another terminal, start frontend
cd frontend
npm run dev
```

### 4. Open in Browser

Navigate to: http://localhost:5173

---

## 📚 Documentation

All documentation is in the **`docs/`** folder:

### Getting Started
- **[START_HERE.md](docs/START_HERE.md)** - Complete setup guide
- **[QUICKSTART.txt](QUICKSTART.txt)** - Quick start commands

### Features
- **[ENHANCED_RAG_GUIDE.md](docs/ENHANCED_RAG_GUIDE.md)** - Advanced RAG with query routing
- **[PDF_SUPPORT_GUIDE.md](docs/PDF_SUPPORT_GUIDE.md)** - Upload and analyze PDFs
- **[FILE_UPLOAD_FEATURE.md](docs/FILE_UPLOAD_FEATURE.md)** - File upload documentation

### Supabase Integration (Optional)
- **[SUPABASE_SETUP_GUIDE.md](docs/SUPABASE_SETUP_GUIDE.md)** - Complete setup tutorial
- **[SUPABASE_INTEGRATION_SUMMARY.md](docs/SUPABASE_INTEGRATION_SUMMARY.md)** - Quick reference
- **[supabase_setup.sql](docs/supabase_setup.sql)** - Database schema

### Architecture & Development
- **[ARCHITECTURE_DIAGRAM.md](docs/ARCHITECTURE_DIAGRAM.md)** - System architecture
- **[FRONTEND_INTEGRATION_GUIDE.md](docs/FRONTEND_INTEGRATION_GUIDE.md)** - Frontend details

---

## 🎯 Usage

### Upload & Analyze

1. **YouTube URL**: Paste any YouTube video URL
2. **Audio/Video File**: Upload MP3, MP4, WAV, etc.
3. **PDF Document**: Upload and analyze PDF documents
4. **Select Language**: English or Hinglish
5. **Click Analyze**: Watch real-time progress
6. **Get Results**: Summary, transcript, action items, and more

### Chat with Your Content

Ask questions about your processed content:

**Local Questions** (specific):
- "What is RAG?"
- "What does page 5 say about AI?"

**Global Questions** (whole document):
- "What are the 7 key concepts discussed?"
- "Summarize the entire video"
- "List all main topics covered"

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **OpenAI Whisper** - Speech-to-text transcription
- **Mistral AI** - LLM for summarization and insights
- **ChromaDB** - Vector database for RAG
- **LangChain** - LLM orchestration
- **Supabase** - Optional cloud storage (Python SDK)

### Frontend
- **React** + **Vite** - Fast modern UI
- **TailwindCSS** - Utility-first styling
- **Lucide Icons** - Beautiful icons

### Processing
- **FFmpeg** - Audio/video processing
- **PyPDF2** - PDF text extraction
- **yt-dlp** - YouTube downloader

---

## 📦 Project Structure

```
AI Video Agent/
├── api/                    # FastAPI backend
│   ├── main.py            # Main API app
│   └── routes/            # API endpoints
├── core/                   # Core business logic
│   ├── transcriber.py     # Whisper transcription
│   ├── rag_engine.py      # RAG with query routing
│   ├── supabase_*.py      # Supabase integration
│   └── ...
├── frontend/              # React frontend
│   └── src/
│       └── components/    # UI components
├── utils/                 # Utility functions
├── docs/                  # 📚 All documentation
├── requirements.txt       # Python dependencies
└── .env.example          # Environment template
```

---

## 🔧 Configuration

### Required Environment Variables

```env
# Mistral AI (Required)
MISTRAL_API_KEY=your_mistral_api_key

# Sarvam AI (Required for Hinglish)
SARVAM_API_KEY=your_sarvam_api_key
```

### Optional Environment Variables

```env
# Supabase (For cloud storage)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key

# Whisper Configuration
WHISPER_MODEL=small  # tiny, base, small, medium, large
```

See `.env.example` for all options.

---

## 🎨 Features in Detail

### Enhanced RAG System
- **Query Routing**: Automatically classifies questions as local or global
- **Multi-Strategy Retrieval**: Different approaches for different question types
- **Global Metadata**: Precomputed topics and concepts for fast whole-video queries
- **Map-Reduce**: Handles long transcripts with hierarchical summarization

### Supabase Integration (Optional)
- **Permanent Storage**: Files stored forever in cloud
- **Public URLs**: Direct links to download files
- **Metadata Database**: Track all processed files
- **Multi-Device Access**: Access from anywhere

### File Upload Support
- **Multiple Formats**: MP3, MP4, WAV, M4A, AVI, MOV, MKV, WebM, PDF
- **Large Files**: Up to 500MB
- **Drag & Drop**: Easy file upload interface
- **Progress Tracking**: Real-time processing status

---

## 🧪 Testing

```bash
# Test RAG query routing
python test_enhanced_rag.py

# Test environment configuration
python test_env_loading.py
```

---

## 🐛 Troubleshooting

### Backend Won't Start
- Check `.env` file has required API keys
- Verify Python packages installed: `pip install -r requirements.txt`
- Check FFmpeg is installed: `ffmpeg -version`

### Frontend Won't Start
- Verify Node.js installed: `node --version`
- Install packages: `cd frontend && npm install`
- Check port 5173 is available

### Transcription Fails
- Verify API keys in `.env` are correct (no quotes!)
- Check internet connection for YouTube downloads
- Ensure audio files are valid formats

See **[docs/](docs/)** folder for detailed troubleshooting guides.

---

## 📝 Scripts

### Backend
- `start.bat` - Start backend server
- `install_pdf_support.bat` - Install PDF support
- `install_supabase.bat` - Install Supabase SDK

### Frontend
- `frontend/RESTART_FRONTEND.bat` - Restart frontend

---

## 🤝 Contributing

Contributions welcome! This is an open development project.

---

## 📄 License

This project is open source. See individual package licenses for dependencies.

---

## 🎉 Credits

Built with:
- OpenAI Whisper
- Mistral AI
- Sarvam AI
- LangChain
- Supabase
- FastAPI
- React

---

## 📞 Support

- **Documentation**: Check the `docs/` folder
- **Issues**: Review troubleshooting guides in docs
- **Logs**: Check `logs/` directory for error details

---

## 🚀 What's Next?

- ✅ Enhanced RAG with query routing
- ✅ PDF document support
- ✅ Supabase cloud storage
- 🔜 OCR for scanned PDFs
- 🔜 Multi-document queries
- 🔜 User authentication
- 🔜 Export to Notion/Markdown

---

**Made with ❤️ for developers who want to make video content searchable and actionable.**

**Start here**: Read `docs/START_HERE.md` for complete setup instructions!
