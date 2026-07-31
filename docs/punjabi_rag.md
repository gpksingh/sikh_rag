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
In the sidebar pick **ਪੰਜਾਬੀ (Punjabi)**, keep **Grounded quote (recommended)** for fast faithful answers,
initialize, then ask e.g. `ਸਿੱਖ ਧਰਮ ਕਿਸ ਨੇ ਸਥਾਪਿਤ ਕੀਤਾ?`

**Answer styles**
- **Grounded quote (recommended):** returns the best retrieved Gurmukhi passage (~1s). Best for faithfulness on CPU.
- **LLM paraphrase:** asks the local model to rewrite; falls back to a quote if output is empty/looping/weakly grounded. Small models struggle with Gurmukhi generation — prefer `qwen2.5:3b+` if you use this mode.

**Punjabi English (Roman) — optional**
- Enable **Show Punjabi English (Roman)** in the Punjabi sidebar.
- This is **Punjabi written with English letters** (e.g. `guru nanak`), **not** an English translation.
- Display modes: **Gurmukhi + Punjabi English**, **Punjabi English only**, or **Gurmukhi only**.
- Styles: **Simple (ASCII)** (default) or **Scholarly (IAST)** with diacritics.
- Uses the `indic-transliteration` package (Gurmukhi → Roman).

**Upload a Punjabi PDF**
- In ਪੰਜਾਬੀ mode, choose **Upload Punjabi PDF**, then pick a PDF/TXT.
- Click **Initialize RAG Pipeline** after uploading.

**OCR for scanned Gurmukhi books**
- Enable **OCR scanned Punjabi PDFs (Gurmukhi)** (on by default in Punjabi mode).
- If the PDF has no selectable text, the app runs **Tesseract** with `pan` (Punjabi) / Gurmukhi.
- Streamlit Cloud needs `packages.txt` entries: `tesseract-ocr`, `tesseract-ocr-pan`, `poppler-utils`.
- OCR is slower and memory-heavy — use **Max OCR pages** for large books.
- Tip: text-layer Unicode PDFs skip OCR automatically (unless you check **Always OCR**).

## Book requirements
- Prefer **text-extractable** Unicode Gurmukhi PDFs or `.txt` / `.md` files.
- Scanned/image-only PDFs extract as empty text — the app warns when Gurmukhi ratio is near zero. OCR is not bundled yet.

## Regenerate sample booklet
```bash
# needs reportlab + fonts/NotoSansGurmukhi-Regular.ttf
.venv/bin/pip install reportlab
.venv/bin/python scripts/create_punjabi_sample_book.py
```
