# AGENTS.md

## Cursor Cloud specific instructions

This repo is a single Python product: a **Streamlit RAG app** (`streamlit_app.py`) that answers
questions about Sikhism from PDF texts, using **Ollama** for embeddings + LLM generation and a
local **FAISS** vector store (committed under `faiss_index_/`). `app.py` is a legacy CLI variant with
a hardcoded macOS PDF path, so it will not run as-is — use `streamlit_app.py` as the entrypoint.

### Environment (already provisioned in the VM snapshot)
- Python deps are installed into a virtualenv at `.venv/` (the startup update script keeps it in sync
  with `requirements.txt`). Run tools via `.venv/bin/...` (e.g. `.venv/bin/streamlit`, `.venv/bin/python`).
- **Ollama is installed locally** and the required models are pre-pulled into the snapshot:
  `nomic-embed-text` (embeddings, 768-dim — matches the committed FAISS index) and `gemma3:1b`
  (a small, CPU-friendly LLM). Pull more with `ollama pull <model>` if needed.

### Running the app
1. Start the Ollama server (it is NOT started automatically): `ollama serve` (listens on
   `127.0.0.1:11434`). Leave it running.
2. Start Streamlit **with the local Ollama host exported**:
   `OLLAMA_HOST=http://localhost:11434 .venv/bin/streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true`
3. Open `http://localhost:8501`, click **Initialize RAG Pipeline**, then ask a question.

### Non-obvious gotchas
- **You MUST set `OLLAMA_HOST=http://localhost:11434`.** Otherwise the app defaults to a remote
  Railway Ollama URL (`https://ollama-production-1333.up.railway.app`) hardcoded in `streamlit_app.py`.
  There is no `.streamlit/secrets.toml` (gitignored); the code falls back to the `OLLAMA_HOST` env var.
- With default sidebar settings (default book, chunk size 1000, overlap 30, `nomic-embed-text`), the
  fingerprint matches the committed `faiss_index_/`, so **Initialize loads the cached index instead of
  re-embedding** the PDF. Changing those settings triggers a full (slow, CPU) re-embed.
- CPU-only inference: `gemma3:1b` answers a query in ~15–25s. Larger models will be much slower.
- Lint: `.venv/bin/python -m pyflakes streamlit_app.py` reports 2 pre-existing, harmless warnings
  (an unused `urljoin` import and an unused exception var). There is no configured test suite;
  `test_railway.sh` / `ollama_railway_test.py` only probe a remote Ollama host.
