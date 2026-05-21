# LangChain v0.2+ Quick Import Reference

## Summary Table

| Component | Old (❌ Wrong) | New (✅ Correct) |
|-----------|---|---|
| **PDF Loader** | `from langchain.document_loaders import PyPDFLoader` | `from langchain_community.document_loaders.pdf import PyPDFLoader` |
| **Text Splitter** | `from langchain.text_splitter import CharacterTextSplitter` | `from langchain_text_splitters import CharacterTextSplitter` |
| **Embeddings** | `from langchain.embeddings import HuggingFaceEmbeddings` | `from langchain_community.embeddings import HuggingFaceEmbeddings` |
| **Vector Store** | `from langchain.vectorstores import FAISS` | `from langchain_community.vectorstores import FAISS` |
| **Ollama LLM** | `from langchain.llms import Ollama` | `from langchain_ollama import OllamaLLM` |
| **Prompts** | `from langchain.prompts import ChatPromptTemplate` | `from langchain_core.prompts import ChatPromptTemplate` |
| **Runnables** | `from langchain.schema.runnable import RunnablePassthrough` | `from langchain_core.runnables import RunnablePassthrough` |
| **Messages** | `from langchain.schema import HumanMessage` | `from langchain_core.messages import HumanMessage` |

## Package Organization in v0.2+

```
langchain/                      # Core abstractions
├── langchain-core/             # Core interfaces
├── langchain-community/        # Integrations & implementations
├── langchain-text-splitters/   # Text splitting utilities
├── langchain-ollama/           # Ollama integration
├── langchain-google-genai/     # Google Gemini integration
└── ... other integrations
```

## Installation Command

```bash
pip install langchain-community langchain-core langchain-text-splitters langchain-ollama
```

## Your Fixed Code

```python
# ✅ NOW CORRECT:
from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# Load the document
loader = PyPDFLoader("/Users/gurparkashsingh/Darbar Sahib Library RAG/documents/sample.pdf")
documents = loader.load()

# Split the document into chunks
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=30, separator="\n")
docs = text_splitter.split_documents(documents=documents)

# Load embedding model
embedding_model_name = "sentence-transformers/all-mpnet-base-v2"
model_kwargs = {"device": "cuda"}
embeddings = HuggingFaceEmbeddings(
    model_name=embedding_model_name,
    model_kwargs=model_kwargs
)

# Create FAISS vector store
vectorstore = FAISS.from_documents(docs, embeddings)

# Save and reload the vector store
vectorstore.save_local("faiss_index_")
persisted_vectorstore = FAISS.load_local("faiss_index_", embeddings, allow_dangerous_deserialization=True)

# Create a retriever
retriever = persisted_vectorstore.as_retriever()
```

This should now work without any import errors! ✅

