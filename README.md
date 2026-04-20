# Cyrus AI 🤖

> **Your intelligent coding assistant** – chat, voice input, conversation memory search, multilingual support, and a plug-in architecture to add any LLM provider later.

Built as a student-friendly MVP using:
- **FastAPI** backend (sessions, chat, embeddings, Qdrant vector search, STT/TTS hooks)
- **Qdrant** vector database (conversation memory)
- **Next.js 15 + Tailwind CSS** frontend (mobile-first, WhatsApp-style voice recording)
- **Docker Compose** for one-command local stack

---

## Screenshots

| Chat | History Tiles |
|------|--------------|
| Mobile-first responsive dark UI | Summary chips replace date badges |

---

## Prerequisites

| Tool | Minimum version | Install |
|------|----------------|---------|
| **Git** | any | [git-scm.com](https://git-scm.com) |
| **Docker Desktop** | 24+ | [docker.com](https://www.docker.com/products/docker-desktop/) |
| **Node.js LTS** | 20+ | [nodejs.org](https://nodejs.org) |
| **Python** | 3.11+ | [python.org](https://www.python.org) |

> **GitHub Student Pack tip**: You get free GitHub Copilot (autocomplete in VS Code), Vercel Pro, and credits on several cloud providers – use them!

---

## Quick Start (Docker Compose – recommended)

```bash
# 1. Clone
git clone https://github.com/0324080078-cyber/DivineBa-Ai.git
cd DivineBa-Ai

# 2. Configure environment
cp .env.example .env
# Open .env and set OPENAI_API_KEY=sk-...

# 3. Start everything
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend (Cyrus AI) | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Qdrant Dashboard | http://localhost:6333/dashboard |

---

## Manual / Development Setup

### Backend

```bash
cd backend

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run Qdrant in Docker (separate terminal)
docker run -p 6333:6333 qdrant/qdrant:v1.9.5

# Start the API
OPENAI_API_KEY=sk-... uvicorn app.main:app --reload
```

Visit http://localhost:8000/docs for the interactive Swagger UI.

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # or just set NEXT_PUBLIC_API_BASE=http://localhost:8000
npm run dev
```

---

## Environment Variables

Copy `.env.example` → `.env` and fill in:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | *(required)* | Your OpenAI API key |
| `CYRUS_PROVIDER` | `openai` | LLM provider (`openai` \| `grok` \| `deepseek`) |
| `CYRUS_CHAT_MODEL` | `gpt-4o-mini` | Chat model name |
| `CYRUS_EMBED_MODEL` | `text-embedding-3-small` | Embedding model name |
| `QDRANT_URL` | `http://qdrant:6333` | Qdrant connection URL |
| `CYRUS_COLLECTION` | `cyrus_messages` | Qdrant collection name |
| `STT_PROVIDER` | `openai` | STT backend (`openai` \| `local`) |
| `TTS_PROVIDER` | `openai` | TTS backend (`openai` \| `local`) |
| `NEXT_PUBLIC_API_BASE` | `http://localhost:8000` | Frontend → backend URL |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/sessions` | Create a new session |
| `GET` | `/api/sessions/{id}/tiles` | History tiles with summary chips |
| `POST` | `/api/chat` | Send a message, get a reply |
| `POST` | `/api/stt` | Audio file → text (Whisper) |
| `POST` | `/api/tts` | Text → speech audio |

Full docs at http://localhost:8000/docs when the backend is running.

---

## Features

### ✅ Chat with memory
Every message is embedded and stored in Qdrant. Relevant past messages are retrieved as context for each new reply.

### ✅ History tiles with summary chips
The sidebar shows conversation tiles. Each tile has a one-line AI-generated chip (≤ 7 words) *instead* of a date – so you instantly know what the conversation was about.

### ✅ WhatsApp-style voice input
Press-and-hold the microphone button to record audio. Release to transcribe via Whisper (OpenAI API or local `faster-whisper`). The transcript fills the text box – you can edit it before sending.

### ✅ Multilingual
Locale is detected from the browser and passed to the backend. Both the system prompt and the summary chip generation preserve the user's language.

### ✅ Provider plug-in architecture
Adding a new provider (Grok, Deepseek, etc.):
1. Create `backend/app/services/providers/<name>_provider.py` and subclass `LLMProvider`
2. Add an `elif` branch in `backend/app/services/provider_factory.py`
3. Set `CYRUS_PROVIDER=<name>` in `.env`

### 🔒 Website clone feature (stub)
> Cloning websites without permission violates their Terms of Service and may be illegal.  
> Cyrus AI does **not** implement automatic website cloning.  
> **Planned "Design Inspiration" feature**: Users will be able to paste a URL and receive an *original* UI design inspired by that site's color scheme and layout – built with their own content and full legal compliance. This feature will be part of the paid upgrade tier.

---

## Hosting (Student-friendly)

### Frontend → Vercel (free)
1. Push your repo to GitHub
2. Go to [vercel.com](https://vercel.com), import the repo
3. Set root directory to `frontend`
4. Add env var: `NEXT_PUBLIC_API_BASE=https://your-backend-url`

### Backend → Render (free tier)
1. Go to [render.com](https://render.com), create a new **Web Service**
2. Connect your GitHub repo, set root to `backend`
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add all env vars from `.env.example`

### Qdrant → Qdrant Cloud (free tier)
1. Go to [cloud.qdrant.io](https://cloud.qdrant.io)
2. Create a free cluster
3. Set `QDRANT_URL=https://your-cluster.qdrant.io:6333` and `QDRANT_API_KEY=...` in your backend env vars

### Alternative backends
- **Fly.io**: `fly launch` inside `backend/` – great free tier
- **Railway**: connect GitHub repo, auto-detects Dockerfile

---

## Local STT/TTS (No API key needed)

### STT – faster-whisper
```bash
pip install faster-whisper
# Set in .env:
STT_PROVIDER=local
```

### TTS – Piper
```bash
pip install piper-tts
# Download a voice model from https://huggingface.co/rhasspy/piper-voices
# Set in .env:
TTS_PROVIDER=local
PIPER_MODEL=/path/to/model.onnx
```

---

## Project Structure

```
DivineBa-Ai/
├── docker-compose.yml          # One-command local stack
├── .env.example                # Environment variable template
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py             # FastAPI app entry point
│       ├── core/config.py      # Settings (pydantic-settings)
│       ├── models/schemas.py   # Pydantic request/response models
│       ├── db/qdrant.py        # Qdrant client helpers
│       ├── services/
│       │   ├── provider_factory.py   # Provider plug-in factory
│       │   ├── providers/
│       │   │   ├── base.py           # Abstract LLMProvider
│       │   │   └── openai_provider.py
│       │   ├── memory.py       # Embed + upsert + search
│       │   └── summarizer.py   # Summary chip generation
│       └── api/routes/
│           ├── health.py
│           ├── sessions.py     # POST /sessions, POST /chat, GET tiles
│           ├── stt.py          # POST /stt
│           └── tts.py          # POST /tts
└── frontend/
    ├── Dockerfile
    ├── next.config.ts
    └── app/
        ├── layout.tsx
        ├── globals.css
        └── page.tsx            # Main chat UI
```

---

## License

MIT – see [LICENSE](LICENSE) for details.

---

*Made with ❤️ by a student developer. If this helped you, give it a ⭐!*
