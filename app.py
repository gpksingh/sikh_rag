from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate

# Load the document
loader = PyPDFLoader("/Users/gurparkashsingh/Darbar Sahib Library RAG/a-brief-introduction-to-sikhism-gurbachan-singh-sidhu.pdf")
documents = loader.load()

# Split the document into chunks
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=30, separator="\n")
docs = text_splitter.split_documents(documents=documents)

# Load embedding model
print("Loading embedding model...")
embeddings = OllamaEmbeddings(model="nomic-embed-text")

# Test embedding model
print("Testing embedding model...")
try:
    test_embedding = embeddings.embed_query("test")
    print(f"✓ Embedding model works! Vector size: {len(test_embedding)}")
except Exception as e:
    print(f"❌ Embedding model error: {e}")
    print("Make sure to pull the embedding model:")
    print("  ollama pull nomic-embed-text")
    import sys
    sys.exit(1)

# Create FAISS vector store
print(f"Creating FAISS vector store with {len(docs)} documents...")
try:
    vectorstore = FAISS.from_documents(docs, embeddings)
    print("✓ Vector store created successfully")
except Exception as e:
    print(f"❌ Error creating vector store: {e}")
    import sys
    sys.exit(1)

# Save and reload the vector store
vectorstore.save_local("faiss_index_")
persisted_vectorstore = FAISS.load_local("faiss_index_", embeddings, allow_dangerous_deserialization=True)

# Create a retriever
retriever = persisted_vectorstore.as_retriever()

# Initialize the LLM model
llm = Ollama(model="llama3.1")

# Interactive query loop
print("\n" + "="*50)
print("RAG Query Interface")
print("="*50)

while True:
    query = input("\nType your query (or type 'exit' to quit): ")
    if query.lower() == "exit":
        break
    
    # Retrieve relevant documents
    docs = retriever.invoke(query)
    
    # Combine context from retrieved documents
    context = "\n".join([doc.page_content for doc in docs])
    
    # Create prompt with context
    prompt_text = f"""Based on the following context about Sikhism, answer the question.

Context:
{context}

Question: {query}

Answer:"""
    
    # Get response from LLM
    response = llm.invoke(prompt_text)
    print(f"\nAnswer: {response}")
    print("-"*50)