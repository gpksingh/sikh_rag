import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_community.vectorstores import FAISS
import os
import tempfile
import requests
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
    
    model_name = st.selectbox(
        "LLM Model",
        ["gemma3:4b", "gemma:4b", "mistral", "llama2", "neural-chat", "gemma:7b"],
        index=0
    )
    
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
        help="Standard RAG: retrieve → generate.\nReFRAG: retrieve → LLM filters relevant chunks → reformulate query if needed → generate.\nCompare Both: run both and show context window metrics side-by-side."
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


def run_standard_rag(query: str, retriever, llm) -> tuple:
    """Standard RAG: retrieve → generate. Returns (answer, docs, stats)."""
    docs = retriever.invoke(query)
    context = "\n\n".join([d.page_content for d in docs])
    prompt_text = f"""Based on the following context about Sikhism, answer the question accurately.

Context:
{context}

Question: {query}

Answer:"""
    answer = llm.invoke(prompt_text)
    stats = context_stats(docs, query)
    return answer, docs, stats

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
    ReFRAG pipeline:
    1. Retrieve top_k chunks
    2. Score each chunk for relevance with the LLM
    3. If fewer than min_relevant chunks pass, reformulate the query and retrieve again
    4. Combine all relevant chunks and generate the final answer
    """
    steps = []

    # Step 1: Initial retrieval
    retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})
    initial_docs = retriever.invoke(query)
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

    # Fall back to all initial docs if still nothing passed
    final_docs = relevant_docs if relevant_docs else initial_docs

    # Step 4: Generate answer
    context = "\n\n".join([doc.page_content for doc in final_docs])
    effective_query = reformulated_query or query
    prompt_text = f"""Based on the following context about Sikhism, answer the question accurately.

Context:
{context}

Question: {effective_query}

Answer:"""
    answer = llm.invoke(prompt_text)

    return answer, final_docs, steps, context_stats(final_docs, effective_query)


# ── Query interface ────────────────────────────────────────────────────────────

def render_stats_card(stats: dict, label: str, color: str):
    """Render a context window stats card."""
    st.markdown(f"""
    <div style="background:{color};padding:1rem;border-radius:8px;margin-bottom:0.5rem;">
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

        # ── Compare Both ──────────────────────────────────────────────────────
        if rag_mode == "⚖️ Compare Both":
            with st.spinner("Running Standard RAG..."):
                try:
                    rag_answer, rag_docs, rag_stats = run_standard_rag(
                        query, st.session_state.retriever, st.session_state.llm
                    )
                except Exception as e:
                    st.error(f"❌ Standard RAG error: {e}")
                    st.stop()

            with st.spinner("Running ReFRAG (this takes longer due to chunk scoring)..."):
                try:
                    ref_answer, ref_docs, ref_steps, ref_stats = run_refrag(
                        query,
                        st.session_state.vectorstore,
                        st.session_state.llm,
                        top_k=refrag_top_k,
                        min_relevant=refrag_relevance_threshold,
                    )
                except Exception as e:
                    st.error(f"❌ ReFRAG error: {e}")
                    st.stop()

            # Context window comparison banner
            st.markdown("### 📊 Context Window Comparison")
            m1, m2, m3, m4 = st.columns(4)
            delta_chunks = ref_stats["chunks"] - rag_stats["chunks"]
            delta_tokens = ref_stats["est_context_tokens"] - rag_stats["est_context_tokens"]
            m1.metric("RAG Chunks", rag_stats["chunks"])
            m2.metric("ReFRAG Chunks", ref_stats["chunks"], delta=delta_chunks,
                      delta_color="inverse")
            m3.metric("RAG Est. Tokens", f"{rag_stats['est_context_tokens']:,}")
            m4.metric("ReFRAG Est. Tokens", f"{ref_stats['est_context_tokens']:,}",
                      delta=delta_tokens, delta_color="inverse")

            # Token reduction bar
            if rag_stats["est_context_tokens"] > 0:
                reduction_pct = (1 - ref_stats["est_context_tokens"] / rag_stats["est_context_tokens"]) * 100
                st.markdown(f"**Token reduction with ReFRAG:** `{reduction_pct:+.1f}%` "
                            f"({'fewer' if reduction_pct > 0 else 'more'} tokens in context)")

            st.markdown("---")

            # Side-by-side answers
            col_rag, col_ref = st.columns(2)

            with col_rag:
                st.markdown("#### 📄 Standard RAG")
                render_stats_card(rag_stats, "Context Stats", "#f0f4ff")
                st.markdown("**Answer:**")
                st.write(rag_answer)
                with st.expander("📖 Source Documents (RAG)"):
                    for i, doc in enumerate(rag_docs, 1):
                        st.markdown(f"**Doc {i}:**")
                        st.text(doc.page_content[:400] + "...")
                        st.markdown("---")

            with col_ref:
                st.markdown("#### 🔬 ReFRAG")
                render_stats_card(ref_stats, "Context Stats", "#f0fff4")
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
                    answer, final_docs, steps, stats = run_refrag(
                        query,
                        st.session_state.vectorstore,
                        st.session_state.llm,
                        top_k=refrag_top_k,
                        min_relevant=refrag_relevance_threshold,
                    )
                    with st.expander("🔬 ReFRAG Pipeline Steps", expanded=True):
                        for title, detail in steps:
                            st.markdown(f"**{title}:** {detail}")
                    render_stats_card(stats, "Context Window Stats", "#f0fff4")
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
                    response, retrieved_docs, stats = run_standard_rag(
                        query, st.session_state.retriever, st.session_state.llm
                    )
                    render_stats_card(stats, "Context Window Stats", "#f0f4ff")
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
