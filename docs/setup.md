# Setup

## Install Python packages

pip install langchain langchain-community langchain-google-genai langchain-ollama faiss-cpu pypdf python-dotenv

## Install Ollama

Install Ollama from the official Ollama website.

Then pull models:

ollama pull llama3.2
ollama pull nomic-embed-text

## Environment Variables

Create a .env file:

GEMINI_API_KEY=your_api_key_here
