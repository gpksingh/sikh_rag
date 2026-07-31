# Sikh & Punjabi RAG App

Ask grounded questions over Sikh / Punjabi books with LangChain, Ollama, FAISS, and Streamlit.

## Modes
- **English** — default English Sikh PDFs in the repo root
- **ਪੰਜਾਬੀ (Punjabi)** — Gurmukhi books, multilingual embeddings (`bge-m3`), answers in Punjabi

See [docs/punjabi_rag.md](docs/punjabi_rag.md) for Punjabi setup details.

## Quick start
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
ollama serve   # separate terminal
ollama pull bge-m3 && ollama pull qwen2.5:3b
OLLAMA_HOST=http://localhost:11434 .venv/bin/streamlit run streamlit_app.py
```

## Tech stack
- Python, Streamlit, LangChain, Ollama, FAISS, PyPDF
