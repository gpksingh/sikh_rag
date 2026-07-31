import streamlit as st
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_community.vectorstores import FAISS
import os
import requests
import time

import rag as rag_helpers

# MUST be the first Streamlit command (Cloud fails otherwise).
st.set_page_config(page_title="Sikh & Punjabi RAG", layout="wide")

# Get Ollama configuration from Streamlit secrets (for cloud) or environment
try:
    OLLAMA_HOST = st.secrets.get("OLLAMA_HOST", "https://ollama-production-1333.up.railway.app").strip()
    OLLAMA_API_KEY = st.secrets.get("OLLAMA_API_KEY", "").strip()
except (KeyError, FileNotFoundError, Exception):
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "https://ollama-production-1333.up.railway.app").strip()
    OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "").strip()

# Build auth headers if API key is present
OLLAMA_HEADERS = {"Authorization": f"Bearer {OLLAMA_API_KEY}"} if OLLAMA_API_KEY else {}

# Function to test Ollama connection
def test_ollama_connection(base_url, api_key="", timeout=10):
    """Test if Ollama is responding"""
    try:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        response = requests.get(f"{base_url}/api/tags", headers=headers, timeout=timeout)
        return response.status_code == 200
    except requests.exceptions.Timeout:
        return False
    except requests.exceptions.ConnectionError:
        return False
    except Exception:
        return False

def benchmark_ollama(base_url: str, timeout: int = 15) -> dict:
    """Run a quick embed request and return latency stats."""
    try:
        t0 = time.time()
        resp = requests.post(
            f"{base_url}/api/embeddings",
            json={"model": "nomic-embed-text", "prompt": "Waheguru"},
            timeout=timeout,
        )
        latency = time.time() - t0
        if resp.status_code == 200:
            return {"status": "online", "latency_ms": round(latency * 1000)}
        else:
            return {"status": "error", "latency_ms": None, "code": resp.status_code}
    except requests.exceptions.Timeout:
        return {"status": "timeout", "latency_ms": None}
    except Exception:
        return {"status": "offline", "latency_ms": None}


# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stTitle {
        color: #1f77b4;
    }
    </style>
    """, unsafe_allow_html=True)

# Answer script: Punjabi Gurmukhi vs Punjabi English (Roman). RAG is always Punjabi.
with st.sidebar:
    st.header("🌐 Script / ਲਿਪੀ")
    script_label = st.radio(
        "Answer script",
        ["ਪੰਜਾਬੀ (Gurmukhi)", "Punjabi English (Roman)"],
        index=0,
        help="Both use Punjabi books. "
             "Gurmukhi = ਪੰਜਾਬੀ script answers. "
             "Punjabi English = ask in English (or Punjabi); answers in Roman Punjabi "
             "(same Punjabi words in English letters, not an English translation).",
    )
    # API key status (after set_page_config)
    if OLLAMA_API_KEY:
        masked = OLLAMA_API_KEY[:4] + "..." + OLLAMA_API_KEY[-4:]
        st.caption(f"🔑 API Key loaded: `{masked}`")
    else:
        st.caption("ℹ️ No OLLAMA_API_KEY in secrets (OK if your Ollama host is open).")

answer_script = "roman" if "Roman" in script_label else "gurmukhi"
language = "punjabi"  # indexing / OCR / prompts always Punjabi
show_punjabi_english = answer_script == "roman"
transliteration_display = "Punjabi English only" if answer_script == "roman" else "Gurmukhi only"
transliteration_style = "Simple (ASCII)"

# Title and description
st.title("📚 ਪੰਜਾਬੀ RAG — ਸਿੱਖ / ਪੰਜਾਬੀ ਪੁਸਤਕਾਂ")
if answer_script == "roman":
    st.markdown(
        "Ask in **English** about an uploaded Punjabi book — answers come back in "
        "**Punjabi English** (Roman Punjabi: same Punjabi words in English letters, "
        "e.g. `guru nanak` — not an English translation). "
        "Upload a Punjabi PDF or use the sample booklet."
    )
else:
    st.markdown(
        "ਪੰਜਾਬੀ (ਗੁਰਮੁਖੀ) ਕਿਤਾਬਾਂ ਤੋਂ grounded ਜਵਾਬ ਲਵੋ। "
        "You can also ask in English; answers stay in Gurmukhi. "
        "Upload a Punjabi PDF, or use the sample booklet."
    )

# ── Top metrics banner ────────────────────────────────────────────────────────
st.markdown("### 📈 Last Query Performance")
if st.session_state.get("last_perf"):
    p = st.session_state.last_perf
    t1, t2, t3 = st.columns(3)
    t1.metric(
        "⚡ Time to First Token",
        f"{p['ttft_ms']:,} ms",
        help="Retrieval time + time until the LLM produces its first token. Key user-experience metric."
    )
    t2.metric(
        "⏱️ End-to-End Latency",
        f"{p['e2e_ms']:,} ms",
        help="Total time from query submission to complete response."
    )
    total_tok = p["input_tokens"] + p["output_tokens"]
    t3.metric(
        "🪙 Token Consumption",
        f"{total_tok:,} tokens",
        help=f"Input: {p['input_tokens']:,} tokens · Output: {p['output_tokens']:,} tokens"
    )
    st.caption(
        f"📥 Input: `{p['input_tokens']:,}` &nbsp;·&nbsp; "
        f"📤 Output: `{p['output_tokens']:,}` &nbsp;·&nbsp; "
        f"🔍 Retrieval: `{p.get('retrieve_ms', 0):,} ms` &nbsp;·&nbsp; "
        f"🏷️ Mode: `{st.session_state.get('last_mode', 'Standard RAG')}`"
    )
else:
    t1, t2, t3 = st.columns(3)
    t1.metric("⚡ Time to First Token", "—", help="Run a query to see TTFT")
    t2.metric("⏱️ End-to-End Latency", "—", help="Run a query to see E2E latency")
    t3.metric("🪙 Token Consumption", "—", help="Run a query to see token usage")
    st.caption("ℹ️ Metrics will appear here after your first query.")
st.markdown("---")

# Show Ollama status with detailed diagnostics
ollama_connected = test_ollama_connection(OLLAMA_HOST, OLLAMA_API_KEY, timeout=10)
status_icon = "✅" if ollama_connected else "⚠️"
status_text = "Connected" if ollama_connected else "Offline/Error"

if ollama_connected:
    st.info(f"{status_icon} **Ollama Status:** {status_text}\n\n🔗 **Host:** `{OLLAMA_HOST}`")
else:
    st.warning(f"{status_icon} **Ollama Status:** {status_text}\n\n🔗 **Host:** `{OLLAMA_HOST}`\n\n⚠️ **Ollama Cloud Not Responding:**\n- Check your API key is valid\n- Verify Ollama Cloud service is running\n- Check network connectivity\n- This app requires Ollama Cloud to function")

# Initialize session state
if "retriever" not in st.session_state:
    st.session_state.retriever = None
    st.session_state.vectorstore = None
    st.session_state.llm = None
    st.session_state.initialized = False
    st.session_state.last_perf = None

st.session_state.active_language = language
st.session_state.answer_script = answer_script

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")

    # PDF / text source selection (Punjabi books only)
    source_label = "Use Default Punjabi Book"
    upload_label = "Upload Punjabi PDF"
    pdf_source = st.radio(
        "📄 Select Source",
        [source_label, upload_label],
        index=0,
        help="Upload your own Punjabi (Gurmukhi) PDF or TXT to build a grounded index.",
    )

    if pdf_source == source_label:
        pdf_books = rag_helpers.PUNJABI_DEFAULT_BOOKS
        selected_book = st.selectbox(
            "📖 Select Book",
            list(pdf_books.keys()),
            index=0
        )
        pdf_path = pdf_books[selected_book]
        uploaded_file = None
    else:
        st.info(
            "📤 Upload a **Punjabi PDF** (or TXT/MD) with extractable Gurmukhi text, "
            "or a scanned book (OCR can read Gurmukhi pages)."
        )
        uploaded_file = st.file_uploader(
            "Choose a Punjabi PDF or TXT file",
            type=["pdf", "txt", "md"],
            key="punjabi_book_uploader",
        )
        if uploaded_file is not None:
            st.success(f"✅ File uploaded: {uploaded_file.name}")
        pdf_path = None

    chunk_size = st.slider("Chunk Size", 500, 2000, 800, 100)
    chunk_overlap = st.slider("Chunk Overlap", 0, 500, 80, 10)

    # Dynamically fetch available LLM / embedding models from the connected Ollama host
    @st.cache_data(ttl=60, show_spinner=False)
    def get_ollama_model_names(host):
        try:
            resp = requests.get(f"{host}/api/tags", timeout=5)
            if resp.status_code == 200:
                return [m.get("name", "") for m in resp.json().get("models", []) if m.get("name")]
        except Exception:
            pass
        return []

    @st.cache_data(ttl=60, show_spinner=False)
    def get_available_models(host):
        try:
            resp = requests.get(f"{host}/api/tags", timeout=5)
            if resp.status_code == 200:
                all_models = resp.json().get("models", [])
                llm_models = [
                    m for m in all_models
                    if not rag_helpers.is_embedding_model_name(m.get("name", ""))
                ]
                llm_models.sort(key=lambda m: m.get("size", 0))
                names = [m["name"] for m in llm_models]
                if "gemma4:e2b" in names:
                    names.remove("gemma4:e2b")
                    names.insert(0, "gemma4:e2b")
                return names or ["gemma3:4b"]
        except Exception:
            pass
        return ["gemma3:4b"]

    available_llm_models = rag_helpers.prefer_models(
        get_available_models(OLLAMA_HOST), rag_helpers.PUNJABI_PREFERRED_LLMS
    )
    st.caption("Tip: prefer `qwen2.5:1.5b` or `qwen2.5:3b` for Gurmukhi answers.")
    model_name = st.selectbox(
        "LLM Model",
        available_llm_models,
        index=0
    )
    st.caption(f"🔗 Models from `{OLLAMA_HOST}`")

    preferred_embeds = rag_helpers.PUNJABI_EMBEDDING_MODELS
    host_model_names = get_ollama_model_names(OLLAMA_HOST)
    embed_choices, missing_embeds = rag_helpers.resolve_embedding_choices(
        preferred_embeds, host_model_names
    )
    embedding_model = st.selectbox(
        "Embedding Model",
        embed_choices,
        index=0,
        help="Prefer bge-m3 for Punjabi/Gurmukhi when installed on the Ollama host. "
             "If missing, the app falls back to whatever embedding model is available (often nomic-embed-text).",
    )
    if missing_embeds and "bge-m3" in missing_embeds:
        st.warning(
            "⚠️ `bge-m3` is not installed on this Ollama host, so Punjabi retrieval "
            f"will use `{embedding_model}` instead. For better Gurmukhi retrieval, run "
            "`ollama pull bge-m3` on the Ollama server (e.g. your Railway instance)."
        )
    elif host_model_names and embedding_model.split(":")[0] not in {
        rag_helpers.normalize_model_base(n) for n in host_model_names
    }:
        st.error(
            f"❌ Embedding model `{embedding_model}` is not on `{OLLAMA_HOST}`. "
            f"Pull it there (`ollama pull {embedding_model}`) or pick another model."
        )

    punjabi_answer_style = st.radio(
        "Punjabi answer style",
        ["Grounded quote (recommended)", "LLM paraphrase"],
        index=0,
        help="Grounded quote returns the best retrieved Gurmukhi passage (fast & faithful). "
             "LLM paraphrase needs a stronger model (qwen2.5:3b+) and may fall back to a quote.",
    )

    st.markdown("---")
    st.subheader("🖨️ OCR (scanned books)")
    ocr_ok, ocr_detail = rag_helpers.ocr_available()
    enable_ocr = st.checkbox(
        "OCR scanned Punjabi PDFs (Gurmukhi)",
        value=True,
        help="If the PDF has no selectable text, run Tesseract OCR with Punjabi (pan) to read Gurmukhi pages.",
    )
    force_ocr = st.checkbox(
        "Always OCR (ignore text layer)",
        value=False,
        help="Force OCR even when the PDF already has a text layer.",
    )
    max_ocr_pages = st.slider(
        "Max OCR pages",
        1,
        200,
        40,
        1,
        help="Limit pages for OCR to control time/memory (Streamlit Cloud is limited).",
    )
    ocr_dpi = st.select_slider(
        "OCR DPI",
        options=[150, 200, 250, 300],
        value=200,
        help="Higher DPI is more accurate but slower and uses more memory.",
    )
    if not ocr_ok:
        st.warning(
            f"⚠️ OCR system packages not available here ({ocr_detail}). "
            "On Streamlit Cloud, ensure `packages.txt` includes tesseract-ocr, "
            "tesseract-ocr-pan, and poppler-utils."
        )
    else:
        st.caption(f"OCR ready · Tesseract lang `{rag_helpers.resolve_ocr_lang('pan+eng')}`")

    st.markdown("---")
    st.header("🔬 RAG Mode")
    rag_mode = st.radio(
        "Select RAG strategy:",
        ["Standard RAG", "ReFRAG", "⚖️ Compare Both"],
        index=0,
        help="Standard RAG: retrieve → generate.\nReFRAG: retrieve → LLM filters → reformulate → generate.\nCompare Both: RAG vs ReFRAG context window metrics."
    )

    if rag_mode == "ReFRAG":
        st.info("**ReFRAG** filters out irrelevant chunks using the LLM, then reformulates the query if not enough relevant context is found.")
        refrag_top_k = st.slider("Initial retrieval top-k", 4, 20, 8, 2)
        refrag_relevance_threshold = st.slider("Min relevant chunks before re-query", 1, 6, 2, 1)
    elif rag_mode == "⚖️ Compare Both":
        st.info("Runs **both** pipelines and compares context window size, chunk count, and answer quality.")
        refrag_top_k = st.slider("ReFRAG initial top-k", 4, 20, 8, 2)
        refrag_relevance_threshold = st.slider("ReFRAG min relevant chunks", 1, 6, 2, 1)
    else:
        refrag_top_k = 4
        refrag_relevance_threshold = 2

# Initialize RAG pipeline
if st.button("🚀 Initialize RAG Pipeline", key="init_button"):
    try:
        load_info = {"ocr_used": False}

        def _ocr_progress(page_no, total_pages, _text):
            # Lightweight progress updates during OCR
            frac = min(page_no / max(total_pages, 1), 1.0)
            st.session_state["_ocr_progress"] = (page_no, total_pages, frac)

        # Check if user uploaded a file or using default
        if pdf_source == upload_label and uploaded_file is not None:
            ocr_box = st.empty()
            progress_bar = st.progress(0.0) if (language == "punjabi" and enable_ocr) else None

            def _cb(page_no, total_pages, text):
                if progress_bar is not None:
                    progress_bar.progress(min(page_no / max(total_pages, 1), 1.0))
                ocr_box.caption(f"OCR page {page_no}/{total_pages}…")

            with st.spinner("Loading uploaded file (OCR runs automatically for scanned Punjabi PDFs)..."):
                documents, source_name, load_info = rag_helpers.load_uploaded_file(
                    uploaded_file,
                    language=language,
                    use_ocr=(language == "punjabi" and enable_ocr),
                    force_ocr=(language == "punjabi" and force_ocr),
                    ocr_lang="pan+eng",
                    ocr_dpi=ocr_dpi,
                    max_ocr_pages=max_ocr_pages,
                    progress_callback=_cb if (language == "punjabi" and enable_ocr) else None,
                )
                st.success(f"✓ Loaded {len(documents)} document unit(s) from '{source_name}'")
            if progress_bar is not None:
                progress_bar.empty()
            ocr_box.empty()
            _source = source_name

        elif pdf_source == source_label and pdf_path:
            if not os.path.exists(pdf_path):
                st.error(f"❌ Book not found at `{pdf_path}`")
                st.stop()
            ocr_box = st.empty()
            progress_bar = st.progress(0.0) if (language == "punjabi" and enable_ocr) else None

            def _cb2(page_no, total_pages, text):
                if progress_bar is not None:
                    progress_bar.progress(min(page_no / max(total_pages, 1), 1.0))
                ocr_box.caption(f"OCR page {page_no}/{total_pages}…")

            with st.spinner("Loading book..."):
                if pdf_path.lower().endswith((".txt", ".md")):
                    documents = rag_helpers.load_text_file(pdf_path)
                    load_info = {"ocr_used": False, "reason": "text_file"}
                else:
                    documents, load_info = rag_helpers.load_pdf_with_optional_ocr(
                        pdf_path,
                        language=language,
                        use_ocr=(language == "punjabi" and enable_ocr),
                        force_ocr=(language == "punjabi" and force_ocr),
                        ocr_lang="pan+eng",
                        ocr_dpi=ocr_dpi,
                        max_ocr_pages=max_ocr_pages,
                        progress_callback=_cb2 if (language == "punjabi" and enable_ocr) else None,
                    )
                st.success(f"✓ Loaded {len(documents)} pages/sections")
            if progress_bar is not None:
                progress_bar.empty()
            ocr_box.empty()
            _source = pdf_path

        else:
            st.error("❌ Please select a book source and upload a file or select a book!")
            st.stop()

        if load_info.get("ocr_used"):
            st.success(
                f"🖨️ OCR used ({load_info.get('ocr_lang')}) — "
                f"{load_info.get('final_pages', len(documents))} page(s) recognized "
                f"(reason: {load_info.get('reason')})"
            )

        stats = rag_helpers.documents_gurmukhi_stats(documents)
        if language == "punjabi":
            st.info(
                f"🔤 Gurmukhi detection: **{stats['gurmukhi_chars']:,}** Gurmukhi chars "
                f"({stats['ratio']:.0%} of letters)"
            )
            if stats["ratio"] < 0.05:
                st.warning(
                    "⚠️ Little or no Gurmukhi text after loading. "
                    "Try enabling OCR, raising OCR DPI, or confirm the PDF is Gurmukhi "
                    "(not Shahmukhi / image of poor quality)."
                )
        elif stats["has_gurmukhi"]:
            st.caption(f"Detected some Gurmukhi in the source ({stats['ratio']:.0%} of letters).")

        with st.spinner("Splitting documents..."):
            docs = rag_helpers.split_documents(
                documents,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                language=language,
            )
            st.success(f"✓ Created {len(docs)} chunks")

        with st.spinner("Loading embedding model..."):
            embeddings = OllamaEmbeddings(
                model=embedding_model,
                base_url=OLLAMA_HOST,
            )

        # Build a fingerprint of current settings to decide if cached index is valid
        import hashlib, json as _json
        _fingerprint = hashlib.md5(
            _json.dumps(
                {
                    "source": _source,
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap,
                    "embedding": embedding_model,
                    "language": language,
                    "ocr_used": bool(load_info.get("ocr_used")),
                    "force_ocr": bool(language == "punjabi" and force_ocr),
                    "max_ocr_pages": max_ocr_pages if language == "punjabi" else None,
                    "ocr_dpi": ocr_dpi if language == "punjabi" else None,
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()[:8]
        FAISS_PATH = rag_helpers.faiss_dir_for(language)
        FINGERPRINT_FILE = os.path.join(FAISS_PATH, "fingerprint.txt")

        # Check if the cached index matches current settings
        cached_fingerprint = None
        if os.path.exists(FINGERPRINT_FILE):
            with open(FINGERPRINT_FILE) as f:
                cached_fingerprint = f.read().strip()

        if cached_fingerprint == _fingerprint and os.path.exists(os.path.join(FAISS_PATH, "index.faiss")):
            with st.spinner("Loading cached vector store..."):
                persisted_vectorstore = FAISS.load_local(
                    FAISS_PATH, embeddings, allow_dangerous_deserialization=True
                )
                st.success(f"✓ Loaded cached vector store for `{_source}` (chunk={chunk_size}, overlap={chunk_overlap})")
        else:
            with st.spinner("Embedding model test..."):
                test_embedding = embeddings.embed_query("ਵਾਹਿਗੁਰੂ" if language == "punjabi" else "test")
                st.success(f"✓ Embedding model works! Vector size: {len(test_embedding)}")

            with st.spinner("Creating vector store (embedding in batches)..."):
                BATCH_SIZE = 8
                vectorstore = None
                progress = st.progress(0)
                for i in range(0, len(docs), BATCH_SIZE):
                    batch = docs[i:i + BATCH_SIZE]
                    for attempt in range(3):
                        try:
                            if vectorstore is None:
                                vectorstore = FAISS.from_documents(batch, embeddings)
                            else:
                                batch_vs = FAISS.from_documents(batch, embeddings)
                                vectorstore.merge_from(batch_vs)
                            break
                        except Exception:
                            if attempt < 2:
                                time.sleep(2 ** attempt)
                            else:
                                raise
                    time.sleep(0.5)
                    progress.progress(min((i + BATCH_SIZE) / len(docs), 1.0))
                progress.empty()

            with st.spinner("Saving vector store..."):
                os.makedirs(FAISS_PATH, exist_ok=True)
                vectorstore.save_local(FAISS_PATH)
                # Save fingerprint so next run with same settings skips embedding
                with open(FINGERPRINT_FILE, "w") as f:
                    f.write(_fingerprint)
                persisted_vectorstore = FAISS.load_local(
                    FAISS_PATH, embeddings, allow_dangerous_deserialization=True
                )
                st.success("✓ Vector store created and saved")

        st.session_state.retriever = persisted_vectorstore.as_retriever(
            search_kwargs={"k": 4 if language == "punjabi" else 8}
        )
        st.session_state.vectorstore = persisted_vectorstore

        with st.spinner("Loading LLM model..."):
            llm_kwargs = {
                "model": model_name,
                "base_url": OLLAMA_HOST,
                "temperature": 0.1 if language == "punjabi" else 0.7,
            }
            if language == "punjabi":
                # Cap length to reduce looping on small multilingual models.
                llm_kwargs["num_predict"] = 120
            st.session_state.llm = OllamaLLM(**llm_kwargs)
            st.success(f"✓ LLM model ({model_name}) loaded")

        st.session_state.initialized = True
        st.session_state.rag_language = language
        st.success("✅ RAG ਪਾਈਪਲਾਈਨ ਤਿਆਰ ਹੈ!")

    except Exception as e:
        err = str(e)
        if "not found" in err.lower() or "404" in err:
            st.error(
                f"❌ Error: {err}\n\n"
                f"Pull the model on your Ollama host (`{OLLAMA_HOST}`), e.g.:\n"
                f"`ollama pull {embedding_model}` or `ollama pull nomic-embed-text`\n"
                "Then refresh this page and pick an embedding model that appears in the sidebar list."
            )
        else:
            st.error(f"❌ Error: {err}")

# ── ReFRAG helpers ────────────────────────────────────────────────────────────

def context_stats(docs: list, query: str) -> dict:
    """Compute context window metrics for a set of retrieved docs."""
    full_context = "\n\n".join([d.page_content for d in docs])
    chars = len(full_context)
    # Rough token estimate: 1 token ≈ 4 chars for English text
    est_tokens = chars // 4
    # Add prompt overhead estimate (~50 tokens for template)
    total_prompt_tokens = est_tokens + len(query) // 4 + 50
    return {
        "chunks": len(docs),
        "total_chars": chars,
        "est_context_tokens": est_tokens,
        "est_total_prompt_tokens": total_prompt_tokens,
    }


def run_llm_streaming(llm, prompt_text: str, *, prefer_invoke: bool = False) -> tuple:
    """
    Stream LLM output to capture TTFT and E2E latency.
    Returns (response, ttft_ms, llm_e2e_ms, output_tokens)

    prefer_invoke=True skips streaming (more reliable for Gurmukhi on small CPU models).
    """
    t0 = time.time()
    t_first = None
    full_response = ""
    if prefer_invoke:
        full_response = str(llm.invoke(prompt_text) or "")
        llm_e2e_ms = round((time.time() - t0) * 1000)
        t_first = t0
    else:
        try:
            for chunk in llm.stream(prompt_text):
                if t_first is None:
                    t_first = time.time()
                full_response += str(chunk)
            llm_e2e_ms = round((time.time() - t0) * 1000)
            # Empty/garbled streams → fall back to invoke
            if not full_response.strip():
                raise RuntimeError("empty stream")
        except Exception:
            full_response = str(llm.invoke(prompt_text) or "")
            llm_e2e_ms = round((time.time() - t0) * 1000)
            t_first = t0
    ttft_ms = round((t_first - t0) * 1000) if t_first else 0
    output_tokens = max(1, len(full_response) // 4)
    return full_response, ttft_ms, llm_e2e_ms, output_tokens


def retrieve_punjabi_docs(query: str, retriever, llm, *, k: int = 4) -> tuple:
    """
    Retrieve from a Punjabi index. If the user asked in English, translate to
    Gurmukhi for search and merge with the original-query hits.
    Returns (docs, retrieve_ms, search_query, translated_query).
    """
    t_retrieve = time.time()
    english_q = rag_helpers.looks_like_english(query)
    translated = ""
    if english_q:
        translated = rag_helpers.translate_english_to_gurmukhi_query(llm, query)
    search_query = translated or query
    docs_primary = retriever.invoke(search_query)
    docs_secondary = []
    if translated and translated != query:
        try:
            docs_secondary = retriever.invoke(query)
        except Exception:
            docs_secondary = []
    docs = rag_helpers.merge_retrieved_docs(docs_primary, docs_secondary, limit=k)
    retrieve_ms = round((time.time() - t_retrieve) * 1000)
    return docs, retrieve_ms, search_query, translated


def run_standard_rag(
    query: str,
    retriever,
    llm,
    language: str = "english",
    punjabi_answer_style: str = "LLM paraphrase",
) -> tuple:
    """Standard RAG. Returns (answer, docs, stats, perf) where perf = {ttft_ms, e2e_ms, input_tokens, output_tokens}."""
    english_q = language == "punjabi" and rag_helpers.looks_like_english(query)

    if language == "punjabi":
        docs, retrieve_ms, search_query, translated = retrieve_punjabi_docs(
            query, retriever, llm, k=4
        )
    else:
        t_retrieve = time.time()
        docs = retriever.invoke(query)
        retrieve_ms = round((time.time() - t_retrieve) * 1000)
        search_query, translated = query, ""

    # Small multilingual models handle shorter Punjabi contexts more reliably.
    use_docs = docs[:2] if language == "punjabi" else docs

    if language == "punjabi" and punjabi_answer_style.startswith("Grounded quote"):
        answer = rag_helpers.extractive_punjabi_answer(use_docs, query)
        stats = context_stats(use_docs, query)
        perf = {
            "ttft_ms": retrieve_ms,
            "e2e_ms": retrieve_ms,
            "retrieve_ms": retrieve_ms,
            "input_tokens": stats["est_total_prompt_tokens"],
            "output_tokens": max(1, len(answer) // 4),
            "search_query": search_query,
            "translated_query": translated,
        }
        return answer, use_docs, stats, perf

    context = "\n\n".join([d.page_content for d in use_docs])
    prompt_text = rag_helpers.answer_prompt(
        language, context, query, english_question=english_q
    )
    answer, ttft_ms, llm_e2e_ms, output_tokens = run_llm_streaming(
        llm, prompt_text, prefer_invoke=(language == "punjabi")
    )
    if language == "punjabi":
        extractive = rag_helpers.extractive_punjabi_answer(use_docs, query)
        # Prefer extractive when generation is empty, non-Gurmukhi, looping, or weakly grounded.
        if rag_helpers.is_low_quality_gurmukhi_answer(answer):
            answer = extractive
        else:
            # Require at least some token overlap with retrieved context.
            ctx_tokens = set(context.replace("।", " ").split())
            ans_tokens = set(answer.replace("।", " ").split())
            if len(ctx_tokens & ans_tokens) < 3:
                answer = extractive
        output_tokens = max(1, len(answer) // 4)
    stats = context_stats(use_docs, query)
    perf = {
        "ttft_ms": retrieve_ms + ttft_ms,   # user-facing: includes retrieval wait
        "e2e_ms": retrieve_ms + llm_e2e_ms, # full round-trip
        "retrieve_ms": retrieve_ms,
        "input_tokens": stats["est_total_prompt_tokens"],
        "output_tokens": output_tokens,
        "search_query": search_query,
        "translated_query": translated if language == "punjabi" else "",
    }
    return answer, use_docs, stats, perf

def score_chunk_relevance(llm, query: str, chunk: str, language: str = "english") -> bool:
    """Ask the LLM whether a chunk is relevant to the query. Returns True/False."""
    prompt = rag_helpers.relevance_prompt(language, query, chunk)
    try:
        resp = llm.invoke(prompt).strip().lower()
        return resp.startswith("yes") or resp.startswith("ਹਾਂ")
    except Exception:
        return True  # default to keeping the chunk on error


def reformulate_query(llm, original_query: str, retrieved_chunks: list, language: str = "english") -> str:
    """Ask the LLM to reformulate the query given that retrieved chunks weren't relevant enough."""
    prompt = rag_helpers.reformulate_prompt(language, original_query, retrieved_chunks)
    try:
        return llm.invoke(prompt).strip()
    except Exception:
        return original_query


def run_refrag(query: str, vectorstore, llm, top_k: int, min_relevant: int, language: str = "english"):
    """
    ReFRAG pipeline. Returns (answer, final_docs, steps, stats, perf).
    """
    steps = []
    t_start = time.time()
    english_q = language == "punjabi" and rag_helpers.looks_like_english(query)

    # Step 1: Initial retrieval (English → Gurmukhi when needed)
    retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})
    if language == "punjabi":
        initial_docs, retrieve_ms, search_query, translated = retrieve_punjabi_docs(
            query, retriever, llm, k=top_k
        )
        if translated:
            steps.append(
                ("🌐 English → Punjabi search", f"Translated query: *{translated}*")
            )
    else:
        t_retrieve = time.time()
        initial_docs = retriever.invoke(query)
        retrieve_ms = round((time.time() - t_retrieve) * 1000)
        search_query, translated = query, ""
    steps.append(
        ("🔍 Initial retrieval", f"Retrieved {len(initial_docs)} chunks for: *{search_query}*")
    )

    # Step 2: Score relevance (use Gurmukhi search query when available)
    relevance_query = search_query if language == "punjabi" else query
    relevant_docs = []
    irrelevant_docs = []
    for doc in initial_docs:
        if score_chunk_relevance(llm, relevance_query, doc.page_content, language=language):
            relevant_docs.append(doc)
        else:
            irrelevant_docs.append(doc)
    steps.append(("🧠 Relevance filtering",
                  f"{len(relevant_docs)} relevant / {len(irrelevant_docs)} filtered out"))

    # Step 3: Reformulate if not enough relevant chunks
    reformulated_query = None
    if len(relevant_docs) < min_relevant:
        reformulate_seed = search_query if language == "punjabi" else query
        reformulated_query = reformulate_query(
            llm, reformulate_seed, initial_docs, language=language
        )
        steps.append(("✏️ Query reformulation", f"New query: *{reformulated_query}*"))
        retriever2 = vectorstore.as_retriever(search_kwargs={"k": top_k})
        extra_docs = retriever2.invoke(reformulated_query)
        for doc in extra_docs:
            if doc not in relevant_docs and score_chunk_relevance(
                llm, reformulated_query, doc.page_content, language=language
            ):
                relevant_docs.append(doc)
        steps.append(("🔍 Re-retrieval",
                      f"After re-retrieval: {len(relevant_docs)} relevant chunks total"))

    final_docs = relevant_docs if relevant_docs else initial_docs

    # Step 4: Generate answer with streaming metrics
    context = "\n\n".join([doc.page_content for doc in final_docs])
    effective_query = reformulated_query or query
    prompt_text = rag_helpers.answer_prompt(
        language, context, effective_query, english_question=english_q
    )
    answer, ttft_ms, llm_e2e_ms, output_tokens = run_llm_streaming(
        llm, prompt_text, prefer_invoke=(language == "punjabi")
    )
    if language == "punjabi" and rag_helpers.is_low_quality_gurmukhi_answer(answer):
        answer = rag_helpers.extractive_punjabi_answer(final_docs, query)
        output_tokens = max(1, len(answer) // 4)
    stats = context_stats(final_docs, effective_query)
    perf = {
        "ttft_ms": retrieve_ms + ttft_ms,
        "e2e_ms": round((time.time() - t_start) * 1000),
        "retrieve_ms": retrieve_ms,
        "input_tokens": stats["est_total_prompt_tokens"],
        "output_tokens": output_tokens,
        "search_query": search_query,
        "translated_query": translated if language == "punjabi" else "",
    }
    return answer, final_docs, steps, stats, perf


# ── Query interface ────────────────────────────────────────────────────────────

def render_perf_metrics(perf: dict):
    """Display TTFT, E2E Latency, and Token Cost/Consumption as a metric row."""
    c1, c2, c3 = st.columns(3)
    c1.metric(
        "⚡ TTFT",
        f"{perf['ttft_ms']:,} ms",
        help="Time to First Token — retrieval wait + time until LLM starts generating. Key user-experience metric."
    )
    c2.metric(
        "⏱️ E2E Latency",
        f"{perf['e2e_ms']:,} ms",
        help="End-to-End Latency — total time from query submission to full response."
    )
    total_tokens = perf["input_tokens"] + perf["output_tokens"]
    c3.metric(
        "🪙 Token Consumption",
        f"{total_tokens:,}",
        help=f"Input tokens: {perf['input_tokens']:,}  |  Output tokens: {perf['output_tokens']:,}"
    )
    st.caption(
        f"📥 Input tokens: `{perf['input_tokens']:,}` &nbsp;·&nbsp; "
        f"📤 Output tokens: `{perf['output_tokens']:,}` &nbsp;·&nbsp; "
        f"🔍 Retrieval: `{perf.get('retrieve_ms', 0):,} ms`"
    )
    translated = (perf.get("translated_query") or "").strip()
    if translated:
        st.caption(f"🌐 English question searched as: `{translated}`")


def _translit_scheme() -> str:
    return "iast" if "IAST" in transliteration_style else "simple"


def render_punjabi_text(text: str, *, preview_chars: int | None = None):
    """Render Gurmukhi text with optional Punjabi English (Roman) reading."""
    body = text if preview_chars is None else (text[:preview_chars] + ("..." if len(text) > preview_chars else ""))
    show_gurmukhi = transliteration_display != "Punjabi English only"
    show_roman = show_punjabi_english and transliteration_display != "Gurmukhi only"

    if show_gurmukhi:
        st.write(body)
    if show_roman:
        try:
            roman = rag_helpers.gurmukhi_to_punjabi_english(body, style=_translit_scheme())
        except Exception as e:
            st.caption(f"Punjabi English unavailable: {e}")
            if not show_gurmukhi:
                st.write(body)
            return
        if transliteration_display == "Punjabi English only":
            st.write(roman)
        else:
            st.caption("Punjabi English (Roman)")
            st.markdown(f"*{roman}*")


def render_source_docs(docs, *, preview: int = 500, label_prefix: str = "Document"):
    for i, doc in enumerate(docs, 1):
        st.markdown(f"**{label_prefix} {i}:**")
        render_punjabi_text(doc.page_content, preview_chars=preview)
        st.markdown("---")


def render_stats_card(stats: dict, label: str, color: str):
    """Render a context window stats card."""
    st.markdown(f"""
    <div style="background:#111111;color:#ffffff;padding:1rem;border-radius:8px;margin-bottom:0.5rem;border:1px solid #333;">
        <b>{label}</b><br/>
        📦 <b>Chunks used:</b> {stats['chunks']}<br/>
        📝 <b>Context characters:</b> {stats['total_chars']:,}<br/>
        🔢 <b>Est. context tokens:</b> {stats['est_context_tokens']:,}<br/>
        📨 <b>Est. total prompt tokens:</b> {stats['est_total_prompt_tokens']:,}
    </div>
    """, unsafe_allow_html=True)


if st.session_state.initialized:
    st.markdown("---")
    active_lang = st.session_state.get("rag_language", language)
    if answer_script == "roman":
        st.subheader("🔍 Ask in English")
        st.caption("Answers are shown in Punjabi English (Roman Punjabi), not English.")
        q_label = "Your question (English):"
        q_placeholder = "e.g., Who founded Sikhism? What are the Five Ks?"
        q_button = "Search"
    elif active_lang == "punjabi":
        st.subheader("🔍 ਸਵਾਲ ਪੁੱਛੋ")
        q_label = "ਤੁਹਾਡਾ ਸਵਾਲ:"
        q_placeholder = "ਉਦਾਹਰਨ: ਸਿੱਖ ਧਰਮ ਕਿਸ ਨੇ ਸਥਾਪਿਤ ਕੀਤਾ? ਪੰਜ ਕਕਾਰ ਕੀ ਹਨ? (or ask in English)"
        q_button = "ਖੋਜੋ"
    else:
        st.subheader("🔍 Ask a Question")
        q_label = "Your question:"
        q_placeholder = "e.g., What is Sikhism? Who founded it?"
        q_button = "Search"

    col1, col2 = st.columns([4, 1])
    with col1:
        query = st.text_input(q_label, placeholder=q_placeholder)
    with col2:
        search_button = st.button(q_button, type="primary")

    if search_button and query:

        # ── Compare Both ──────────────────────────────────────────────────────
        if rag_mode == "⚖️ Compare Both":
            with st.spinner("Running Standard RAG..."):
                try:
                    rag_answer, rag_docs, rag_stats, rag_perf = run_standard_rag(
                        query,
                        st.session_state.retriever,
                        st.session_state.llm,
                        language=active_lang,
                        punjabi_answer_style=punjabi_answer_style,
                    )
                except Exception as e:
                    st.error(f"❌ Standard RAG error: {e}")
                    st.stop()

            with st.spinner("Running ReFRAG (this takes longer due to chunk scoring)..."):
                try:
                    ref_answer, ref_docs, ref_steps, ref_stats, ref_perf = run_refrag(
                        query,
                        st.session_state.vectorstore,
                        st.session_state.llm,
                        top_k=refrag_top_k,
                        min_relevant=refrag_relevance_threshold,
                        language=active_lang,
                    )
                except Exception as e:
                    st.error(f"❌ ReFRAG error: {e}")
                    st.stop()

            # Performance + context window comparison banner
            st.markdown("### 📊 Performance & Context Window Comparison")
            m1, m2, m3, m4, m5, m6 = st.columns(6)
            m1.metric("RAG TTFT", f"{rag_perf['ttft_ms']:,} ms")
            m2.metric("ReFRAG TTFT", f"{ref_perf['ttft_ms']:,} ms",
                      delta=f"{ref_perf['ttft_ms']-rag_perf['ttft_ms']:+,} ms", delta_color="inverse")
            m3.metric("RAG E2E", f"{rag_perf['e2e_ms']:,} ms")
            m4.metric("ReFRAG E2E", f"{ref_perf['e2e_ms']:,} ms",
                      delta=f"{ref_perf['e2e_ms']-rag_perf['e2e_ms']:+,} ms", delta_color="inverse")
            rag_total_tok = rag_perf["input_tokens"] + rag_perf["output_tokens"]
            ref_total_tok = ref_perf["input_tokens"] + ref_perf["output_tokens"]
            m5.metric("RAG Tokens", f"{rag_total_tok:,}")
            m6.metric("ReFRAG Tokens", f"{ref_total_tok:,}",
                      delta=f"{ref_total_tok-rag_total_tok:+,}", delta_color="inverse")

            if rag_perf["input_tokens"] > 0:
                token_reduction = (1 - ref_total_tok / max(rag_total_tok, 1)) * 100
                st.caption(f"Token reduction with ReFRAG: **{token_reduction:+.1f}%** "
                           f"({'fewer' if token_reduction > 0 else 'more'} tokens total)")
            # Save ReFRAG perf as last (more interesting for the top banner)
            st.session_state.last_perf = ref_perf
            st.session_state.last_mode = "⚖️ Compare Both (ReFRAG)"
            st.markdown("---")

            # Side-by-side answers
            col_rag, col_ref = st.columns(2)

            with col_rag:
                st.markdown("#### 📄 Standard RAG")
                render_perf_metrics(rag_perf)
                render_stats_card(rag_stats, "Context Stats", "#111111")
                st.markdown("**Answer:**")
                render_punjabi_text(rag_answer) if active_lang == "punjabi" else st.write(rag_answer)
                with st.expander("📖 Source Documents (RAG)"):
                    if active_lang == "punjabi":
                        render_source_docs(rag_docs, preview=400, label_prefix="Doc")
                    else:
                        for i, doc in enumerate(rag_docs, 1):
                            st.markdown(f"**Doc {i}:**")
                            st.text(doc.page_content[:400] + "...")
                            st.markdown("---")

            with col_ref:
                st.markdown("#### 🔬 ReFRAG")
                render_perf_metrics(ref_perf)
                render_stats_card(ref_stats, "Context Stats", "#111111")
                with st.expander("🔬 ReFRAG Pipeline Steps"):
                    for title, detail in ref_steps:
                        st.markdown(f"**{title}:** {detail}")
                st.markdown("**Answer:**")
                render_punjabi_text(ref_answer) if active_lang == "punjabi" else st.write(ref_answer)
                with st.expander("📖 Source Documents (ReFRAG)"):
                    if active_lang == "punjabi":
                        render_source_docs(ref_docs, preview=400, label_prefix="Doc")
                    else:
                        for i, doc in enumerate(ref_docs, 1):
                            st.markdown(f"**Doc {i}:**")
                            st.text(doc.page_content[:400] + "...")
                            st.markdown("---")

        # ── ReFRAG only ───────────────────────────────────────────────────────
        elif rag_mode == "ReFRAG":
            with st.spinner("Running ReFRAG pipeline..."):
                try:
                    answer, final_docs, steps, stats, perf = run_refrag(
                        query,
                        st.session_state.vectorstore,
                        st.session_state.llm,
                        top_k=refrag_top_k,
                        min_relevant=refrag_relevance_threshold,
                        language=active_lang,
                    )
                    st.session_state.last_perf = perf
                    st.session_state.last_mode = "ReFRAG"
                    render_perf_metrics(perf)
                    with st.expander("🔬 ReFRAG Pipeline Steps", expanded=True):
                        for title, detail in steps:
                            st.markdown(f"**{title}:** {detail}")
                    render_stats_card(stats, "Context Window Stats", "#111111")
                    st.markdown("### ਜਵਾਬ" if active_lang == "punjabi" else "### Answer")
                    render_punjabi_text(answer) if active_lang == "punjabi" else st.write(answer)
                    with st.expander("📖 Source Documents used"):
                        if active_lang == "punjabi":
                            render_source_docs(final_docs, preview=500)
                        else:
                            for i, doc in enumerate(final_docs, 1):
                                st.markdown(f"**Document {i}:**")
                                st.text(doc.page_content[:500] + "...")
                                st.markdown("---")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

        # ── Standard RAG only ─────────────────────────────────────────────────
        else:
            with st.spinner("ਖੋਜ ਅਤੇ ਜਵਾਬ ਤਿਆਰ ਹੋ ਰਿਹਾ ਹੈ..." if active_lang == "punjabi" else "Searching and generating answer..."):
                try:
                    response, retrieved_docs, stats, perf = run_standard_rag(
                        query,
                        st.session_state.retriever,
                        st.session_state.llm,
                        language=active_lang,
                        punjabi_answer_style=punjabi_answer_style,
                    )
                    st.session_state.last_perf = perf
                    st.session_state.last_mode = "Standard RAG"
                    render_perf_metrics(perf)
                    render_stats_card(stats, "Context Window Stats", "#111111")
                    st.markdown("### ਜਵਾਬ" if active_lang == "punjabi" else "### Answer")
                    render_punjabi_text(response) if active_lang == "punjabi" else st.write(response)
                    with st.expander("📖 Source Documents"):
                        if active_lang == "punjabi":
                            render_source_docs(retrieved_docs, preview=500)
                        else:
                            for i, doc in enumerate(retrieved_docs, 1):
                                st.markdown(f"**Document {i}:**")
                                st.text(doc.page_content[:500] + "...")
                                st.markdown("---")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

else:
    if answer_script == "roman":
        tip = "👈 Click Initialize RAG Pipeline, then ask in English — answers come in Punjabi English (Roman)."
    elif language == "punjabi":
        tip = "👈 ਖੱਬੇ ਪਾਸੇ 'Initialize RAG Pipeline' ਦਬਾਓ ਅਤੇ ਫਿਰ ਪੰਜਾਬੀ ਸਵਾਲ ਪੁੱਛੋ (Punjabi or English)!"
    else:
        tip = "👈 Click 'Initialize RAG Pipeline' to get started!"
    st.info(tip)

# Footer
st.markdown("---")
st.markdown("Made with ❤️ using LangChain, Ollama, and Streamlit · Punjabi RAG uses `bge-m3` + Gurmukhi prompts")
