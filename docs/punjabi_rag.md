# Punjabi RAG notes

## What this is
The Streamlit app (`streamlit_app.py`) now supports a **ਪੰਜਾਬੀ (Punjabi)** language mode that:
1. Indexes Punjabi books (Unicode Gurmukhi PDF/TXT)
2. Retrieves with a multilingual embedding model (`bge-m3` by default)
3. Answers in Gurmukhi using language-aware prompts

Shared helpers live in `rag.py`. Sample booklet:
- `punjabi_books/sikh_dharam_jaan_pehchaan_punjabi.pdf`
- `punjabi_books/sikh_dharam_jaan_pehchaan_punjabi.txt`

## Recommended models (Ollama)
```bash
ollama pull bge-m3          # multilingual embeddings (required for good Punjabi retrieval)
ollama pull qwen2.5:3b      # better Gurmukhi generation than tiny English-centric models
```

## Run
```bash
OLLAMA_HOST=http://localhost:11434 .venv/bin/streamlit run streamlit_app.py
```
In the sidebar pick **ਪੰਜਾਬੀ (Punjabi)**, initialize, then ask e.g. `ਸਿੱਖ ਧਰਮ ਕਿਸ ਨੇ ਸਥਾਪਿਤ ਕੀਤਾ?`

## Book requirements
- Prefer **text-extractable** Unicode Gurmukhi PDFs or `.txt` / `.md` files.
- Scanned/image-only PDFs extract as empty text — the app warns when Gurmukhi ratio is near zero. OCR is not bundled yet.

## Regenerate sample booklet
```bash
# needs reportlab + fonts/NotoSansGurmukhi-Regular.ttf
.venv/bin/pip install reportlab
.venv/bin/python scripts/create_punjabi_sample_book.py
```
