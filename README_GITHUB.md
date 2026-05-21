# 📚 Sikh Religious Texts RAG

A modern **Retrieval-Augmented Generation (RAG)** application for querying Sikh religious texts using local AI models. Built with LangChain, Ollama, and Streamlit for a beautiful web interface.

## 🌟 Features

- 📖 **PDF Document Loading** - Load and process Sikh religious texts
- 🧠 **Local AI Models** - Uses Ollama with Gemma 4 31B for privacy-first processing
- 🔍 **Vector Search** - FAISS-based semantic search for relevant context
- 💬 **Interactive Q&A** - Ask questions about Sikh teachings
- 🎨 **Modern Web UI** - Clean, responsive Streamlit interface
- ⚙️ **Configurable** - Customize models, chunk sizes, and retrieval parameters
- 🔗 **Network Accessible** - Share with others on your network

## 📋 Prerequisites

- Python 3.12+
- [Ollama](https://ollama.ai) installed and running
- Virtual environment (venv, conda, etc.)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/sikh-rag.git
cd sikh-rag
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Start Ollama Server
```bash
ollama serve
```

### 5. Pull Required Models (in another terminal)
```bash
ollama pull gemma4:31b-cloud
ollama pull nomic-embed-text
```

### 6. Run the Application
```bash
streamlit run streamlit_app.py
```

The app will open at `http://localhost:8501`

## 🌐 Network Access

To allow others on your network to access the app:

```bash
streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

Find your IP address:
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

Share the link: `http://<your-ip>:8501`

## 📁 Project Structure

```
sikh-rag/
├── streamlit_app.py          # Main web application
├── app.py                    # Terminal-based RAG interface
├── rag.py                    # Core RAG class
├── requirements.txt          # Python dependencies
├── .gitignore               # Git ignore rules
├── docs/                    # Documentation
│   ├── architecture.md
│   ├── setup.md
│   └── rag_pipeline.md
└── README.md                # This file
```

## 🔧 Configuration

Edit `streamlit_app.py` to customize:

- **PDF Path** - Point to your Sikh religious texts
- **Chunk Size** - Document chunk size (default: 1000)
- **Chunk Overlap** - Overlap between chunks (default: 30)
- **LLM Model** - Choose between Gemma 4 31B, Llama 3.1, etc.
- **Embedding Model** - Nomic-embed-text for local embeddings

## 💻 Usage

1. Click **"Initialize RAG Pipeline"** to load and process your PDF
2. Type your question in the search box
3. Click **"Search"** to get answers grounded in the document
4. View source documents in the expandable section

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **LLM Framework** | LangChain v0.2+ |
| **Local LLM** | Ollama (Gemma 4 31B) |
| **Embeddings** | Nomic-embed-text |
| **Vector Store** | FAISS |
| **Web Framework** | Streamlit |
| **PDF Processing** | PyPDF |
| **Language** | Python 3.12+ |

## 📚 How It Works

1. **Document Loading** - PDFs are loaded and parsed
2. **Text Chunking** - Documents split into overlapping chunks
3. **Embedding** - Each chunk converted to vector embeddings locally
4. **Vector Storage** - Embeddings stored in FAISS for fast retrieval
5. **Retrieval** - User query converted to embedding and matched against stored chunks
6. **Context Generation** - Top-K relevant chunks combined as context
7. **LLM Response** - Context sent to Gemma 4 31B for answer generation

## 🔐 Privacy & Security

- ✅ All processing happens locally
- ✅ No data sent to external APIs (unless using cloud models)
- ✅ Models run on your machine
- ✅ Network access is controlled by firewall

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📖 Documentation

See the `docs/` folder for detailed documentation:

- **architecture.md** - System design and components
- **setup.md** - Installation and setup guide
- **rag_pipeline.md** - Detailed RAG pipeline explanation

## 🆘 Troubleshooting

### Ollama Connection Error
- Ensure `ollama serve` is running in another terminal
- Check Ollama is listening on `127.0.0.1:11434`

### Model Not Found Error
- Pull the model: `ollama pull gemma4:31b-cloud`
- Pull embeddings: `ollama pull nomic-embed-text`

### FAISS Installation Issues
```bash
pip install faiss-cpu
# or for GPU support
pip install faiss-gpu
```

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- LangChain for RAG framework
- Ollama for local LLM hosting
- Streamlit for web UI
- FAISS by Meta AI Research

## 📞 Support

For issues and questions:
- Open a GitHub Issue
- Check existing documentation in `docs/` folder
- Review troubleshooting guide

---

Made with ❤️ for exploring Sikh religious texts using AI
