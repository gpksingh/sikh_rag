# 🚀 Easy Deployment Guide

Your app is now ready for easy deployment! Follow one of these paths:

---

## 🟢 EASIEST: DigitalOcean App Platform + Local Ollama

**Time: 15 minutes | Cost: Free trial or $12/month**

### Step 1: Create DigitalOcean Account
1. Go to https://www.digitalocean.com
2. Sign up (get $200 free credits)
3. Verify email

### Step 2: Deploy Streamlit App
1. In DigitalOcean dashboard, click **"App Platform"**
2. Click **"Create App"**
3. Choose **GitHub**
4. Connect your GitHub account
5. Select repository: `gpksingh/Sikh_Rag`
6. Branch: `main`
7. Click **"Configure"**
8. Set Main File: `streamlit_app.py`
9. Click **"Create Resource"**
10. Set **Environment Variable:**
    - Name: `OLLAMA_HOST`
    - Value: `http://YOUR_LOCAL_IP:11434`
11. Click **"Deploy"**

### Step 3: Get Your Local IP
On your Mac, run:
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```
Use that IP in the environment variable (e.g., `http://192.168.1.100:11434`)

### Step 4: Keep Ollama Running
```bash
# On your Mac, keep this running
ollama serve
```

### ✅ Your app is live at: `https://<app-name>.ondigitalocean.app`

---

## 🟡 BETTER: DigitalOcean Droplet + Docker (All in cloud)

**Time: 30 minutes | Cost: $5-12/month (one server for everything)**

### Step 1: Create Droplet
1. DigitalOcean → Droplets → Create Droplet
2. Choose: **Ubuntu 22.04**
3. Basic plan: **$6/month (1GB RAM)**
4. Create

### Step 2: SSH into Droplet
```bash
ssh root@YOUR_DROPLET_IP
```

### Step 3: Install Docker
```bash
apt update && apt upgrade -y
apt install -y docker.io git

# Add user to docker group
usermod -aG docker root
```

### Step 4: Clone Your Repo
```bash
cd /root
git clone https://github.com/gpksingh/Sikh_Rag.git
cd Sikh_Rag
```

### Step 5: Create Dockerfile
Create file: `Dockerfile`
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
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
CMD ["streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"]
```

### Step 6: Build and Run
```bash
# Build Docker image
docker build -t sikh-rag .

# Run container with Ollama on same server
docker run -d \
  --name sikh-rag-app \
  -p 8501:8501 \
  -e OLLAMA_HOST="http://localhost:11434" \
  sikh-rag
```

### Step 7: Install Ollama on Droplet
```bash
# In another terminal, SSH in again
curl https://ollama.ai/install.sh | sh

# Start Ollama in background
ollama serve &

# Pull models
ollama pull gemma4:31b-cloud
ollama pull nomic-embed-text
```

### ✅ Your app is live at: `http://YOUR_DROPLET_IP:8501`

---

## 🔴 NOT RECOMMENDED: Local Deployment Only

**Only for development/testing - not public**

```bash
cd "/Users/gurparkashsingh/Darbar Sahib Library RAG"
source venv/bin/activate
streamlit run streamlit_app.py --server.address 0.0.0.0
```

---

## 📊 Comparison

| Option | Cost | Setup | Scalability | Recommendation |
|--------|------|-------|-------------|-----------------|
| **Option 1: DO App + Local Ollama** | Free/12$/mo | 15 min | Low | 🟢 **Start here** |
| **Option 2: DO Droplet + Docker** | 5-12$/mo | 30 min | Medium | 🟡 **Best balance** |
| **Option 3: Local Only** | Free | 5 min | None | 🔴 **Dev only** |

---

## 🎯 My Recommendation

**Start with Option 1 (DigitalOcean App + Local Ollama):**
- Easiest to set up (15 min)
- Works immediately
- Can upgrade later
- Free trial available

**Then upgrade to Option 2 if needed:**
- True cloud deployment
- Everything self-contained
- No dependency on local machine
- Professional setup

---

## 🔗 Useful Links

- **DigitalOcean Apps:** https://www.digitalocean.com/products/app-platform
- **DigitalOcean Droplets:** https://www.digitalocean.com/products/droplets
- **Ollama Install:** https://ollama.ai
- **Docker Docs:** https://docs.docker.com

---

## ✅ Checklist

- [ ] Updated `streamlit_app.py` with `OLLAMA_HOST`
- [ ] Code pushed to GitHub
- [ ] Created DigitalOcean account
- [ ] Deployed to App Platform OR Droplet
- [ ] Ollama running somewhere
- [ ] Environment variables configured
- [ ] App is live and working!

---

**Questions? Start with Option 1 - it's the easiest! 🚀**
