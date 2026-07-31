# Sikh & Punjabi RAG App

Ask grounded questions over Sikh / Punjabi books with LangChain, Ollama, FAISS, and Streamlit.

## Modes
- **ਪੰਜਾਬੀ (Gurmukhi)** — answers in Gurmukhi script
- **Punjabi English (Roman)** — same Punjabi answers written with English letters (not a translation)

Both modes use Punjabi books, multilingual embeddings (`bge-m3` when available), and optional OCR for scanned PDFs.

See [docs/punjabi_rag.md](docs/punjabi_rag.md) for setup details.

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
