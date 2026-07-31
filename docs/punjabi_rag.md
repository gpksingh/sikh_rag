# Punjabi RAG notes

## What this is
The Streamlit app (`streamlit_app.py`) is a Punjabi RAG that:
1. Indexes Punjabi books (Unicode Gurmukhi PDF/TXT, or scanned PDFs via OCR)
2. Retrieves with a multilingual embedding model (`bge-m3` when available)
3. Answers in either **Gurmukhi** or **Punjabi English (Roman)**

Shared helpers live in `rag.py`. Sample booklet:
- `punjabi_books/sikh_dharam_jaan_pehchaan_punjabi.pdf`
- `punjabi_books/sikh_dharam_jaan_pehchaan_punjabi.txt`

## Answer script (only two options)
- **ਪੰਜਾਬੀ (Gurmukhi):** answers in Gurmukhi script
- **Punjabi English (Roman):** ask in **English** (or Punjabi); answers in Roman Punjabi
  (same Punjabi words in English letters, e.g. `guru nanak`) — not an English translation

There is no separate English-language answer mode. English questions are translated to
Gurmukhi for retrieval against Punjabi books, then the Gurmukhi answer is shown as Roman
when Punjabi English is selected.

## Recommended models (Ollama)
```bash
ollama pull bge-m3          # best multilingual embeddings for Punjabi (optional but preferred)
ollama pull nomic-embed-text  # fallback if bge-m3 is not on the host (e.g. Railway default)
ollama pull qwen2.5:1.5b    # optional; used for LLM paraphrase mode
ollama pull qwen2.5:3b      # better paraphrase quality when you have the RAM/CPU budget
```

If the Ollama host does **not** have `bge-m3`, the app automatically falls back to an installed
embedding model (usually `nomic-embed-text`) and shows a sidebar warning.

## Run
```bash
OLLAMA_HOST=http://localhost:11434 .venv/bin/streamlit run streamlit_app.py
```
Pick **ਪੰਜਾਬੀ (Gurmukhi)** or **Punjabi English (Roman)**, keep **Grounded quote**, initialize.
- Gurmukhi mode: ask e.g. `ਸਿੱਖ ਧਰਮ ਕਿਸ ਨੇ ਸਥਾਪਿਤ ਕੀਤਾ?` (English also works)
- Punjabi English mode: ask e.g. `Who founded Sikhism?` → answer like `sandarabh anusara: ... guru nanak ...`

**Answer styles**
- **Grounded quote (recommended):** returns the best retrieved Gurmukhi passage (~1s).
- **LLM paraphrase:** asks the local model to rewrite; falls back to a quote if weak.

**Upload a Punjabi PDF**
- Choose **Upload Punjabi PDF**, then pick a PDF/TXT.
- Click **Initialize RAG Pipeline** after uploading.

**OCR for scanned Gurmukhi books**
- Enable **OCR scanned Punjabi PDFs (Gurmukhi)** (on by default).
- Uses **Tesseract** with `pan` (Punjabi) / Gurmukhi when the PDF has no text layer.
- Streamlit Cloud: `packages.txt` must list `tesseract-ocr`, `tesseract-ocr-pan`, `poppler-utils`.
- Use **Max OCR pages** for large books.

## Book requirements
- Prefer Unicode Gurmukhi PDFs or `.txt` / `.md` files.
- Scanned/image-only PDFs are handled by OCR when enabled.

## Regenerate sample booklet
```bash
# needs reportlab + fonts/NotoSansGurmukhi-Regular.ttf
.venv/bin/pip install reportlab
.venv/bin/python scripts/create_punjabi_sample_book.py
```
