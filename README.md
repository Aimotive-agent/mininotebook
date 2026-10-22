# MiniNotebook

**Your own private, self-hosted NotebookLM-style app** — grounded AI chat with citations, OCR for scanned documents, and a "Studio" that generates audio overviews, slide decks, videos, mind maps, and more.

Upload your own documents, ask questions that are answered **only from your sources** (with clickable citations), save notes, and generate artifacts — all running locally on your machine with your own API keys. Nothing leaves your server.

---

## ✨ Features

| Area | What it does |
|---|---|
| **Sources** | Upload PDF, DOCX, PPTX, EPUB, RTF, MD, TXT, CSV, JSON, HTML — or paste a URL / YouTube link / plain text |
| **OCR** | Scanned/image PDFs and image files (PNG/JPG/…) are automatically OCR'd using a vision model |
| **Grounded chat** | Answers only from your sources, with inline `[n]` citations that jump to the exact quote |
| **Notes** | Save answers and write your own notes; the AI uses your saved notes as context |
| **Studio** | Generate **Audio Overview**, **Slide Deck**, **Video Overview** (MP4 slideshow), **Mind Map**, **Report**, **Flashcards**, **Quiz**, **Infographic**, **Data Table**, **Summary**, **Study Guide** |
| **Persistence** | Notebooks, sources, notes, chat history and artifacts are all saved to disk |

---

## 🧱 Architecture

- **Backend** — Python FastAPI
- **Vector store** — ChromaDB (local, persistent)
- **Embeddings** — [Ollama](https://ollama.com) (`embeddinggemma` or any embedding model)
- **LLM / vision OCR** — any OpenAI-compatible endpoint (DeepSeek shown by default)
- **Audio** — `edge-tts` (free neural voices) + `ffmpeg`
- **Video** — `ffmpeg` slideshow with narration
- **Frontend** — single-file vanilla HTML/CSS/JS (no build step)

---

## 🚀 Quick start (Docker)

```bash
git clone https://github.com/<your-user>/mininotebook.git
cd mininotebook

# 1. Create your config
cp .env.example .env
#    edit .env and add your LLM API key

# 2. Install Ollama (for embeddings) and pull a model
ollama pull embeddinggemma

# 3. Build & run
docker compose up -d --build

# 4. Open the app
open http://localhost:8095
```

> **Embeddings note:** the container reaches Ollama at `OLLAMA_URL`. The compose file uses `host.docker.internal`, which maps to the Docker host — so Ollama running on your machine is reachable directly.

---

## 🔑 Configuration (`.env`)

| Variable | Default | Purpose |
|---|---|---|
| `LLM_BASE` | `https://api.deepseek.com/v1` | Any OpenAI-compatible base URL (DeepSeek, OpenAI, OpenRouter, a local vLLM/Ollama, …) |
| `LLM_KEY` | — | Your API key |
| `LLM_MODEL` | `deepseek-flash` | Model used for chat, summaries, guides, studio |
| `OCR_MODEL` | `deepseek-flash` | Vision model used to OCR scanned PDFs/images |
| `OLLAMA_URL` | `http://host.docker.internal:11434` | Ollama endpoint for embeddings |
| `EMBED_MODEL` | `embeddinggemma:latest` | Embedding model (must be pulled in Ollama) |
| `DATA_DIR` | `/data` | Where all data is persisted |

### Using your own keys

Set `LLM_BASE`, `LLM_KEY`, and `LLM_MODEL` to any provider. Examples:

```ini
# DeepSeek (default — also does OCR)
LLM_BASE=https://api.deepseek.com/v1
LLM_KEY=sk-...
LLM_MODEL=deepseek-flash

# OpenAI
LLM_BASE=https://api.openai.com/v1
LLM_KEY=sk-...
LLM_MODEL=gpt-4o-mini

# OpenRouter
LLM_BASE=https://openrouter.ai/api/v1
LLM_KEY=sk-or-...
LLM_MODEL=openrouter/auto

# Local (no API key needed)
LLM_BASE=http://host.docker.internal:11434/v1
LLM_KEY=ollama
LLM_MODEL=qwen3.5:4b
```

If your LLM isn't vision-capable, point `OCR_MODEL` at a separate vision model so scanned PDFs still work.

---

## 🧪 Run without Docker

```bash
cd app
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# needs: ffmpeg installed on the system (for audio/video)

export LLM_BASE=https://api.deepseek.com/v1
export LLM_KEY=sk-...
export OLLAMA_URL=http://localhost:11434
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 🗂 How it works

1. **Add sources** → files are parsed (and OCR'd if needed), chunked, embedded, and stored in Chroma.
2. **Chat** → your question is embedded, the top chunks are retrieved, and the LLM answers **only** from them, citing `[1] [3]`.
3. **Studio** → each button builds a saved artifact you can open, save to a note, or delete. Audio/video are rendered with `edge-tts` + `ffmpeg`.

---

## 📄 License

[MIT](LICENSE)

---

## Part of the Veritas Global AI platform

Veritas Global AI builds private, sovereign and self-hosted AI for regulated
enterprises — inference, retrieval and agents that run inside your own
perimeter, with an audit trail you can hand to a regulator.

- [Private AI deployment](https://veritasglobalai.com/private-ai-deployment) — run the model inside your own infrastructure
- [Sovereign AI](https://veritasglobalai.com/sovereign-ai) — jurisdiction, control, operability and evidence
- [AI governance & compliance](https://veritasglobalai.com/ai-governance) — controls that produce evidence
- [AI readiness assessment](https://veritasglobalai.com/assessment) — a confidential evaluation of where you stand

<https://veritasglobalai.com>
