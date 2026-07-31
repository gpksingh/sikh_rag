"""Shared helpers for English and Punjabi (Gurmukhi) RAG."""

from __future__ import annotations

import os
import tempfile
from typing import Iterable, List, Tuple

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import CharacterTextSplitter, RecursiveCharacterTextSplitter

# Preferred Ollama models for Punjabi grounded answers (CPU-friendly first).
# Note: on CPU, qwen2.5:1.5b often follows Gurmukhi prompts more reliably than :3b.
PUNJABI_PREFERRED_LLMS = [
    "qwen2.5:1.5b",
    "qwen2.5:3b",
    "qwen2.5:7b",
    "gemma3:4b",
    "llama3.1",
    "gemma3:1b",
]

PUNJABI_EMBEDDING_MODELS = ["bge-m3", "nomic-embed-text"]
ENGLISH_EMBEDDING_MODELS = ["nomic-embed-text", "bge-m3"]

# Substrings that mark embedding-capable Ollama tags (exclude from LLM list).
EMBEDDING_NAME_HINTS = ("embed", "bge-", "e5-", "minilm", "mxbai-embed")


def is_embedding_model_name(name: str) -> bool:
    lower = (name or "").lower()
    return any(h in lower for h in EMBEDDING_NAME_HINTS)


def normalize_model_base(name: str) -> str:
    """Strip :tag so 'bge-m3:latest' matches preferred 'bge-m3'."""
    return (name or "").split(":", 1)[0].strip().lower()


def resolve_embedding_choices(
    preferred: List[str],
    available_names: List[str],
) -> Tuple[List[str], List[str]]:
    """
    Return (choices_for_ui, missing_preferred).

    Prefers models that are actually present on the Ollama host. If none of the
    preferred models are installed, falls back to any detected embedding model,
    then finally to the preferred list (so the UI still shows options).
    """
    available = list(available_names or [])
    by_base = {}
    for n in available:
        by_base.setdefault(normalize_model_base(n), n)

    chosen = []
    missing = []
    for pref in preferred:
        base = normalize_model_base(pref)
        if base in by_base:
            chosen.append(by_base[base])
        elif pref in available:
            chosen.append(pref)
        else:
            missing.append(pref)

    if chosen:
        # Keep any other installed embedding models after preferred ones.
        for n in available:
            if is_embedding_model_name(n) and n not in chosen:
                chosen.append(n)
        return chosen, missing

    installed_embeds = [n for n in available if is_embedding_model_name(n)]
    if installed_embeds:
        return installed_embeds, missing

    return list(preferred), missing

PUNJABI_DEFAULT_BOOKS = {
    "ਸਿੱਖ ਧਰਮ: ਜਾਣ-ਪਛਾਣ (Punjabi sample)": "punjabi_books/sikh_dharam_jaan_pehchaan_punjabi.pdf",
    "Scanned Gurmukhi sample (OCR test)": "punjabi_books/scanned_gurmukhi_sample.pdf",
}

ENGLISH_DEFAULT_BOOKS = {
    "a-brief-introduction-to-sikhism-gurbachan-singh-sidhu.pdf": "a-brief-introduction-to-sikhism-gurbachan-singh-sidhu.pdf",
    "Sikh_Religion_Vol_1.pdf": "Sikh_Religion_Vol_1.pdf",
}


def is_gurmukhi_char(ch: str) -> bool:
    return "\u0A00" <= ch <= "\u0A7F"


def gurmukhi_stats(text: str) -> dict:
    letters = [c for c in text if c.isalpha() or is_gurmukhi_char(c)]
    gurmukhi = sum(1 for c in letters if is_gurmukhi_char(c))
    total = len(letters) or 1
    return {
        "gurmukhi_chars": gurmukhi,
        "letter_chars": len(letters),
        "ratio": gurmukhi / total,
        "has_gurmukhi": gurmukhi > 0,
    }


def documents_gurmukhi_stats(docs: Iterable[Document]) -> dict:
    text = "\n".join(d.page_content or "" for d in docs)
    return gurmukhi_stats(text)


def prefer_models(available: List[str], preferred: List[str]) -> List[str]:
    """Reorder available model names so preferred ones come first when present."""
    names = list(available)
    for pref in reversed(preferred):
        matches = [n for n in names if n == pref or n.startswith(pref + ":") or n.startswith(pref)]
        # Exact / prefix match: move first match to front
        for m in matches:
            if m in names:
                names.remove(m)
                names.insert(0, m)
                break
    return names


def load_pdf(path: str) -> List[Document]:
    return PyPDFLoader(path).load()


def load_text_file(path: str) -> List[Document]:
    return TextLoader(path, encoding="utf-8").load()


def pdf_needs_ocr(
    docs: List[Document],
    *,
    language: str = "punjabi",
    min_chars_per_page: int = 40,
    min_gurmukhi_ratio: float = 0.05,
) -> bool:
    """True when the PDF text layer is empty/weak (typical of scanned books)."""
    if not docs:
        return True
    text = "\n".join((d.page_content or "") for d in docs)
    avg_chars = len(text.strip()) / max(len(docs), 1)
    if avg_chars < min_chars_per_page:
        return True
    if language == "punjabi":
        return gurmukhi_stats(text)["ratio"] < min_gurmukhi_ratio
    return False


def ocr_available() -> Tuple[bool, str]:
    """Return (ok, detail) for Tesseract + Punjabi language data."""
    try:
        import importlib.util
        import pytesseract

        if importlib.util.find_spec("pdf2image") is None:
            return False, "Missing Python package: pdf2image"
    except ImportError as e:
        return False, f"Missing Python package: {e}"
    try:
        langs = set(pytesseract.get_languages(config=""))
    except Exception as e:
        return False, f"Tesseract not available: {e}"
    if "pan" not in langs and "Gurmukhi" not in langs:
        return False, "Tesseract is installed but Punjabi/Gurmukhi data is missing (need tesseract-ocr-pan)."
    return True, "ok"


def resolve_ocr_lang(preferred: str = "pan+eng") -> str:
    """Pick a Tesseract language string based on installed tessdata."""
    try:
        import pytesseract

        langs = set(pytesseract.get_languages(config=""))
    except Exception:
        return preferred
    parts = []
    for code in preferred.split("+"):
        if code in langs:
            parts.append(code)
        elif code == "pan" and "Gurmukhi" in langs:
            parts.append("Gurmukhi")
    if parts:
        return "+".join(parts)
    if "pan" in langs:
        return "pan"
    if "Gurmukhi" in langs:
        return "Gurmukhi"
    if "eng" in langs:
        return "eng"
    return preferred


def ocr_pdf_to_documents(
    path: str,
    *,
    lang: str = "pan+eng",
    dpi: int = 200,
    max_pages: int | None = 60,
    progress_callback=None,
) -> List[Document]:
    """
    OCR a (scanned) PDF into LangChain Documents, one per page.
    Uses Tesseract with Punjabi (pan) / Gurmukhi language data when available.
    """
    from pdf2image import convert_from_path
    import pytesseract

    ok, detail = ocr_available()
    if not ok:
        raise RuntimeError(
            f"OCR is not available ({detail}). "
            "Install system packages: tesseract-ocr tesseract-ocr-pan poppler-utils "
            "and Python packages: pytesseract pdf2image"
        )

    ocr_lang = resolve_ocr_lang(lang)
    # First pass: get page count without loading all images into RAM
    try:
        from pypdf import PdfReader

        total_pages = len(PdfReader(path).pages)
    except Exception:
        total_pages = None

    if max_pages is not None and total_pages is not None:
        last_page = min(total_pages, max_pages)
    elif max_pages is not None:
        last_page = max_pages
    else:
        last_page = total_pages

    docs: List[Document] = []
    # Convert in small batches to limit memory on Streamlit Cloud
    batch_size = 2
    start = 1
    end_limit = last_page or 10_000
    while start <= end_limit:
        stop = min(start + batch_size - 1, end_limit)
        try:
            images = convert_from_path(
                path,
                dpi=dpi,
                first_page=start,
                last_page=stop,
                fmt="png",
                thread_count=1,
            )
        except Exception as e:
            if start == 1:
                raise RuntimeError(f"Failed to render PDF pages for OCR: {e}") from e
            break
        if not images:
            break
        for offset, image in enumerate(images):
            page_no = start + offset
            text = pytesseract.image_to_string(image, lang=ocr_lang) or ""
            docs.append(
                Document(
                    page_content=text.strip(),
                    metadata={
                        "source": path,
                        "page": page_no - 1,
                        "ocr": True,
                        "ocr_lang": ocr_lang,
                    },
                )
            )
            if progress_callback:
                total_for_progress = last_page or page_no
                progress_callback(page_no, total_for_progress, text)
        start = stop + 1
        if total_pages is None and len(images) < batch_size:
            break
        if max_pages is not None and len(docs) >= max_pages:
            break
    return docs


def load_pdf_with_optional_ocr(
    path: str,
    *,
    language: str = "punjabi",
    use_ocr: bool = True,
    force_ocr: bool = False,
    ocr_lang: str = "pan+eng",
    ocr_dpi: int = 200,
    max_ocr_pages: int | None = 60,
    progress_callback=None,
) -> Tuple[List[Document], dict]:
    """
    Load a PDF; if text extraction yields little/no Gurmukhi (or force_ocr), run OCR.
    Returns (documents, info) where info describes whether OCR ran.
    """
    info = {
        "ocr_used": False,
        "ocr_forced": force_ocr,
        "ocr_lang": None,
        "text_layer_pages": 0,
        "final_pages": 0,
        "reason": "text_layer",
    }
    docs = load_pdf(path)
    info["text_layer_pages"] = len(docs)
    needs = force_ocr or (use_ocr and pdf_needs_ocr(docs, language=language))
    if not needs:
        info["final_pages"] = len(docs)
        return docs, info

    if not use_ocr and not force_ocr:
        info["final_pages"] = len(docs)
        info["reason"] = "ocr_disabled"
        return docs, info

    ocr_docs = ocr_pdf_to_documents(
        path,
        lang=ocr_lang,
        dpi=ocr_dpi,
        max_pages=max_ocr_pages,
        progress_callback=progress_callback,
    )
    info.update(
        {
            "ocr_used": True,
            "ocr_lang": resolve_ocr_lang(ocr_lang),
            "final_pages": len(ocr_docs),
            "reason": "forced" if force_ocr else "weak_text_layer",
        }
    )
    return ocr_docs, info


def load_uploaded_file(
    uploaded_file,
    *,
    language: str = "english",
    use_ocr: bool = False,
    force_ocr: bool = False,
    ocr_lang: str = "pan+eng",
    ocr_dpi: int = 200,
    max_ocr_pages: int | None = 60,
    progress_callback=None,
) -> Tuple[List[Document], str, dict]:
    """Save an uploaded Streamlit file, load it (with optional OCR). Returns (docs, source_name, info)."""
    suffix = os.path.splitext(uploaded_file.name)[1].lower() or ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name
    info = {"ocr_used": False, "reason": "text_file"}
    try:
        if suffix in {".txt", ".md"}:
            docs = load_text_file(tmp_path)
        else:
            docs, info = load_pdf_with_optional_ocr(
                tmp_path,
                language=language,
                use_ocr=use_ocr,
                force_ocr=force_ocr,
                ocr_lang=ocr_lang,
                ocr_dpi=ocr_dpi,
                max_ocr_pages=max_ocr_pages,
                progress_callback=progress_callback,
            )
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
    return docs, uploaded_file.name, info


def split_documents(
    documents: List[Document],
    *,
    chunk_size: int,
    chunk_overlap: int,
    language: str,
) -> List[Document]:
    if language == "punjabi":
        # Recursive splitter handles Gurmukhi better than a single newline separator.
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", "।", " ", ""],
        )
    else:
        splitter = CharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separator="\n",
        )
    return splitter.split_documents(documents=documents)


def is_low_quality_gurmukhi_answer(text: str) -> bool:
    """Detect empty, non-Gurmukhi, or heavily repetitive model output."""
    if not text or not text.strip():
        return True
    stats = gurmukhi_stats(text)
    if stats["ratio"] < 0.35:
        return True
    # Collapse whitespace and look for repeated 12+ char phrases (looping models).
    compact = " ".join(text.split())
    if len(compact) > 80:
        window = 18
        seen = {}
        for i in range(0, max(1, len(compact) - window)):
            frag = compact[i : i + window]
            seen[frag] = seen.get(frag, 0) + 1
            if seen[frag] >= 4:
                return True
    return False


def extractive_punjabi_answer(docs: list, query: str) -> str:
    """Grounded fallback: quote the top retrieved passage (FAISS already ranked it)."""
    if not docs:
        return "ਇਸ ਸੰਦਰਭ ਵਿੱਚ ਜਾਣਕਾਰੀ ਉਪਲਬਧ ਨਹੀਂ।"
    passage = (docs[0].page_content or "").strip()
    sentences = [s.strip() for s in passage.replace("?", "।").split("।") if s.strip()]
    if not sentences:
        snippet = passage
    else:
        snippet = "। ".join(sentences[:2]) + "।"
    if len(snippet) > 420:
        snippet = snippet[:420].rstrip() + "…"
    return f"ਸੰਦਰਭ ਅਨੁਸਾਰ: {snippet}"


def answer_prompt(language: str, context: str, query: str) -> str:
    if language == "punjabi":
        return f"""ਤੁਸੀਂ ਇੱਕ RAG ਸਹਾਇਕ ਹੋ। ਸਿਰਫ਼ ਸੰਦਰਭ ਵਿੱਚੋਂ ਹੀ ਜਵਾਬ ਦਿਓ।
ਨਾਂ ਅਤੇ ਤਾਰੀਖਾਂ ਸੰਦਰਭ ਵਾਂਗ ਹੀ ਲਿਖੋ। 1-2 ਛੋਟੇ ਵਾਕ ਲਿਖੋ।
ਪੂਰਾ ਜਵਾਬ ਗੁਰਮੁਖੀ ਪੰਜਾਬੀ ਵਿੱਚ ਹੋਵੇ।

ਸੰਦਰਭ:
{context}

ਸਵਾਲ: {query}

ਜਵਾਬ:"""
    return f"""Based on the following context about Sikhism, answer the question accurately.
If the answer is not in the context, say you do not have enough information.

Context:
{context}

Question: {query}

Answer:"""


def relevance_prompt(language: str, query: str, chunk: str) -> str:
    snippet = chunk[:800]
    if language == "punjabi":
        return f"""ਤੁਸੀਂ ਇੱਕ relevance ਫਿਲਟਰ ਹੋ। ਸਿਰਫ਼ 'yes' ਜਾਂ 'no' ਲਿਖੋ।

ਕੀ ਹੇਠਾਂ ਦਿੱਤਾ ਪੈਸੇਜ ਇਸ ਸਵਾਲ ਦਾ ਜਵਾਬ ਦੇਣ ਲਈ ਢੁਕਵਾਂ ਹੈ?

ਸਵਾਲ: {query}

ਪੈਸੇਜ:
{snippet}

ਜਵਾਬ (yes/no):"""
    return f"""You are a relevance filter. Answer ONLY with 'yes' or 'no'.

Is the following passage relevant to answering this question?

Question: {query}

Passage:
{snippet}

Answer (yes/no):"""


def reformulate_prompt(language: str, original_query: str, retrieved_chunks: list) -> str:
    context_sample = "\n---\n".join([c.page_content[:300] for c in retrieved_chunks[:3]])
    if language == "punjabi":
        return f"""ਹੇਠਾਂ ਦਿੱਤਾ ਸਵਾਲ ਪੁੱਛਿਆ ਗਿਆ ਸੀ ਪਰ ਮਿਲੇ ਪੈਸੇਜ ਕਾਫ਼ੀ ਢੁਕਵੇਂ ਨਹੀਂ ਸਨ।

ਅਸਲ ਸਵਾਲ: {original_query}

ਮਿਲੇ ਪੈਸੇਜਾਂ ਦਾ ਨਮੂਨਾ:
{context_sample}

ਸਵਾਲ ਨੂੰ ਪੰਜਾਬੀ ਧਾਰਮਿਕ ਪਾਠ ਤੋਂ ਵਧੀਆ ਜਾਣਕਾਰੀ ਲੱਭਣ ਲਈ ਮੁੜ ਲਿਖੋ।
ਸਿਰਫ਼ ਨਵਾਂ ਸਵਾਲ ਵਾਪਸ ਕਰੋ, ਹੋਰ ਕੁਝ ਨਹੀਂ।"""
    return f"""The following question was asked but the retrieved passages were not relevant enough.

Original question: {original_query}

Sample of what was retrieved:
{context_sample}

Please rewrite the question to be more specific and likely to retrieve better passages from a Sikh religious text.
Return ONLY the rewritten question, nothing else."""


def faiss_dir_for(language: str) -> str:
    return "faiss_index_punjabi_" if language == "punjabi" else "faiss_index_"


def gurmukhi_to_english_transliteration(text: str, *, style: str = "simple") -> str:
    """Deprecated alias — use gurmukhi_to_punjabi_english()."""
    return gurmukhi_to_punjabi_english(text, style=style)


def gurmukhi_to_punjabi_english(text: str, *, style: str = "simple") -> str:
    """
    Convert Gurmukhi Punjabi to Punjabi English (Roman Punjabi):
    the same Punjabi words written with English/Latin letters
    (e.g. 'guru nanak'), NOT a translation into English meaning.

    style:
      - "simple": ASCII-friendly (no diacritics) — everyday Punjabi English
      - "iast": scholarly IAST with diacritics (ā, ī, ṃ, …)
    Non-Gurmukhi characters are preserved.
    """
    if not text:
        return ""
    try:
        from indic_transliteration import sanscript
        from indic_transliteration.sanscript import transliterate
    except ImportError as e:
        raise RuntimeError(
            "indic-transliteration is required for Punjabi English. "
            "Install with: pip install indic-transliteration"
        ) from e

    # Transliterate per contiguous Gurmukhi run so Latin/punctuation stays intact.
    out = []
    buf = []

    def flush():
        if not buf:
            return
        chunk = "".join(buf)
        buf.clear()
        roman = transliterate(chunk, sanscript.GURMUKHI, sanscript.IAST)
        # Indic danda often becomes '|'
        roman = roman.replace("|", ".")
        if style != "iast":
            import unicodedata

            roman = unicodedata.normalize("NFD", roman)
            roman = "".join(c for c in roman if unicodedata.category(c) != "Mn")
            # Common nasal mark left as 'M' in some paths → 'n'
            roman = roman.replace("M", "n").replace("m̐", "n")
        out.append(roman)

    for ch in text:
        if is_gurmukhi_char(ch) or ch in ("੍", "ੰ", "ੱ", "ਂ", "ਃ"):
            buf.append(ch)
        else:
            flush()
            out.append(ch)
    flush()
    result = "".join(out)
    result = result.replace("|", ".").replace("।", ".")
    # Tidy whitespace around newlines
    return "\n".join(line.rstrip() for line in result.splitlines())
