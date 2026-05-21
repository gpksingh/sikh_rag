# Quick Start Guide

## ⚠️ Before Running app.py

### Step 1: Start Ollama Service

Open a **new terminal** and run:

```bash
ollama serve
```

Keep this terminal open while using the app.

### Step 2: Pull Required Models

In another terminal, run:

```bash
# Pull embedding model (required)
ollama pull nomic-embed-text

# Pull LLM model (required)
ollama pull llama3.1
```

### Step 3: Verify Installation

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Should return a list of models
```

### Step 4: Run the App

```bash
python app.py
```

---

## ✅ Expected Output

```
✅ Ollama is running
Loading embedding model...
Creating vector store from documents...
✓ Documents indexed successfully
Tell me a joke
[Response from LLM...]
```

---

## ❌ Troubleshooting

### "Ollama is not running!"

**Solution:**
```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Run app
python app.py
```

### "model 'nomic-embed-text' not found"

**Solution:**
```bash
ollama pull nomic-embed-text
ollama pull llama3.1
```

### "Connection refused"

- Check if Ollama is running: `ollama serve`
- Check port 11434 is available
- Try: `curl http://localhost:11434/api/tags`

---

## 📋 System Requirements

- Ollama installed and running
- Python 3.8+
- 8GB RAM (minimum)
- Internet for first model pull

---

## 🚀 Next Steps

1. ✅ Start Ollama service
2. ✅ Pull required models
3. ✅ Run `python app.py`
4. ✅ Build your RAG application

