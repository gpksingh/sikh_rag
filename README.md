# Gemini + Ollama RAG App

This app lets a user upload documents, converts the documents into text chunks,
stores them in a vector database, retrieves relevant chunks, and sends them to
Gemini or Ollama to answer questions.

## Tech Stack

- Python
- LangChain
- Gemini API
- Ollama
- FAISS vector database
- PyPDF for PDF loading

## Pipeline

1. Load documents
2. Split documents into chunks
3. Generate embeddings
4. Store embeddings in FAISS
5. Retrieve relevant chunks
6. Send context to Gemini/Ollama
7. Return grounded answer
