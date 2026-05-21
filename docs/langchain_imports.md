# LangChain v0.2+ Import Reference Guide

## Problem
LangChain reorganized its code in v0.2+. Old imports no longer work, causing `ModuleNotFoundError`.

## Solution: Correct Import Paths

### 📄 Document Loaders

```python
# ✅ CORRECT (v0.2+)
from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import DirectoryLoader

# ❌ WRONG (Old syntax)
from langchain.document_loaders import PyPDFLoader
from langchain.document_loaders import TextLoader
```

**Usage:**
```python
loader = PyPDFLoader("document.pdf")
documents = loader.load()
```

---

### ✂️ Text Splitters

```python
# ✅ CORRECT (v0.2+)
from langchain_text_splitters import CharacterTextSplitter
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_text_splitters import TokenTextSplitter

# ❌ WRONG (Old syntax)
from langchain.text_splitter import CharacterTextSplitter
```

**Usage:**
```python
splitter = CharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separator="\n"
)
docs = splitter.split_documents(documents)
```

---

### 🧠 Embeddings

```python
# ✅ CORRECT (v0.2+)
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.embeddings import SentenceTransformerEmbeddings
from sentence_transformers import SentenceTransformer  # Direct usage

# ❌ WRONG (Old syntax)
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.embeddings import OllamaEmbeddings
```

**Usage:**
```python
# Option 1: HuggingFace
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-mpnet-base-v2",
    model_kwargs={"device": "cuda"}
)

# Option 2: Ollama (Recommended for local)
from langchain_ollama import OllamaEmbeddings
embeddings = OllamaEmbeddings(model="nomic-embed-text")

# Option 3: Direct SentenceTransformer
model = SentenceTransformer("all-mpnet-base-v2")
embeddings_array = model.encode("text here")
```

---

### 📦 Vector Stores

```python
# ✅ CORRECT (v0.2+)
from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores import Chroma
from langchain_community.vectorstores import Pinecone
from langchain_community.vectorstores import Weaviate

# ❌ WRONG (Old syntax)
from langchain.vectorstores import FAISS
```

**Usage:**
```python
# Create vector store
vectorstore = FAISS.from_documents(docs, embeddings)

# Save locally
vectorstore.save_local("faiss_index")

# Load from local
vectorstore = FAISS.load_local(
    "faiss_index",
    embeddings,
    allow_dangerous_deserialization=True
)

# Create retriever
retriever = vectorstore.as_retriever()
```

---

### 🤖 Language Models (LLMs)

```python
# ✅ CORRECT (v0.2+)
from langchain_ollama import OllamaLLM
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.llms import Ollama
from langchain_community.llms import LlamaCpp

# ❌ WRONG (Old syntax)
from langchain.llms import OpenAI
from langchain.llms.ollama import Ollama
```

**Usage:**
```python
# Ollama (Local)
llm = OllamaLLM(model="gemma4:31b-cloud")

# Google Gemini (Cloud)
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    api_key="your_api_key"
)
```

---

### 💬 Prompts

```python
# ✅ CORRECT (v0.2+)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import HumanMessagePromptTemplate
from langchain_core.prompts import SystemMessagePromptTemplate

# ❌ WRONG (Old syntax)
from langchain.prompts import ChatPromptTemplate
from langchain.prompts import PromptTemplate
```

**Usage:**
```python
prompt = ChatPromptTemplate.from_template(
    """Answer the question based on context.
    
Context: {context}
Question: {question}
Answer:"""
)
```

---

### ⛓️ Chains & Runnables

```python
# ✅ CORRECT (v0.2+)
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables import RunnableLambda
from langchain_core.chains import LLMChain  # If needed

# ❌ WRONG (Old syntax)
from langchain.schema.runnable import RunnablePassthrough
from langchain.chains import LLMChain
```

**Usage:**
```python
chain = (
    {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
    | prompt
    | llm
)

result = chain.invoke({"context": context_text, "question": question})
```

---

### 📨 Messages & Outputs

```python
# ✅ CORRECT (v0.2+)
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser

# ❌ WRONG (Old syntax)
from langchain.schema import HumanMessage, AIMessage
```

---

## Complete Working Example

```python
# Correct imports for RAG pipeline
from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

# 1. Load documents
loader = PyPDFLoader("document.pdf")
documents = loader.load()

# 2. Split into chunks
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
docs = splitter.split_documents(documents)

# 3. Create embeddings
embeddings = OllamaEmbeddings(model="nomic-embed-text")

# 4. Create vector store
vectorstore = FAISS.from_documents(docs, embeddings)
retriever = vectorstore.as_retriever()

# 5. Create LLM
llm = OllamaLLM(model="gemma4:31b-cloud")

# 6. Create chain
prompt = ChatPromptTemplate.from_template(
    "Context: {context}\n\nQuestion: {question}\n\nAnswer:"
)

chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
)

# 7. Query
result = chain.invoke("What is the document about?")
print(result)
```

---

## Migration Checklist

Before running your code:

- [ ] Update all imports to use `langchain_community`, `langchain_core`, `langchain_ollama` etc.
- [ ] Remove any imports from old `langchain.*` format
- [ ] Install correct packages: `pip install langchain-community langchain-core langchain-ollama langchain-text-splitters`
- [ ] Update any custom code that referenced old import paths
- [ ] Test each component individually

---

## Package Installation

```bash
# Core packages
pip install langchain langchain-core langchain-community

# Specialized packages
pip install langchain-text-splitters    # Text splitting
pip install langchain-ollama           # Ollama integration
pip install langchain-google-genai     # Google Gemini

# Supporting packages
pip install faiss-cpu                   # Vector store
pip install sentence-transformers      # Embeddings
pip install pypdf                       # PDF loading
pip install python-dotenv              # Environment variables
```

---

## Common Errors & Fixes

### Error: `ModuleNotFoundError: No module named 'langchain.document_loaders'`

**Fix:**
```python
# Wrong
from langchain.document_loaders import PyPDFLoader

# Correct
from langchain_community.document_loaders.pdf import PyPDFLoader
```

### Error: `ModuleNotFoundError: No module named 'langchain.vectorstores'`

**Fix:**
```python
# Wrong
from langchain.vectorstores import FAISS

# Correct
from langchain_community.vectorstores import FAISS
```

### Error: `ModuleNotFoundError: No module named 'langchain.text_splitter'`

**Fix:**
```python
# Wrong
from langchain.text_splitter import CharacterTextSplitter

# Correct
from langchain_text_splitters import CharacterTextSplitter
```

---

## References

- [LangChain Migration Guide](https://python.langchain.com/docs/get_started/introduction)
- [LangChain Documentation](https://python.langchain.com)
- [LangChain Community Docs](https://python.langchain.com/docs/integrations/providers)
- [LangChain GitHub](https://github.com/langchain-ai/langchain)

