import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_community.vectorstores import FAISS
import os
import tempfile
import requests
from urllib.parse import urljoin

# Get Ollama host from Streamlit secrets (for cloud) or environment (for local)
try:
    OLLAMA_HOST = st.secrets["OLLAMA_HOST"]
except (KeyError, FileNotFoundError):
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Function to test Ollama connection
def test_ollama_connection(base_url, timeout=10):
    """Test if Ollama is responding"""
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=timeout)
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

# Show Ollama status
ollama_connected = test_ollama_connection(OLLAMA_HOST, timeout=5)
status_icon = "✅" if ollama_connected else "⚠️"
status_text = "Connected" if ollama_connected else "Offline/Timeout"

st.info(f"{status_icon} **Ollama Status:** {status_text}\n\n🔗 **Host:** `{OLLAMA_HOST}`\n\n**Note:** Railway apps may take time to respond on first request. If offline, the app may be sleeping or warming up.")

# Initialize session state
if "retriever" not in st.session_state:
    st.session_state.retriever = None
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
        ["mistral", "llama2", "neural-chat", "gemma:7b"],
        index=0
    )
    
    embedding_model = st.selectbox(
        "Embedding Model",
        ["nomic-embed-text"]
    )

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
            try:
                embeddings = OllamaEmbeddings(
                    model=embedding_model, 
                    base_url=OLLAMA_HOST
                )
                test_embedding = embeddings.embed_query("test")
                st.success(f"✓ Embedding model works! Vector size: {len(test_embedding)}")
            except requests.exceptions.Timeout:
                st.error("❌ Embedding model request timed out. Railway app may be sleeping. Wait 30-60 seconds and try again.")
                st.stop()
            except Exception as e:
                st.error(f"❌ Failed to load embedding model: {str(e)}")
                st.info("💡 **Troubleshooting tips:**\n- Ensure Ollama is running on " + OLLAMA_HOST + "\n- Wait 30-60 seconds if using Railway (cold start)\n- Check that the embedding model exists on your Ollama instance")
                st.stop()
        
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
            st.session_state.retriever = persisted_vectorstore.as_retriever()
            st.success("✓ Vector store saved")
        
        with st.spinner("Loading LLM model..."):
            try:
                st.session_state.llm = OllamaLLM(
                    model=model_name, 
                    base_url=OLLAMA_HOST
                )
                st.success(f"✓ LLM model ({model_name}) loaded")
            except Exception as e:
                st.error(f"❌ Failed to load LLM model: {str(e)}")
                st.info("💡 Ensure the model '" + model_name + "' is pulled on your Ollama instance")
                st.stop()
        
        st.session_state.initialized = True
        st.success("✅ RAG Pipeline is ready!")
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# Query interface
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
        with st.spinner("Searching and generating answer..."):
            try:
                # Retrieve relevant documents
                retrieved_docs = st.session_state.retriever.invoke(query)
                
                # Combine context
                context = "\n".join([doc.page_content for doc in retrieved_docs])
                
                # Create prompt
                prompt_text = f"""Based on the following context about Sikhism, answer the question accurately.

Context:
{context}

Question: {query}

Answer:"""
                
                # Get response
                response = st.session_state.llm.invoke(prompt_text)
                
                # Display results
                st.markdown("### Answer")
                st.write(response)
                
                # Display source documents
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
