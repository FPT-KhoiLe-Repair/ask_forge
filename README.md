# 🎓 AskForge - AI-Powered E-Learning Platform

<div align="center">

![AskForge Banner](https://via.placeholder.com/800x200/4F46E5/FFFFFF?text=AskForge+-+Smart+Learning+Assistant)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15.2.4-black.svg)](https://nextjs.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)

**An intelligent learning platform that transforms PDF documents into interactive Q&A experiences using RAG and Question Generation**

[Features](#-features) • [Demo](#-demo) • [Installation](#-installation) • [Architecture](#-architecture) • [API Docs](#-api-documentation) • [Contributing](#-contributing)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Technology Stack](#-technology-stack)
- [Architecture](#-architecture)
- [Getting Started](#-getting-started)
- [Project Structure](#-project-structure)
- [API Documentation](#-api-documentation)
- [Configuration](#-configuration)
- [Development](#-development)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

**AskForge** is an advanced AI-powered educational platform that enables students to learn more effectively through intelligent question generation and document-based Q&A. By leveraging Retrieval-Augmented Generation (RAG) and state-of-the-art language models, AskForge transforms static PDF documents into dynamic, interactive learning experiences.

### 🌟 Why AskForge?

- **📚 Smart Document Processing**: Automatically indexes and chunks PDF documents for optimal retrieval
- **🤖 AI-Powered Q&A**: Uses Gemini & custom fine-tuned models for accurate, context-aware responses
- **💡 Question Generation**: Generates follow-up questions to encourage deeper learning
- **🎨 Modern UI/UX**: Beautiful, responsive interface built with Next.js and Tailwind CSS
- **⚡ High Performance**: FastAPI backend with async support and streaming responses
- **🔧 Modular Architecture**: Easy to extend with new models and features

---

## ✨ Key Features

### Core Capabilities

| Feature | Description |
|---------|-------------|
| 📄 **PDF Ingestion** | Upload multiple PDFs and automatically build searchable indexes |
| 🔍 **Semantic Search** | Vector-based retrieval using ChromaDB and sentence transformers |
| 💬 **Conversational AI** | Context-aware responses with conversation history management |
| 🎯 **Question Quality Assessment** | Evaluates and provides feedback on user questions (1-10 scale) |
| 🔄 **Follow-up Generation** | Automatically suggests relevant follow-up questions |
| 🌐 **Bilingual Support** | Full support for English and Vietnamese |
| 🎨 **Dark Mode** | Beautiful light/dark theme switching |
| 📊 **Model Thoughts Panel** | View AI reasoning and context retrieval in real-time |

### Technical Features

- **Streaming Responses**: Real-time token-by-token response generation using SSE
- **Background Job Processing**: Async question generation with AsyncIO queue
- **Multi-Model Support**: Seamless switching between Gemini and local HuggingFace models
- **LLM Router**: Intelligent routing based on task type and requirements
- **Persistent Storage**: Vector embeddings stored in ChromaDB with metadata
- **Conversation Memory**: Context-aware chat with sliding window memory
- **Hot-Reload Development**: Fast iteration with Next.js and Uvicorn
- **Docker Support**: One-command deployment with docker-compose

---

## 🛠 Technology Stack

### Backend
```
FastAPI          → High-performance async web framework
Python 3.11+     → Modern Python with type hints
ChromaDB         → Vector database for embeddings
Gemini API       → Google's generative AI for chat
HuggingFace      → Custom fine-tuned question generation models
LangChain        → LLM orchestration and RAG pipelines
Pydantic         → Data validation and settings management
Prometheus       → Metrics and monitoring
```

### Frontend
```
Next.js 15       → React framework with App Router
TypeScript       → Type-safe development
Tailwind CSS 4   → Utility-first styling
Shadcn/ui        → Beautiful, accessible components
Zustand          → Lightweight state management
Framer Motion    → Smooth animations
React Markdown   → Rich text rendering
```

### DevOps & Tools
```
Docker           → Containerization
Docker Compose   → Multi-container orchestration
Git              → Version control
pnpm             → Fast package manager
Uvicorn          → ASGI server
```

---

## 🏗 Architecture

### High-Level Architecture
```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Next.js App   │────────▶│   FastAPI Server │────────▶│   ChromaDB      │
│   (Frontend)    │         │    (Backend)     │         │  (Vector Store) │
└─────────────────┘         └──────────────────┘         └─────────────────┘
        │                            │                             │
        │                            ▼                             │
        │                    ┌───────────────┐                    │
        │                    │  LLM Router   │                    │
        │                    └───────────────┘                    │
        │                            │                             │
        │                    ┌───────┴────────┐                  │
        │                    ▼                ▼                   │
        │            ┌──────────────┐  ┌─────────────┐          │
        │            │ Gemini API   │  │ HuggingFace │          │
        │            │   (Chat)     │  │  (Q-Gen)    │          │
        │            └──────────────┘  └─────────────┘          │
        └───────────────────────────────────────────────────────┘
```

### Backend Architecture
```
backend/
├── app/
│   ├── main.py                      # FastAPI application entry
│   ├── core/
│   │   ├── config.py                # Settings & environment variables
│   │   ├── app_state.py             # Singleton state manager
│   │   └── logging.py               # Structured logging setup
│   ├── api/
│   │   ├── dependencies.py          # Dependency injection
│   │   └── routes/
│   │       ├── chat_routes.py       # Chat & streaming endpoints
│   │       └── index_routes.py      # Index management endpoints
│   ├── services/
│   │   ├── chat/
│   │   │   ├── service.py           # Chat orchestration
│   │   │   ├── pipeline.py          # RAG pipeline logic
│   │   │   └── schemas.py           # Pydantic models
│   │   ├── llm/
│   │   │   ├── registry.py          # LLM provider registry
│   │   │   ├── router.py            # Intelligent routing
│   │   │   └── adapters/            # Provider implementations
│   │   ├── indexing/
│   │   │   ├── pipeline.py          # PDF processing pipeline
│   │   │   └── chunking.py          # Text chunking strategies
│   │   └── queue/
│   │       └── async_queue.py       # Background job processing
│   ├── repositories/
│   │   └── vectorstore.py           # ChromaDB operations
│   └── utils/
│       ├── io.py                    # File I/O utilities
│       └── naming.py                # Index naming conventions
└── requirements.txt
```

### Frontend Architecture
```
frontend/
├── app/
│   ├── page.tsx                     # Main application page
│   ├── layout.tsx                   # Root layout with providers
│   ├── globals.css                  # Global styles & themes
│   └── api/
│       ├── chat.ts                  # Chat API & SSE handling
│       └── indexing.ts              # Index management API
├── components/
│   ├── topbar.tsx                   # Navigation bar
│   ├── index-panel.tsx              # PDF upload & index management
│   ├── chat-panel.tsx               # Main chat interface
│   ├── chat-message.tsx             # Message rendering
│   ├── model-thoughts-panel.tsx     # AI reasoning display
│   ├── followup_questions_pill.tsx  # Question suggestions
│   └── ui/                          # Reusable UI components
├── lib/
│   ├── store.ts                     # Zustand global state
│   ├── translations.ts              # i18n support
│   └── config.ts                    # Environment configuration
└── package.json
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Node.js 20+** - [Download](https://nodejs.org/)
- **pnpm** - `npm install -g pnpm`
- **Docker & Docker Compose** (optional) - [Download](https://www.docker.com/)
- **Gemini API Key** - [Get one here](https://makersuite.google.com/app/apikey)

### Option 1: Docker Compose (Recommended)

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/askforge.git
cd askforge
```

2. **Set up environment variables**
```bash
# Create .env file in backend/app/core/
echo "GEMINI_API_KEY=your_actual_api_key_here" > backend/app/core/.env
```

3. **Start the application**
```bash
docker-compose up --build
```

4. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option 2: Local Development

#### Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cat > app/core/.env << EOL
GEMINI_API_KEY=your_actual_api_key_here
GEMINI_MODEL_NAME=gemini-2.0-flash-exp
HF_PRELOAD_AT_STARTUP=True
HF_QUESTION_GENERATOR_CKPT=Qwen/qwen-security-final-question-reformatted
EOL

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup
```bash
cd frontend

# Install dependencies
pnpm install

# Set up environment
echo "NEXT_PUBLIC_API_BASE=http://localhost:8000" > .env.local

# Run development server
pnpm dev
```

---

## 📖 API Documentation

### Interactive Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Index Management
```http
POST /api/build_index
Content-Type: multipart/form-data

files: [file1.pdf, file2.pdf]
index_name: "my_study_material"
```
```http
GET /api/active_indexes

Response: {
  "ok": true,
  "active_indexes": ["index1", "index2"],
  "count": 2
}
```
```http
DELETE /api/index/{index_name}
```

#### Chat & Q&A
```http
POST /api/chat/stream
Content-Type: application/json

{
  "query_text": "What is photosynthesis?",
  "index_name": "biology_notes",
  "lang": "english",
  "n_results": 5,
  "min_rel": 0.2
}

Response: text/event-stream
data: {"type":"token","content":"Photosynthesis"}
data: {"type":"token","content":" is"}
data: {"type":"contexts","data":[...]}
data: {"type":"qg_job","job_id":"abc123","poll_url":"/api/chat/qg/abc123"}
data: [DONE]
```
```http
GET /api/chat/qg/{job_id}

Response: {
  "status": "completed",
  "job_id": "abc123",
  "questions": [
    "What are the main stages of photosynthesis?",
    "How does light intensity affect photosynthesis?",
    "What is the role of chlorophyll in photosynthesis?"
  ]
}
```

---

## ⚙️ Configuration

### Backend Configuration

Edit `backend/app/core/.env`:
```bash
# Core Settings
DEBUG=False
APP_PREFIX=/api

# Chunking Strategy
CHUNK_SIZE=1024          # Characters per chunk
CHUNK_OVERLAP=300        # Overlap between chunks
MIN_CHARS=300            # Minimum chunk size

# Storage
PAGES_JSON_DIR=data/user_db
CHROMA_PERSIST_DIR=.chroma

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Gemini API
GEMINI_API_KEY=your_key_here
GEMINI_MODEL_NAME=gemini-2.0-flash-exp

# HuggingFace Models
HF_QUESTION_GENERATOR_CKPT=Qwen/qwen-security-final-question-reformatted
HF_PRELOAD_AT_STARTUP=True
HF_DEVICE_MAP=auto
HF_DTYPE=bfloat16

# Queue (if using Redis)
REDIS_URL=redis://localhost:6379
```

### Frontend Configuration

Edit `frontend/.env.local`:
```bash
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

---

## 🔧 Development

### Backend Development
```bash
# Run with auto-reload
uvicorn app.main:app --reload

# Run tests
pytest

# Format code
black .
isort .

# Type checking
mypy .
```

### Frontend Development
```bash
# Development server
pnpm dev

# Build for production
pnpm build

# Start production server
pnpm start

# Lint code
pnpm lint
```

### Adding New Features

#### 1. Add a New LLM Provider
```python
# backend/app/services/llm/adapters/my_provider.py
from ask_forge.backend.app.services.llm.base import LLMProvider

class MyProviderAdapter(LLMProvider):
    async def generate(self, prompt: str, **kwargs) -> str:
        # Your implementation
        pass
    
    async def generate_stream(self, prompt: str, **kwargs):
        # Your implementation
        pass

# Register in app_state.py
self.llm_registry.register("my_provider", MyProviderAdapter())
```

#### 2. Add a New Route
```python
# backend/app/api/routes/my_routes.py
from fastapi import APIRouter

router = APIRouter(tags=["my_feature"])

@router.get("/my-endpoint")
async def my_endpoint():
    return {"message": "Hello World"}

# Register in main.py
from app.api.routes.my_routes import router as my_router
app.include_router(my_router, prefix="/api")
```

---

## 🚢 Deployment

### Docker Production Deployment
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Deployment

#### Backend (Gunicorn + Uvicorn Workers)
```bash
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

#### Frontend (Vercel/Netlify)
```bash
# Build
pnpm build

# Deploy to Vercel
vercel --prod

# Deploy to Netlify
netlify deploy --prod
```

---

## 📊 Performance & Monitoring

### Metrics Endpoint

Access Prometheus metrics at: `http://localhost:8000/metrics`

### Key Metrics

- Request latency (p50, p95, p99)
- Request rate
- Error rate
- Model inference time
- ChromaDB query time

### Health Check
```bash
curl http://localhost:8000/
# Response: {"message": "Welcome to Ask Forge!"}
```

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Code Style

- **Backend**: Follow PEP 8, use Black formatter
- **Frontend**: Follow Airbnb style guide, use Prettier
- **Commits**: Use conventional commits format

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **FastAPI** - Modern Python web framework
- **Anthropic & Google** - AI model providers
- **Shadcn/ui** - Beautiful component library
- **LangChain** - LLM orchestration tools
- **ChromaDB** - Vector database

---

## 📧 Contact

**Project Maintainer**: Your Name
- Email: your.email@example.com
- LinkedIn: [Your LinkedIn](https://linkedin.com/in/yourprofile)
- Portfolio: [yourportfolio.com](https://yourportfolio.com)

**Project Link**: [https://github.com/yourusername/askforge](https://github.com/yourusername/askforge)

---

<div align="center">

**⭐ Star this repo if you find it helpful!**

Made with ❤️ and ☕ by [Your Name]

</div>
