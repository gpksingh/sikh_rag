# Deploying to GitHub

Follow these steps to deploy the Sikh RAG application to GitHub:

## 1. Create GitHub Repository

1. Go to [GitHub](https://github.com/new)
2. Create a new repository named `sikh-rag` (or your preferred name)
3. **Do NOT** initialize with README, .gitignore, or license (we have these)

## 2. Initialize Git Locally

```bash
cd "/Users/gurparkashsingh/Darbar Sahib Library RAG"
git init
git config user.name "Gurparkash Singh"
git config user.email "singh94803@gmail.com"
```

## 3. Add Files to Git

```bash
git add .
git status  # Review files being committed
```

**Excluded files (via .gitignore):**
- ✅ `venv/` - Virtual environment
- ✅ `faiss_index_/` - Generated vector store
- ✅ `.env` - Environment variables
- ✅ `__pycache__/` - Python cache
- ✅ `.vscode/` - IDE settings

**Included files:**
- ✅ `streamlit_app.py` - Main app
- ✅ `rag.py` - Core RAG module
- ✅ `requirements.txt` - Dependencies
- ✅ `README.md` - Documentation
- ✅ `docs/` - Additional docs
- ✅ `LICENSE` - MIT License

## 4. Create Initial Commit

```bash
git commit -m "Initial commit: Sikh RAG application with Streamlit UI"
```

## 5. Add Remote Repository

Replace `gpksingh` and `Sikh Rag`:

```bash
git branch -M main
git remote add origin https://github.com/gpksingh/Sikh_Rag.git
```

## 6. Push to GitHub

```bash
git push -u origin main
```

## 7. Verify on GitHub

Visit `https://github.com/gpksingh/Sikh_Rag` and confirm all files are there!

## 📋 Files Structure on GitHub

```
sikh-rag/
├── streamlit_app.py           # Main Streamlit app
├── app.py                     # Terminal interface
├── rag.py                     # Core RAG class
├── requirements.txt           # Python dependencies
├── .gitignore                # Git ignore rules
├── LICENSE                   # MIT License
├── README_GITHUB.md          # Comprehensive guide
├── SETUP.md                  # Setup instructions
├── docs/                     # Documentation folder
│   ├── architecture.md
│   ├── setup.md
│   └── rag_pipeline.md
└── README.md                 # Old readme (optional)
```

## 🔄 Future Updates

To push new changes:

```bash
git add .
git commit -m "Describe your changes"
git push origin main
```

## 🎯 Next Steps

1. **Add GitHub Actions** - CI/CD pipeline
2. **Add GitHub Pages** - Project website
3. **Deploy** - Consider Streamlit Cloud, Heroku, or AWS

## 💡 Tips

- Add meaningful commit messages
- Create branches for new features (`git checkout -b feature/xyz`)
- Create releases for stable versions
- Add GitHub badges to README

## 📞 Support

If you have questions about GitHub deployment, refer to:
- [GitHub Docs](https://docs.github.com)
- [Git Tutorial](https://git-scm.com/book/en/v2)

---

**Ready to deploy? Run the git commands above! 🚀**
