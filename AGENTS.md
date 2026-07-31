# AGENTS.md

## Cursor Cloud specific instructions

This repo is a single Python product: a **Streamlit RAG app** (`streamlit_app.py`) that answers
questions about Sikhism / Punjabi books from PDF/TXT texts, using **Ollama** for embeddings + LLM
generation and local **FAISS** vector stores. Shared helpers are in `rag.py`. `app.py` is a legacy
CLI variant with a hardcoded macOS PDF path — use `streamlit_app.py` as the entrypoint.

### Language modes
- **English** (default books under repo root): uses `faiss_index_/` + `nomic-embed-text` by default.
- **ਪੰਜਾਬੀ (Punjabi)**: sidebar language toggle; indexes Gurmukhi books into `faiss_index_punjabi_/`,
  defaults to multilingual embeddings **`bge-m3`**, prefers **`qwen2.5:1.5b`** in the model list, and uses
  Gurmukhi prompts. Default answer style is **Grounded quote** (returns the top retrieved passage —
  fast and faithful on CPU). **LLM paraphrase** is optional and falls back to a quote when generation
  is weak. Optional **Show English transliteration** renders Roman/ASCII (or IAST) under answers and
  sources. Sample booklet: `punjabi_books/sikh_dharam_jaan_pehchaan_punjabi.pdf`. See `docs/punjabi_rag.md`.

### Environment (already provisioned in the VM snapshot)
- Python deps are installed into a virtualenv at `.venv/` (the startup update script keeps it in sync
  with `requirements.txt`). Run tools via `.venv/bin/...` (e.g. `.venv/bin/streamlit`, `.venv/bin/python`).
- **Ollama is installed locally**. Useful models: `nomic-embed-text`, `bge-m3`, `gemma3:1b`,
  `qwen2.5:1.5b`, `qwen2.5:3b`. Pull more with `ollama pull <model>` if needed.

### Running the app
1. Start the Ollama server (it is NOT started automatically): `ollama serve` (listens on
   `127.0.0.1:11434`). Leave it running.
2. Start Streamlit **with the local Ollama host exported**:
   `OLLAMA_HOST=http://localhost:11434 .venv/bin/streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true`
3. Open `http://localhost:8501`, pick language, click **Initialize RAG Pipeline**, then ask a question.

### Non-obvious gotchas
- **You MUST set `OLLAMA_HOST=http://localhost:11434`.** Otherwise the app defaults to a remote
  Railway Ollama URL (`https://ollama-production-1333.up.railway.app`) hardcoded in `streamlit_app.py`.
  There is no `.streamlit/secrets.toml` (gitignored); the code falls back to the `OLLAMA_HOST` env var.
- Switching English ↔ Punjabi clears the in-memory pipeline; each language has its own FAISS directory.
- Punjabi needs **extractable Unicode Gurmukhi** text. Scanned PDFs (e.g. `Sikh_Religion_Vol_1.pdf`)
  extract empty text — the app warns when the Gurmukhi ratio is near zero. OCR is not included.
- With matching English defaults (default book, chunk 1000/30, `nomic-embed-text`), the committed
  `faiss_index_/` fingerprint loads without re-embedding. Punjabi first init embeds with `bge-m3`
  into `faiss_index_punjabi_/` (gitignored).
- CPU-only: `qwen2.5:3b` Punjabi answers often take ~20–60s; `gemma3:1b` is faster but weaker at Gurmukhi.
- Lint: `.venv/bin/python -m pyflakes streamlit_app.py` may report a pre-existing unused exception var.
  No formal test suite; `test_railway.sh` / `ollama_railway_test.py` only probe a remote Ollama host.
