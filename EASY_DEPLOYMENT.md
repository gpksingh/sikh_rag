# 🚀 Easy Deployment Guide

Your app is now ready for easy deployment! Follow one of these paths:

---

## ⚠️ IMPORTANT: Ollama Connectivity

**Streamlit Cloud cannot access your local Ollama server.** Choose one:

1. **Option 1 (Recommended):** Use DigitalOcean Droplet + Docker (everything in cloud)
2. **Option 2:** Use cloud-hosted LLM (OpenAI, Anthropic, Groq, etc.)
3. **Option 3:** Deploy to your own server with Ollama

---

## 🟢 BEST: DigitalOcean Droplet + Docker (All in cloud, $5-12/month)

**Time: 30 minutes | Cost: $5-12/month (one server for everything)**

### Why This Works
✅ Ollama runs on DigitalOcean server  
✅ Streamlit app connects to it  
✅ App is always accessible  
✅ Everything in one place  

### Step 1: Create DigitalOcean Account
1. Go to https://www.digitalocean.com
2. Sign up (get $200 free credits)
3. Verify email

### Step 2: Create Droplet
1. DigitalOcean → Droplets → Create Droplet
2. Choose: **Ubuntu 22.04**
3. Basic plan: **$6/month (1GB RAM)**
4. Create

### Step 3: SSH into Droplet
```bash
ssh root@YOUR_DROPLET_IP
```

### Step 4: Install Docker
```bash
apt update && apt upgrade -y
apt install -y docker.io git

# Add user to docker group
usermod -aG docker root
```

### Step 5: Clone Your Repo
```bash
cd /root
git clone https://github.com/gpksingh/sikh_rag.git
cd sikh_rag
```

### Step 6: Create docker-compose.yml
Create file: `docker-compose.yml`
```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0:11434
    command: serve

  streamlit:
    build: .
    ports:
      - "8501:8501"
    environment:
      - OLLAMA_HOST=http://ollama:11434
    depends_on:
      - ollama

volumes:
  ollama_data:
```

### Step 7: Create Dockerfile
Create file: `Dockerfile`
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY streamlit_app.py .
COPY *.pdf ./
COPY docs/ ./docs/ 2>/dev/null || true

# Expose port
EXPOSE 8501

# Run app
CMD ["streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
```

### Step 8: Build and Deploy
```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Pull models (wait 2-3 minutes for Ollama to start)
sleep 30
docker-compose exec ollama ollama pull gemma2:2b
docker-compose exec ollama ollama pull nomic-embed-text
```

### Step 9: Configure Firewall
```bash
# Allow HTTP/HTTPS traffic
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### Step 10: Set Up Domain (Optional)
1. Buy domain (Namecheap, GoDaddy, etc.)
2. Point DNS to DigitalOcean droplet IP
3. Use DigitalOcean's Let's Encrypt integration for HTTPS

### ✅ Your app is live at: `http://YOUR_DROPLET_IP:8501`

---

## 🟡 ALTERNATIVE: Streamlit Cloud + Cloud LLM

**Time: 5 minutes | Cost: Free (Streamlit) + API costs**

If you prefer Streamlit Cloud but want LLM, use an API service:

### Update streamlit_app.py
Replace Ollama with your chosen API:

**Option A: OpenAI**
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4", api_key=st.secrets["OPENAI_API_KEY"])
```

**Option B: Anthropic (Claude)**
```python
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(model="claude-3-sonnet", api_key=st.secrets["ANTHROPIC_API_KEY"])
```

**Option C: Groq (Fast, Free tier available)**
```python
from langchain_groq import ChatGroq

llm = ChatGroq(model="mixtral-8x7b-32768", api_key=st.secrets["GROQ_API_KEY"])
```

### Deploy to Streamlit Cloud
1. Go to https://streamlit.io/cloud
2. Click "New app"
3. Select your GitHub repo
4. Select branch and main file
5. Add secrets (API keys)
6. Deploy!

---

## 🔴 NOT RECOMMENDED: Local Only

**Only for development - not accessible to others**

```bash
cd "/Users/gurparkashsingh/Darbar Sahib Library RAG"
source venv/bin/activate
streamlit run streamlit_app.py
```

---

## 📊 Comparison

| Option | Cost | Setup | Model Type | Recommendation |
|--------|------|-------|-----------|-----------------|
| **DO Droplet + Docker** | $6-12/mo | 30 min | Local LLM (Ollama) | 🟢 **BEST** |
| **Streamlit + OpenAI** | Free + $0.03/request | 5 min | Cloud API | 🟡 Good |
| **Streamlit + Groq** | Free + free tier | 5 min | Cloud API | 🟡 Good |
| **Local Only** | Free | 5 min | Local LLM | 🔴 Dev only |

---

## ✅ Quick Decision Tree

```
Does your Mac need to stay on? 
  → YES: Use DigitalOcean Droplet
  → NO: Use Streamlit + Cloud LLM

Do you want to pay for LLM? 
  → NO: Use DigitalOcean Droplet (free Ollama)
  → YES: Use Streamlit + OpenAI/Anthropic

Need something running NOW? 
  → YES: Streamlit + Groq (free tier)
  → NO: DigitalOcean (better long-term)
```

---

## 🔗 Useful Links

- **DigitalOcean Droplets:** https://www.digitalocean.com/products/droplets
- **Streamlit Cloud:** https://streamlit.io/cloud
- **Ollama:** https://ollama.ai
- **Docker Docs:** https://docs.docker.com
- **OpenAI API:** https://platform.openai.com
- **Groq:** https://console.groq.com
- **Anthropic (Claude):** https://console.anthropic.com

---

## ✅ Deployment Checklist

For **DigitalOcean Droplet + Docker**:
- [ ] Created DigitalOcean account
- [ ] Created Ubuntu 22.04 droplet
- [ ] Installed Docker
- [ ] Cloned GitHub repo
- [ ] Created docker-compose.yml
- [ ] Created Dockerfile
- [ ] Built and started containers
- [ ] Pulled Ollama models
- [ ] App accessible at droplet IP:8501
- [ ] (Optional) Set up domain name

For **Streamlit Cloud + Cloud LLM**:
- [ ] Updated streamlit_app.py to use cloud LLM
- [ ] Added API keys to secrets
- [ ] Connected GitHub repo to Streamlit Cloud
- [ ] App deployed and live
- [ ] Tested with sample queries

---

## 🚀 Recommended Path

1. **Fastest:** Streamlit Cloud + Groq (5 min, free tier available)
2. **Best:** DigitalOcean Droplet + Docker (30 min, $6/month, no API costs)
3. **Reliable:** Streamlit Cloud + OpenAI (5 min, pay per use)

**Start with Streamlit + Groq today!** ✨
