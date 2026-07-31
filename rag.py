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

PUNJABI_DEFAULT_BOOKS = {
    "ਸਿੱਖ ਧਰਮ: ਜਾਣ-ਪਛਾਣ (Punjabi sample)": "punjabi_books/sikh_dharam_jaan_pehchaan_punjabi.pdf",
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


def load_uploaded_file(uploaded_file) -> Tuple[List[Document], str]:
    """Save an uploaded Streamlit file to a temp path and load it. Returns (docs, source_name)."""
    suffix = os.path.splitext(uploaded_file.name)[1].lower() or ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name
    try:
        if suffix in {".txt", ".md"}:
            docs = load_text_file(tmp_path)
        else:
            docs = load_pdf(tmp_path)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
    return docs, uploaded_file.name


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
    """
    Transliterate Gurmukhi text to Roman/English letters.

    style:
      - "simple": ASCII-friendly (no diacritics) for general English readers
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
            "indic-transliteration is required for English transliteration. "
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
