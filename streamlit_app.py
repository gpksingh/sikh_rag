import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_community.vectorstores import FAISS
import os
import tempfile
import requests
import time
from urllib.parse import urljoin

# Get Ollama configuration from Streamlit secrets (for cloud) or environment
try:
    OLLAMA_HOST = st.secrets.get("OLLAMA_HOST", "https://ollama-production-1333.up.railway.app").strip()
    OLLAMA_API_KEY = st.secrets.get("OLLAMA_API_KEY", "").strip()
except (KeyError, FileNotFoundError, Exception):
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "https://ollama-production-1333.up.railway.app").strip()
    OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "").strip()

# Build auth headers if API key is present
OLLAMA_HEADERS = {"Authorization": f"Bearer {OLLAMA_API_KEY}"} if OLLAMA_API_KEY else {}

# Debug: show if key is loaded (shows only first/last 4 chars for security)
if OLLAMA_API_KEY:
    masked = OLLAMA_API_KEY[:4] + "..." + OLLAMA_API_KEY[-4:]
    st.sidebar.caption(f"🔑 API Key loaded: `{masked}`")
else:
    st.sidebar.warning("⚠️ No API Key found in secrets!")

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
    except Exception as e:
        return {"status": "offline", "latency_ms": None}


# Page config
st.set_page_config(page_title="Sikh RAG", layout="wide")

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

# Title and description
st.title("📚 Sikh Religious Texts RAG")
st.markdown("Ask questions about Sikhism and get answers based on the sacred texts")

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

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # PDF Source Selection
    pdf_source = st.radio(
        "📄 Select PDF Source",
        ["Use Default PDF", "Upload Your Own PDF"],
        index=0
    )
    
    if pdf_source == "Use Default PDF":
        pdf_books = {
            "a-brief-introduction-to-sikhism-gurbachan-singh-sidhu.pdf": "a-brief-introduction-to-sikhism-gurbachan-singh-sidhu.pdf",
            "Sikh_Religion_Vol_1.pdf": "Sikh_Religion_Vol_1.pdf"
        }
        selected_book = st.selectbox(
            "📖 Select Book",
            list(pdf_books.keys()),
            index=0
        )
        pdf_path = selected_book
        uploaded_file = None
    else:
        st.info("📤 Upload a PDF file to analyze")
        uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
        if uploaded_file is not None:
            st.success(f"✅ File uploaded: {uploaded_file.name}")
        pdf_path = None
    
    chunk_size = st.slider("Chunk Size", 500, 2000, 1000, 100)
    chunk_overlap = st.slider("Chunk Overlap", 0, 500, 30, 50)
    
    # Dynamically fetch available LLM models from the connected Ollama host
    @st.cache_data(ttl=60, show_spinner=False)
    def get_available_models(host):
        try:
            resp = requests.get(f"{host}/api/tags", timeout=5)
            if resp.status_code == 200:
                all_models = [m["name"] for m in resp.json().get("models", [])]
                # Exclude embedding models
                return [m for m in all_models if "embed" not in m.lower()] or ["gemma3:4b"]
        except Exception:
            pass
        return ["gemma3:4b"]

    available_llm_models = get_available_models(OLLAMA_HOST)
    model_name = st.selectbox(
        "LLM Model",
        available_llm_models,
        index=0
    )
    st.caption(f"🔗 Models from `{OLLAMA_HOST}`")
    
    embedding_model = st.selectbox(
        "Embedding Model",
        ["nomic-embed-text"]
    )

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
    elif rag_mode == "🖥️ Local vs ☁️ Cloud":
        st.info("Runs the **same model** on two Ollama instances and compares answers + latency side-by-side.")
        st.caption("⚠️ **Local URL** must be reachable from where this app is running. If using Streamlit Cloud, expose your local Ollama with a tunnel (e.g. [ngrok](https://ngrok.com)) or run this app locally with `streamlit run streamlit_app.py`.")
        local_host = st.text_input("🖥️ Instance A URL (local)", value="http://localhost:11434")
        cloud_host = st.text_input("☁️ Instance B URL (cloud)", value=OLLAMA_HOST)
        local_available = test_ollama_connection(local_host, timeout=3)
        cloud_available = test_ollama_connection(cloud_host, timeout=5)
        compare_model = st.selectbox(
            "Model to compare",
            get_available_models(local_host) if local_available else get_available_models(OLLAMA_HOST),
            index=0
        )
        a_status = "✅ Online" if local_available else "❌ Offline"
        b_status = "✅ Online" if cloud_available else "❌ Offline"
        st.markdown(f"**Instance A:** {a_status} &nbsp;&nbsp;|&nbsp;&nbsp; **Instance B:** {b_status}")
        refrag_top_k = 4
        refrag_relevance_threshold = 2
    else:
        refrag_top_k = 4
        refrag_relevance_threshold = 2

# Initialize RAG pipeline
if st.button("🚀 Initialize RAG Pipeline", key="init_button"):
    try:
        # Check if user uploaded a file or using default
        if pdf_source == "Upload Your Own PDF" and uploaded_file is not None:
            # Handle uploaded file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getbuffer())
                tmp_path = tmp_file.name
            
            with st.spinner("Loading uploaded PDF..."):
                loader = PyPDFLoader(tmp_path)
                documents = loader.load()
                st.success(f"✓ Loaded {len(documents)} pages from '{uploaded_file.name}'")
            
            # Clean up temp file
            import atexit
            atexit.register(lambda: os.unlink(tmp_path) if os.path.exists(tmp_path) else None)
        
        elif pdf_source == "Use Default PDF" and pdf_path:
            # Handle default PDF path
            with st.spinner("Loading PDF..."):
                loader = PyPDFLoader(pdf_path)
                documents = loader.load()
                st.success(f"✓ Loaded {len(documents)} pages")
        
        else:
            st.error("❌ Please select a PDF source and upload a file or select a book!")
            st.stop()
        
        with st.spinner("Splitting documents..."):
            text_splitter = CharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separator="\n"
            )
            docs = text_splitter.split_documents(documents=documents)
            st.success(f"✓ Created {len(docs)} chunks")
        
        with st.spinner("Loading embedding model (this may take 30+ seconds on first request)..."):
            embeddings = OllamaEmbeddings(
                model=embedding_model,
                base_url=OLLAMA_HOST,
            )
            test_embedding = embeddings.embed_query("test")
            st.success(f"✓ Embedding model works! Vector size: {len(test_embedding)}")
        
        with st.spinner("Creating vector store..."):
            vectorstore = FAISS.from_documents(docs, embeddings)
            st.success("✓ Vector store created")
        
        with st.spinner("Saving vector store..."):
            vectorstore.save_local("faiss_index_")
            persisted_vectorstore = FAISS.load_local(
                "faiss_index_",
                embeddings,
                allow_dangerous_deserialization=True
            )
            st.session_state.retriever = persisted_vectorstore.as_retriever(search_kwargs={"k": 8})
            st.session_state.vectorstore = persisted_vectorstore
            st.success("✓ Vector store saved")
        
        with st.spinner("Loading LLM model..."):
            st.session_state.llm = OllamaLLM(
                model=model_name,
                base_url=OLLAMA_HOST,
            )
            st.success(f"✓ LLM model ({model_name}) loaded")
        
        st.session_state.initialized = True
        st.success("✅ RAG Pipeline is ready!")
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

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


def run_llm_streaming(llm, prompt_text: str) -> tuple:
    """
    Stream LLM output to capture TTFT and E2E latency.
    Returns (response, ttft_ms, llm_e2e_ms, output_tokens)
    """
    t0 = time.time()
    t_first = None
    full_response = ""
    try:
        for chunk in llm.stream(prompt_text):
            if t_first is None:
                t_first = time.time()
            full_response += str(chunk)
        llm_e2e_ms = round((time.time() - t0) * 1000)
    except Exception:
        # Fallback if streaming not supported
        full_response = llm.invoke(prompt_text)
        llm_e2e_ms = round((time.time() - t0) * 1000)
        t_first = t0
    ttft_ms = round((t_first - t0) * 1000) if t_first else 0
    output_tokens = max(1, len(full_response) // 4)
    return full_response, ttft_ms, llm_e2e_ms, output_tokens


def run_standard_rag(query: str, retriever, llm) -> tuple:
    """Standard RAG. Returns (answer, docs, stats, perf) where perf = {ttft_ms, e2e_ms, input_tokens, output_tokens}."""
    t_retrieve = time.time()
    docs = retriever.invoke(query)
    retrieve_ms = round((time.time() - t_retrieve) * 1000)

    context = "\n\n".join([d.page_content for d in docs])
    prompt_text = f"""Based on the following context about Sikhism, answer the question accurately.

Context:
{context}

Question: {query}

Answer:"""
    answer, ttft_ms, llm_e2e_ms, output_tokens = run_llm_streaming(llm, prompt_text)
    stats = context_stats(docs, query)
    perf = {
        "ttft_ms": retrieve_ms + ttft_ms,   # user-facing: includes retrieval wait
        "e2e_ms": retrieve_ms + llm_e2e_ms, # full round-trip
        "retrieve_ms": retrieve_ms,
        "input_tokens": stats["est_total_prompt_tokens"],
        "output_tokens": output_tokens,
    }
    return answer, docs, stats, perf

def score_chunk_relevance(llm, query: str, chunk: str) -> bool:
    """Ask the LLM whether a chunk is relevant to the query. Returns True/False."""
    prompt = f"""You are a relevance filter. Answer ONLY with 'yes' or 'no'.

Is the following passage relevant to answering this question?

Question: {query}

Passage:
{chunk[:800]}

Answer (yes/no):"""
    try:
        resp = llm.invoke(prompt).strip().lower()
        return resp.startswith("yes")
    except Exception:
        return True  # default to keeping the chunk on error


def reformulate_query(llm, original_query: str, retrieved_chunks: list) -> str:
    """Ask the LLM to reformulate the query given that retrieved chunks weren't relevant enough."""
    context_sample = "\n---\n".join([c.page_content[:300] for c in retrieved_chunks[:3]])
    prompt = f"""The following question was asked but the retrieved passages were not relevant enough.

Original question: {original_query}

Sample of what was retrieved:
{context_sample}

Please rewrite the question to be more specific and likely to retrieve better passages from a Sikh religious text.
Return ONLY the rewritten question, nothing else."""
    try:
        return llm.invoke(prompt).strip()
    except Exception:
        return original_query


def run_refrag(query: str, vectorstore, llm, top_k: int, min_relevant: int):
    """
    ReFRAG pipeline. Returns (answer, final_docs, steps, stats, perf).
    """
    steps = []
    t_start = time.time()

    # Step 1: Initial retrieval
    t_retrieve = time.time()
    retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})
    initial_docs = retriever.invoke(query)
    retrieve_ms = round((time.time() - t_retrieve) * 1000)
    steps.append(("🔍 Initial retrieval", f"Retrieved {len(initial_docs)} chunks for: *{query}*"))

    # Step 2: Score relevance
    relevant_docs = []
    irrelevant_docs = []
    for doc in initial_docs:
        if score_chunk_relevance(llm, query, doc.page_content):
            relevant_docs.append(doc)
        else:
            irrelevant_docs.append(doc)
    steps.append(("🧠 Relevance filtering",
                  f"{len(relevant_docs)} relevant / {len(irrelevant_docs)} filtered out"))

    # Step 3: Reformulate if not enough relevant chunks
    reformulated_query = None
    if len(relevant_docs) < min_relevant:
        reformulated_query = reformulate_query(llm, query, initial_docs)
        steps.append(("✏️ Query reformulation", f"New query: *{reformulated_query}*"))
        retriever2 = vectorstore.as_retriever(search_kwargs={"k": top_k})
        extra_docs = retriever2.invoke(reformulated_query)
        for doc in extra_docs:
            if doc not in relevant_docs and score_chunk_relevance(llm, reformulated_query, doc.page_content):
                relevant_docs.append(doc)
        steps.append(("🔍 Re-retrieval",
                      f"After re-retrieval: {len(relevant_docs)} relevant chunks total"))

    final_docs = relevant_docs if relevant_docs else initial_docs

    # Step 4: Generate answer with streaming metrics
    context = "\n\n".join([doc.page_content for doc in final_docs])
    effective_query = reformulated_query or query
    prompt_text = f"""Based on the following context about Sikhism, answer the question accurately.

Context:
{context}

Question: {effective_query}

Answer:"""
    answer, ttft_ms, llm_e2e_ms, output_tokens = run_llm_streaming(llm, prompt_text)
    stats = context_stats(final_docs, effective_query)
    perf = {
        "ttft_ms": retrieve_ms + ttft_ms,
        "e2e_ms": round((time.time() - t_start) * 1000),
        "retrieve_ms": retrieve_ms,
        "input_tokens": stats["est_total_prompt_tokens"],
        "output_tokens": output_tokens,
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
    st.subheader("🔍 Ask a Question")

    col1, col2 = st.columns([4, 1])
    with col1:
        query = st.text_input(
            "Your question:",
            placeholder="e.g., What is Sikhism? Who founded it?"
        )
    with col2:
        search_button = st.button("Search", type="primary")

    if search_button and query:

        # ── Local vs Cloud ────────────────────────────────────────────────────
        if rag_mode == "🖥️ Local vs ☁️ Cloud":
            st.markdown("### 🖥️ Instance A vs ☁️ Instance B")
            st.markdown(f"**Model:** `{compare_model}` &nbsp;|&nbsp; **Query:** *{query}*")
            st.markdown("---")

            col_local, col_cloud = st.columns(2)

            def run_comparison_side(host: str, label: str, available: bool, col):
                with col:
                    st.markdown(f"#### {label}")
                    st.caption(f"🔗 `{host}`")
                    if not available:
                        st.error(
                            f"❌ Cannot reach `{host}`\n\n"
                            "**If running on Streamlit Cloud:** expose your local Ollama via "
                            "[ngrok](https://ngrok.com) and paste the public URL above.\n\n"
                            "**If running locally:** make sure `ollama serve` is running."
                        )
                        return
                    with st.spinner(f"Querying {label}..."):
                        try:
                            llm_instance = OllamaLLM(model=compare_model, base_url=host)
                            retriever_instance = st.session_state.vectorstore.as_retriever(
                                search_kwargs={"k": 4}
                            )
                            answer, docs, stats, perf = run_standard_rag(
                                query, retriever_instance, llm_instance
                            )
                            st.session_state.last_perf = perf
                            st.session_state.last_mode = f"Local vs Cloud ({label})"
                            render_perf_metrics(perf)
                            render_stats_card(stats, "Context Stats", "#111111")
                            st.markdown("**Answer:**")
                            st.write(answer)
                            with st.expander("📖 Source Documents"):
                                for i, doc in enumerate(docs, 1):
                                    st.markdown(f"**Doc {i}:**")
                                    st.text(doc.page_content[:400] + "...")
                                    st.markdown("---")
                        except Exception as e:
                            st.error(f"❌ Error: {e}")

            run_comparison_side(local_host, "🖥️ Instance A (Local)", local_available, col_local)
            run_comparison_side(cloud_host, "☁️ Instance B (Cloud)", cloud_available, col_cloud)

        # ── Compare Both ──────────────────────────────────────────────────────
        elif rag_mode == "⚖️ Compare Both":
            with st.spinner("Running Standard RAG..."):
                try:
                    rag_answer, rag_docs, rag_stats, rag_perf = run_standard_rag(
                        query, st.session_state.retriever, st.session_state.llm
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
                st.write(rag_answer)
                with st.expander("📖 Source Documents (RAG)"):
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
                st.write(ref_answer)
                with st.expander("📖 Source Documents (ReFRAG)"):
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
                    )
                    st.session_state.last_perf = perf
                    st.session_state.last_mode = "ReFRAG"
                    render_perf_metrics(perf)
                    with st.expander("🔬 ReFRAG Pipeline Steps", expanded=True):
                        for title, detail in steps:
                            st.markdown(f"**{title}:** {detail}")
                    render_stats_card(stats, "Context Window Stats", "#111111")
                    st.markdown("### Answer")
                    st.write(answer)
                    with st.expander("📖 Source Documents used"):
                        for i, doc in enumerate(final_docs, 1):
                            st.markdown(f"**Document {i}:**")
                            st.text(doc.page_content[:500] + "...")
                            st.markdown("---")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

        # ── Standard RAG only ─────────────────────────────────────────────────
        else:
            with st.spinner("Searching and generating answer..."):
                try:
                    response, retrieved_docs, stats, perf = run_standard_rag(
                        query, st.session_state.retriever, st.session_state.llm
                    )
                    st.session_state.last_perf = perf
                    st.session_state.last_mode = "Standard RAG"
                    render_perf_metrics(perf)
                    render_stats_card(stats, "Context Window Stats", "#111111")
                    st.markdown("### Answer")
                    st.write(response)
                    with st.expander("📖 Source Documents"):
                        for i, doc in enumerate(retrieved_docs, 1):
                            st.markdown(f"**Document {i}:**")
                            st.text(doc.page_content[:500] + "...")
                            st.markdown("---")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

else:
    st.info("👈 Click 'Initialize RAG Pipeline' to get started!")

# Footer
st.markdown("---")
st.markdown("Made with ❤️ using LangChain, Ollama, and Streamlit")
