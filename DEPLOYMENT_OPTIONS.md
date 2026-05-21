# 🚀 Deployment Guide for Sikh RAG

Your application is ready to deploy! Here are the best options:

## Option 1: Streamlit Cloud (RECOMMENDED - Easiest)

### Steps:

1. **Sign up at Streamlit Cloud**
   - Go to https://streamlit.io/cloud
   - Sign in with your GitHub account

2. **Deploy Your App**
   - Click "New app"
   - Select repository: `gpksingh/Sikh_Rag`
   - Select main branch
   - Set main file path: `streamlit_app.py`
   - Click "Deploy"

3. **Configure Secrets**
   - In the app settings, add any environment variables needed
   - (No special secrets needed for this app)

4. **Access Your App**
   - Your app will be live at: `https://<your-app-name>.streamlit.app`
   - Share the link with anyone!

**Pros:**
- ✅ Free tier available
- ✅ No server management
- ✅ Automatic updates from GitHub
- ✅ Built-in scaling

**Cons:**
- ⚠️ Requires Ollama running somewhere accessible (needs server backend)

---

## Option 2: Docker + AWS/Google Cloud (Better for Production)

### Create Dockerfile:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY streamlit_app.py .
COPY rag.py .
COPY docs/ ./docs/
COPY *.pdf ./

# Expose port
EXPOSE 8501

# Run app
CMD ["streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0"]
```

### Deploy to AWS:
```bash
# Using AWS Elastic Beanstalk
eb init -p docker sikh-rag
eb create production
eb deploy
```

---

## Option 3: Heroku (Simple & Free Alternative)

### Steps:

1. **Install Heroku CLI**
   ```bash
   brew tap heroku/brew && brew install heroku
   heroku login
   ```

2. **Create Procfile**
   ```
   web: streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0
   ```

3. **Deploy**
   ```bash
   heroku create your-app-name
   git push heroku main
   ```

---

## Option 4: PythonAnywhere (Beginner Friendly)

1. Go to https://www.pythonanywhere.com
2. Sign up for free account
3. Upload your files
4. Configure web app to run Streamlit
5. Get a public URL

---

## 🎯 QUICK START: Streamlit Cloud (Recommended)

**This is the easiest for your use case:**

1. Go to https://streamlit.io/cloud
2. Click "New app"
3. Connect your GitHub account
4. Select: `gpksingh/Sikh_Rag`
5. Set file to: `streamlit_app.py`
6. Click Deploy!

⏱️ **Takes ~5 minutes**

**Important:** You'll need to host Ollama separately (AWS EC2, Google Cloud, etc.) for the app to work since it needs to call your Ollama server.

---

## 🔧 Ollama Backend Setup (Required for Any Deployment)

Since your app uses Ollama, you have two options:

### Option A: Local Ollama (Network Only)
- Keep Ollama running on your machine
- Update `streamlit_app.py` to point to your machine's IP
- Only works while your machine is on

### Option B: Deploy Ollama to Cloud Server (Recommended)

1. **Rent a server** (AWS EC2, DigitalOcean, Linode, etc.)
   - Recommended: t3.xlarge or similar
   - Ubuntu 22.04
   - Budget: ~$20-50/month

2. **Install Ollama on server**
   ```bash
   curl https://ollama.ai/install.sh | sh
   ollama serve
   ```

3. **Pull models**
   ```bash
   ollama pull gemma4:31b-cloud
   ollama pull nomic-embed-text
   ```

4. **Update your app** to point to server Ollama:
   ```python
   # In streamlit_app.py
   ollama_host = "http://your-server-ip:11434"
   embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url=ollama_host)
   llm = Ollama(model="gemma4:31b-cloud", base_url=ollama_host)
   ```

---

## 📊 Deployment Comparison

| Option | Cost | Setup Time | Ease | Best For |
|--------|------|-----------|------|----------|
| **Streamlit Cloud** | Free | 5 min | ⭐⭐⭐⭐⭐ | **Quick Demo** |
| **Docker + AWS** | $10-50/mo | 30 min | ⭐⭐⭐ | Production |
| **Heroku** | Free/Paid | 10 min | ⭐⭐⭐⭐ | Learning |
| **PythonAnywhere** | Free/Paid | 15 min | ⭐⭐⭐⭐ | Beginners |

---

## ✅ Pre-Deployment Checklist

- [ ] Code committed to GitHub
- [ ] All tests passing locally
- [ ] requirements.txt updated
- [ ] README.md complete
- [ ] .gitignore configured properly
- [ ] No sensitive data in code
- [ ] Ollama backend plan decided

---

## 🎯 My Recommendation

**For immediate deployment:**
1. Deploy to **Streamlit Cloud** (free, easy)
2. Keep Ollama running on your local machine
3. Share the Streamlit Cloud link with others on your network

**For production:**
1. Deploy **Streamlit to Streamlit Cloud**
2. Deploy **Ollama to AWS EC2 or DigitalOcean**
3. Update app to point to cloud Ollama
4. Scale as needed

---

## 📞 Next Steps

1. Choose a deployment option above
2. Follow the steps for that option
3. Test the deployment
4. Share your live app URL!

---

**Need help? The Streamlit Cloud option is recommended - it takes just 5 minutes! 🚀**
