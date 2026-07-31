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
ollama pull qwen2.5:1.5b    # optional; used for LLM paraphrase mode
ollama pull qwen2.5:3b      # better paraphrase quality when you have the RAM/CPU budget
```

## Run
```bash
OLLAMA_HOST=http://localhost:11434 .venv/bin/streamlit run streamlit_app.py
```
In the sidebar pick **ਪੰਜਾਬੀ (Punjabi)**, keep **Grounded quote (recommended)** for fast faithful answers,
initialize, then ask e.g. `ਸਿੱਖ ਧਰਮ ਕਿਸ ਨੇ ਸਥਾਪਿਤ ਕੀਤਾ?`

**Answer styles**
- **Grounded quote (recommended):** returns the best retrieved Gurmukhi passage (~1s). Best for faithfulness on CPU.
- **LLM paraphrase:** asks the local model to rewrite; falls back to a quote if output is empty/looping/weakly grounded. Small models struggle with Gurmukhi generation — prefer `qwen2.5:3b+` if you use this mode.

## Book requirements
- Prefer **text-extractable** Unicode Gurmukhi PDFs or `.txt` / `.md` files.
- Scanned/image-only PDFs extract as empty text — the app warns when Gurmukhi ratio is near zero. OCR is not bundled yet.

## Regenerate sample booklet
```bash
# needs reportlab + fonts/NotoSansGurmukhi-Regular.ttf
.venv/bin/pip install reportlab
.venv/bin/python scripts/create_punjabi_sample_book.py
```
