# Deployment Guide & Production Readiness Checklist
## FarmAI – Agricultural Decision Intelligence System
**Version:** 1.0 | **Date:** 2026-11-04

---

## 1. Local Development Setup

```bash
# Step 1: Clone repository
git clone https://github.com/vignesh2396/farmai_IBMBob.git
cd farmai_IBMBob

# Step 2: Create virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate

# Step 3: Install dependencies
pip install -r requirements.txt

# Step 4: Configure environment
cp .env.example .env
# Edit .env and add: GOOGLE_API_KEY=your_key_here

# Step 5: Initialize knowledge base (first run only)
python -m rag.embeddings

# Step 6: Run application
streamlit run app.py
# Opens at: http://localhost:8501
```

---

## 2. GitHub Repository Setup

### Initial Push
```bash
cd farmai_ibmbob

# Initialize git
git init
git branch -M main

# Stage all files
git add .
git status  # Verify .env is NOT staged

# First commit
git commit -m "feat: FarmAI MVP - initial commit

- 6 specialized AI agents (Farm Profile, Soil, Weather, Crops, Plan, Advisory)
- RAG pipeline with ChromaDB and agricultural knowledge base
- Streamlit UI with Human-in-the-Loop review workflow
- Full SDLC documentation (BRD, FRD, Architecture, API, Security)
- 9 test scenarios with 100% pass rate
- IBM SkillsBuild Agentic AI Capstone 2026"

# Add remote
git remote add origin https://github.com/vignesh2396/farmai_IBMBob.git

# Push
git push -u origin main
```

### Tagging Releases
```bash
# Tag MVP release
git tag -a v1.0.0 -m "FarmAI MVP release - all 6 agents operational"
git push origin v1.0.0

# Future releases
git tag -a v1.1.0 -m "Bug fixes and UI improvements"
git push origin v1.1.0
```

### Branch Strategy
```bash
# Feature development
git checkout -b feature/multi-language-support
# ... develop feature ...
git push origin feature/multi-language-support
# Create PR on GitHub → Merge to main

# Bug fixes
git checkout -b bugfix/weather-cache-ttl
git push origin bugfix/weather-cache-ttl
```

---

## 3. Streamlit Community Cloud Deployment

### Prerequisites
- GitHub repository is public (or Streamlit Cloud has access)
- GOOGLE_API_KEY is ready

### Steps
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Select repository: `vignesh2396/farmai_IBMBob`
4. Branch: `main`
5. Main file path: `app.py`
6. Click "Advanced settings" → Add secrets:
   ```
   GOOGLE_API_KEY = "your_actual_api_key"
   ```
7. Click "Deploy"
8. URL will be: `farmai-ibmbob.streamlit.app`

**Note:** Streamlit Cloud automatically re-deploys on every push to `main`.

---

## 4. Docker Deployment (Optional)

### Dockerfile
```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p data

# Initialize knowledge base
RUN python -m rag.embeddings

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run app
CMD ["streamlit", "run", "app.py", \
     "--server.address=0.0.0.0", \
     "--server.port=8501", \
     "--server.headless=true"]
```

### Build and Run
```bash
docker build -t farmai:1.0.0 .
docker run -p 8501:8501 -e GOOGLE_API_KEY=your_key farmai:1.0.0
```

---

## 5. Production Readiness Checklist

### Security ✅
- [ ] `GOOGLE_API_KEY` in environment variable, not in code
- [ ] `.env` file confirmed in `.gitignore`
- [ ] No secrets in commit history (`git log --all` verified)
- [ ] `pip-audit -r requirements.txt` run — no critical CVEs
- [ ] Prompt injection defenses verified (TC-09)
- [ ] RBAC implemented (Farmer / Officer roles)

### Reliability ✅
- [ ] Retry logic in all external API calls (3 attempts, exponential backoff)
- [ ] Weather API fallback (cache → default message)
- [ ] LLM fallback (mock plan generator when LLM unavailable)
- [ ] ChromaDB auto-rebuild on first run
- [ ] SQLite WAL mode enabled

### Functionality ✅
- [ ] All 6 agents operational
- [ ] RAG pipeline built and queryable
- [ ] Weather API returns live data
- [ ] Crop ranking returns ≥5 crops
- [ ] Farm plan generated for at least one crop
- [ ] Advisory Q&A returns grounded answers
- [ ] HITL flag triggers on pesticide mention

### Testing ✅
- [ ] `pytest tests/ -v` — all tests pass
- [ ] 9 test scenarios manually validated
- [ ] Performance: Full workflow < 60 seconds
- [ ] Prompt injection test passed

### Documentation ✅
- [ ] README.md complete with installation steps
- [ ] .env.example with all variables
- [ ] Architecture diagram saved to assets/
- [ ] Test cases documented in tests/test_cases.md

### Deployment ✅
- [ ] requirements.txt locked with exact versions
- [ ] Git repository initialized with all files
- [ ] .env NOT committed (only .env.example)
- [ ] v1.0.0 tag created
- [ ] README badges updated with correct GitHub URL

---

## 6. Release Checklist (v1.0.0)

- [ ] All unit tests passing
- [ ] All 9 integration test scenarios validated
- [ ] README reviewed for accuracy
- [ ] Screenshots captured and saved
- [ ] Architecture diagram added to assets/
- [ ] Changelog written (or commit log is sufficient)
- [ ] `git tag v1.0.0` created and pushed
- [ ] Streamlit Cloud deployment verified
- [ ] Demo video generated (farmai_demo.mp4)
- [ ] PPT presentation finalized
- [ ] Submission package complete

---

## 7. Git Commands Summary

```bash
# Clone
git clone https://github.com/vignesh2396/farmai_IBMBob.git

# Check status
git status

# Stage and commit
git add .
git commit -m "type: description"

# Push
git push origin main

# Create and push tag
git tag -a v1.0.0 -m "MVP release"
git push origin v1.0.0

# View history
git log --oneline --graph

# Create feature branch
git checkout -b feature/name

# Merge via PR (GitHub)
# After review: "Squash and merge" on GitHub
```

---

## 8. Environment Variables Reference for Deployment

| Platform | Method | Command / Step |
|---|---|---|
| Local | .env file | `cp .env.example .env` then edit |
| Streamlit Cloud | App secrets | Settings → Secrets → Add TOML format |
| GitHub Actions | Repository secrets | Settings → Secrets → Actions |
| Docker | -e flag | `docker run -e GOOGLE_API_KEY=xxx` |
| Docker Compose | environment section | `environment: - GOOGLE_API_KEY=${GOOGLE_API_KEY}` |
