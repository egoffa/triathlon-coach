# 🏊 Triathlon Coach AI - Complete Setup Guide

An open-source, self-hosted AI triathlon coaching system that analyzes your Strava training data and provides personalized recommendations using local LLMs. Zero cloud costs, complete privacy.

## ✨ Features

- **🧠 Multi-Agent AI System**: CrewAI-powered coaching, analytics, and planning agents
- **🤖 Local LLM Support**: Run Llama models locally via Ollama (llama2, mistral, neural-chat)
- **📊 Strava Integration**: Pull training data directly from Strava API
- **🎨 Interactive Web UI**: Beautiful Streamlit interface for easy interaction
- **⚡ Fast & Private**: Everything runs locally - no cloud, no subscriptions
- **🐳 Fully Containerized**: Docker + Docker Compose for one-command deployment
- **📈 Real-time Analysis**: Get AI coaching feedback instantly
- **💾 Session Memory**: Redis caching for improved performance

## 🎯 What It Does

### Input
- Connects to your Strava account
- Fetches your recent training activities (swimming, cycling, running)
- Analyzes your workout data

### Processing
- **Coach Agent**: Evaluates discipline balance, recommends training adjustments
- **Analytics Agent**: Identifies patterns and trends in your performance
- **LLM Analysis**: Uses local Ollama to generate personalized insights

### Output
- ✅ Performance analysis
- ✅ Personalized coaching recommendations
- ✅ Training focus areas
- ✅ Suggested next workouts

## 🚀 Quick Start (10 Minutes)

### Prerequisites

- **Docker & Docker Compose** (includes Docker Desktop)
- **Python 3.11+** (with pip/uv)
- **8GB+ RAM** (16GB recommended)
- **10GB+ disk space** (for LLM models)
- **Strava Account** (free or premium)

### Step 1: Download & Setup

```bash
# Clone the project
git clone https://github.com/yourusername/triathlon-coach.git
cd triathlon-coach

# Create folder structure
mkdir -p config logs

# Verify you have these files in root:
# - docker-compose.yml
# - .env
# - streamlit_app.py
# - src/ (folder with all code)
# - requirements.txt
```

### Step 2: Get Strava Credentials

1. Go to: https://www.strava.com/settings/api
2. Create API Application:
   - **Name**: "Triathlon Coach"
   - **Authorization Callback Domain**: `localhost`
3. Note your **Client ID** and **Client Secret**

### Step 3: Get Strava Refresh Token

⚠️ **Important:** The redirect URL must match your Strava settings.

**Authorization URL:**
```
https://www.strava.com/api/v3/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://localhost&scope=read,activity:read&state=mystate
```

**Steps:**
1. Open URL in browser
2. Click "Authorize"
3. Copy `code` from error page URL: `http://localhost/?state=mystate&code=ABC123...`
4. Run curl command (replace values):
   ```bash
   curl -X POST https://www.strava.com/api/v3/oauth/token \
     -d client_id=YOUR_CLIENT_ID \
     -d client_secret=YOUR_CLIENT_SECRET \
     -d code=ABC123 \
     -d grant_type=authorization_code
   ```
5. Copy `refresh_token` from response

### Step 4: Configure .env

```bash
nano .env
```

Update these values:
```env
# Strava (from steps above)
STRAVA_CLIENT_ID=your_client_id
STRAVA_CLIENT_SECRET=your_client_secret
STRAVA_REFRESH_TOKEN=your_refresh_token

# Local development (macOS/Linux)
LOG_FILE=./logs/triathlon_coach.log
OLLAMA_BASE_URL=http://localhost:11434
REDIS_URL=redis://localhost:6379

# Docker deployment
# LOG_FILE=/app/logs/triathlon_coach.log
# OLLAMA_BASE_URL=http://ollama:11434
# REDIS_URL=redis://redis:6379
```

### Step 5: Install Python Dependencies

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install packages
pip install -r requirements.txt
# OR with uv:
uv pip install -r requirements.txt
```

### Step 6: Run Streamlit

```bash
streamlit run streamlit_app.py
```

Opens at: **http://localhost:8501**

Click "Fetch Activities" to get started! 🎉

---

## 🐳 Docker Deployment (Complete System)

For running with Docker containers (includes Ollama, Redis, FastAPI):

### Step 1: Prepare Environment

```bash
# Make sure .env is configured (see above)
nano .env

# Verify config folder exists
mkdir -p config

# Copy model configuration
cp ollama_models.txt config/
```

### Step 2: Start All Services

```bash
docker-compose up --build
```

**First run takes 5-10 minutes** (downloads ~4GB LLM model)

Wait for messages:
```
✓ Ollama service started
✓ Started Ollama service  
✓ Uvicorn running on http://0.0.0.0:8000
```

### Step 3: Run Streamlit (New Terminal)

```bash
streamlit run streamlit_app.py
```

### Services Available

- **Streamlit UI**: http://localhost:8501 (interactive)
- **FastAPI API**: http://localhost:8000 (JSON endpoints)
- **API Docs**: http://localhost:8000/docs (interactive testing)
- **Ollama**: http://localhost:11434 (LLM server)
- **Redis**: localhost:6379 (cache)

---

## 📊 Using Streamlit Interface

### Main Features

**Left Sidebar:**
- **Days to analyze**: How far back to look (1-90 days)
- **Number of activities**: How many activities to fetch (5-50)
- **Analysis type**: Choose Coach Analysis, AI Insights, or Both

**Main Content:**
- **Fetch Activities**: Pull data from Strava
- **Activities Summary**: Total distance, time, activity count
- **Coach Analysis**: Agent-based analysis and recommendations
- **AI Insights**: LLM-generated personalized coaching

### Workflow

1. Click **"Fetch Activities"** → Download from Strava
2. Review **activities list** → See your recent workouts
3. Click **"Analyze with Coach Agent"** → Get coaching insights
4. Click **"Generate AI Insights"** → Get AI recommendations

---

## 🔧 Configuration

### Environment Variables

```env
# Strava
STRAVA_CLIENT_ID          # From strava.com/settings/api
STRAVA_CLIENT_SECRET      # From strava.com/settings/api
STRAVA_REFRESH_TOKEN      # From OAuth flow

# Ollama (Local Development)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2:7b    # Options: llama2:7b, mistral:7b, neural-chat:7b
OLLAMA_TIMEOUT=60

# Redis (Local Development)
REDIS_URL=redis://localhost:6379

# Logging
LOG_FILE=./logs/triathlon_coach.log
LOG_LEVEL=INFO

# API
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development  # or 'production'

# Agents
CREW_AI_VERBOSE=true
CREW_AI_MAX_ITERATIONS=5
```

### Model Selection

Choose the LLM model based on your hardware:

| Model | Size | Speed | Quality | RAM | Best For |
|-------|------|-------|---------|-----|----------|
| `openchat:7b` | 3.8GB | ⚡⚡⚡ | Good | 4GB | CPU-only, limited RAM |
| `llama2:7b` | 4.0GB | ⚡⚡ | Good | 4-6GB | Default, balanced |
| `neural-chat:7b` | 4.7GB | ⚡⚡ | Better | 5-6GB | Better instruction following |
| `mistral:7b` | 4.7GB | ⚡⚡ | Better | 5-6GB | Strong reasoning |
| `llama2:13b` | 7.3GB | ⚡ | Best | 8-10GB | Best quality (requires GPU) |

Change in `.env`:
```env
OLLAMA_MODEL=mistral:7b
```

---

## 🆘 Troubleshooting

### Strava Shows: "activity:read_permission missing"

**Problem:** Refresh token doesn't have activity read permission

**Solution:**
1. Get new refresh token with correct scope
2. Authorization URL must have: `scope=read,activity:read`
3. Update `.env` with new token
4. Run `python strava_diagnostic.py` to verify

See: STRAVA_SIMPLE_AUTH.md

### "Read-only file system: '/app'"

**Problem:** Log file path incorrect for local dev

**Solution:**
```env
# Change in .env:
LOG_FILE=./logs/triathlon_coach.log  # Local dev
# NOT:
LOG_FILE=/app/logs/triathlon_coach.log  # Docker only
```

### Ollama Connection Refused

**Problem:** Ollama service not running

**Solution:**
```bash
# Check if running
docker-compose logs ollama

# Restart
docker-compose restart ollama

# Wait for model download (5-10 min on first run)
```

### Activities Fetch Returns Empty

**Problem:** No activities in specified date range

**Solution:**
1. Increase "Days to analyze" to 90
2. Make sure you have Strava activities
3. Run `python strava_diagnostic.py` to test API

---

## 📁 Project Structure

```
triathlon-coach/
├── src/                          # Source code
│   ├── agents/                   # CrewAI agents
│   │   ├── coach_agent.py
│   │   ├── base_agent.py
│   │   └── __init__.py
│   ├── api/                      # FastAPI endpoints
│   │   ├── main.py
│   │   └── __init__.py
│   ├── data/                     # Data clients
│   │   ├── strava_client.py      # Strava API
│   │   ├── models.py             # Pydantic models
│   │   └── __init__.py
│   ├── llm/                      # LLM interface
│   │   ├── ollama_handler.py
│   │   └── __init__.py
│   └── utils/                    # Utilities
│       ├── config.py
│       ├── logger.py
│       └── __init__.py
├── docker/                       # Docker files
│   ├── Dockerfile.app
│   └── Dockerfile.ollama
├── config/                       # Configuration
│   ├── ollama_models.txt
│   └── agent_roles.yaml
├── logs/                         # Created automatically
├── .env                          # Your credentials
├── .env.example                  # Template
├── .gitignore
├── .dockerignore
├── requirements.txt              # Python dependencies
├── docker-compose.yml            # Docker orchestration
├── streamlit_app.py              # Interactive UI
├── README.md                     # This file
└── ARCHITECTURE.md               # Technical details
```

---

## 🧪 Testing

### Test Strava Connection

```bash
python strava_diagnostic.py
```

Should show:
```
✅ Client initialized
✅ Athlete read works!
✅ Raw activities endpoint works!
```

### Test LLM

```bash
python -c "
from src.llm.ollama_handler import OllamaHandler
from src.utils.config import get_settings
settings = get_settings()
ollama = OllamaHandler(settings.ollama_base_url, settings.ollama_model)
if ollama.health_check():
    print('✅ Ollama working')
else:
    print('❌ Ollama not responding')
"
```

### Run Unit Tests

```bash
pytest tests/ -v
```

---

## 🚀 Production Deployment

### Recommended Setup

**Hardware:**
- CPU: 8+ cores
- RAM: 16GB
- Storage: 20GB SSD
- GPU: Optional (NVIDIA for 3-5x speedup)

### Cloud Options (Free/Cheap)

- **Oracle Cloud Always Free**: 4 ARM CPUs, 24GB RAM
- **Google Cloud Always Free**: f1-micro (limited)
- **DigitalOcean**: $5/month basic droplet
- **Linode**: $5/month basic instance

### Docker Compose for Production

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

---

## 📚 Advanced Features

### Change Analysis Agents

Edit `src/agents/coach_agent.py` to customize:
- Coaching recommendations
- Performance analysis
- Training plan generation

### Add New Data Sources

1. Create client in `src/data/`
2. Implement same interface as StravaClient
3. Update Streamlit to use it

### Custom LLM Models

In `.env`:
```env
OLLAMA_MODEL=mistral:7b
```

Download new models:
```bash
docker exec triathlon-ollama ollama pull mistral:7b
```

---

## 🔐 Security & Privacy

✅ **All local**: No data sent to cloud services
✅ **No subscriptions**: Zero API costs
✅ **Credentials safe**: .env is git-ignored
✅ **Private models**: Run your own LLMs
✅ **Open source**: Full code transparency

---

## 📖 Documentation

- **README.md** (this file) - Overview and setup
- **ARCHITECTURE.md** - Technical design and data flow
- **GETTING_STARTED.md** - Implementation examples
- **STRAVA_SIMPLE_AUTH.md** - Strava authentication guide
- **QUICK_REFERENCE.md** - Command reference

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional data sources (Garmin, Wahoo, Zwift)
- Web dashboard (React/Vue)
- Mobile app integration
- Advanced analytics & predictions
- Machine learning models

---

## 📄 License

MIT License - See LICENSE file

---

## 🎉 Getting Help

**Strava issues?** → See STRAVA_SIMPLE_AUTH.md
**Docker issues?** → Check docker-compose logs
**Code issues?** → Run strava_diagnostic.py
**Configuration?** → Check .env file

---

## 🏆 What's Next?

After successful setup:

1. ✅ Explore coaching insights
2. ✅ Review AI recommendations
3. ✅ Experiment with different analysis periods
4. ✅ Customize agent behavior
5. ✅ Add new features

---

## 📊 Performance

**Typical response times (on 8-core, 16GB):**
- Fetch activities: 5-10 seconds
- Coach analysis: 3-5 seconds  
- AI insights: 5-8 seconds
- Total workflow: ~20 seconds

**Memory usage:**
- Ollama (7B model): ~4-6GB
- FastAPI app: ~1-2GB
- Redis: ~500MB-1GB
- Total: ~6-9GB

---

## 🎯 Success Checklist

- [ ] Python 3.11+ installed
- [ ] Virtual environment created and activated
- [ ] requirements.txt installed
- [ ] Strava credentials obtained
- [ ] .env file configured
- [ ] `streamlit run streamlit_app.py` starts without errors
- [ ] Can fetch activities from Strava
- [ ] Coach analysis works
- [ ] AI insights generated
- [ ] No errors in logs

All checked? You're ready to use Triathlon Coach AI! 🚀

---

## 📞 Support

- **Issues**: Check troubleshooting section
- **Questions**: Review documentation files
- **Feedback**: GitHub issues/discussions
- **Bug reports**: Include full error message and logs

---

**Version:** 1.0.0  
**Last Updated:** 2024  