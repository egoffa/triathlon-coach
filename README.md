# Triathlon Coach AI 🏊🚴🏃

An open-source, self-hosted AI triathlon coaching system that analyzes your training data and provides personalized coaching recommendations. Built with CrewAI, Ollama, and local LLMs for zero-cost deployment.

## 🎯 Features

- **Multi-Agent AI System**: CrewAI-powered agents for coaching, analytics, and training planning
- **Local LLM Support**: Run Llama models locally via Ollama (no API costs)
- **Strava/Garmin Integration**: Pull training data via MCP servers
- **Performance Analytics**: Analyze metrics like FTP, TSS, training zones, and trends
- **Adaptive Training Plans**: Get personalized training recommendations based on performance
- **Fully Containerized**: Docker + Docker Compose for easy deployment
- **Zero Cost**: No cloud LLM subscriptions, no AI API costs
- **REST API**: FastAPI-based API for easy integration

## 📋 Prerequisites

- Docker and Docker Compose (v1.29+)
- 8GB+ RAM (16GB+ recommended)
- GPU optional but recommended (NVIDIA with CUDA support)
- Strava account with API access (and/or Garmin account)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/yourusername/triathlon-coach.git
cd triathlon-coach
cp .env.example .env
```

### 2. Configure Your Credentials

Edit `.env` with your Strava/Garmin credentials:

```bash
# Get Strava credentials from: https://www.strava.com/settings/api
STRAVA_CLIENT_ID=your_client_id
STRAVA_CLIENT_SECRET=your_client_secret
STRAVA_REFRESH_TOKEN=your_refresh_token

# Optional: Garmin credentials
GARMIN_EMAIL=your_email@example.com
GARMIN_PASSWORD=your_password
```

#### Getting Strava Credentials:
1. Go to https://www.strava.com/settings/api
2. Create an API application
3. Get your Client ID and Secret
4. Use a tool like [strava-oauth](https://github.com/stravalib/stravalib) to get refresh token

### 3. Start the System

```bash
docker-compose up --build
```

This will:
- Start Ollama container and download llama2:7b model (first run takes 5-10 minutes)
- Start Redis cache
- Start the FastAPI application

Services will be available at:
- **API**: http://localhost:8000
- **Ollama**: http://localhost:11434
- **Redis**: localhost:6379

### 4. Test the Setup

```bash
# Check API health
curl http://localhost:8000/health

# Get your latest activities
curl http://localhost:8000/api/activities/latest?limit=5

# Get AI coaching analysis
curl -X POST http://localhost:8000/api/coach/analyze \
  -H "Content-Type: application/json" \
  -d '{"activity_id": 123456789}'
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│           FastAPI Web Application               │
│  Routes: /api/activities, /api/coach, /api/plan │
└──────────────┬──────────────────────────────────┘
               │
       ┌───────┴───────┐
       │               │
┌──────▼──────┐  ┌──────▼──────┐
│  CrewAI     │  │    Redis    │
│  Agents     │  │    Cache    │
└──────┬──────┘  └─────────────┘
       │
   ┌───┴──────────────────┬──────────────┐
   │                      │              │
┌──▼────┐  ┌──────────┐  ┌▼─────┐  ┌───▼─────┐
│Ollama │  │ Strava  │  │Garmin│  │Analytics│
│ LLM   │  │  MCP    │  │ MCP  │  │ Tools   │
└───────┘  └──────────┘  └──────┘  └─────────┘
```

**Components:**
- **FastAPI App**: REST API and request handling
- **CrewAI**: Multi-agent orchestration framework
- **Ollama**: Local LLM inference engine
- **Strava/Garmin MCP**: Data source integration
- **Redis**: Caching and session management
- **Analytics Tools**: Custom metric calculation

## 📁 Project Structure

```
triathlon-coach/
├── docker/
│   ├── Dockerfile.app          # Main app container
│   ├── Dockerfile.ollama       # LLM service container
│   └── docker-compose.yml      # Orchestration
├── src/
│   ├── agents/                 # CrewAI agent definitions
│   │   ├── coach_agent.py
│   │   ├── analytics_agent.py
│   │   └── planning_agent.py
│   ├── data/                   # Data clients
│   │   ├── strava_client.py    # Strava API integration
│   │   ├── garmin_client.py    # Garmin API integration
│   │   ├── mcp_manager.py      # MCP server management
│   │   └── models.py           # Data models
│   ├── llm/
│   │   └── ollama_handler.py   # LLM interface
│   ├── api/                    # FastAPI routes
│   │   ├── main.py
│   │   └── routes.py
│   └── utils/                  # Utilities
│       ├── config.py
│       └── logger.py
├── config/
│   ├── ollama_models.txt       # Model selection
│   └── agent_roles.yaml        # Agent configuration
├── tests/                      # Unit tests
├── requirements.txt
├── .env.example
└── README.md
```

## 🔧 Configuration

### LLM Model Selection

Edit `.env` and docker-compose.yml to choose your model:

```bash
# Lightweight (4-6GB RAM)
OLLAMA_MODEL=llama2:7b              # Default
OLLAMA_MODEL=neural-chat:7b         # Better instruction following
OLLAMA_MODEL=openchat:7b            # Fast

# Powerful (8GB+ RAM)
OLLAMA_MODEL=llama2:13b             # Better reasoning
OLLAMA_MODEL=mistral:7b             # Strong all-rounder
```

Download additional models at runtime:
```bash
docker exec triathlon-ollama ollama pull mistral:7b
```

### Agent Configuration

Edit `config/agent_roles.yaml` to customize agent behavior, roles, and goals.

## 🔌 MCP (Model Context Protocol) Integration

### Strava MCP Setup

```python
# src/data/mcp_manager.py handles MCP server initialization
# Strava MCP allows agents to:
# - Fetch athlete activities
# - Get segment performances
# - Access training data
```

### Adding Custom MCP Servers

1. Define MCP server in `mcp_manager.py`
2. Add credentials to `.env`
3. Reference in agent tools

## 🧠 How It Works

### 1. Data Ingestion
```
User → FastAPI → Strava/Garmin MCP → Training Data
```

### 2. AI Analysis
```
Training Data → CrewAI Agents (Coach, Analytics, Planner) → LLM (Ollama)
```

### 3. Recommendations
```
LLM Analysis → JSON Response → FastAPI → User
```

## 📊 API Endpoints

### Health Check
```bash
GET /health
```

### Activities
```bash
# Get recent activities
GET /api/activities/latest?limit=10

# Get specific activity
GET /api/activities/{activity_id}

# Sync latest from Strava
POST /api/activities/sync
```

### Coaching
```bash
# Get AI coaching analysis
POST /api/coach/analyze
Body: { "activity_id": 123, "days_back": 7 }

# Get personalized tips
GET /api/coach/tips?focus=pace|power|recovery

# Get performance insights
GET /api/coach/insights
```

### Training Plans
```bash
# Generate training plan
POST /api/plans/generate
Body: { "goal": "ironman", "weeks": 12, "level": "intermediate" }

# Get current plan
GET /api/plans/current

# Update plan
PUT /api/plans/{plan_id}
```

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app
docker-compose logs -f ollama

# Stop services
docker-compose down

# Rebuild containers
docker-compose up --build

# Access container shell
docker exec -it triathlon-coach-app bash

# Run tests
docker exec triathlon-coach-app pytest tests/
```

## 📝 Development

### Local Setup (Without Docker)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start Ollama locally: https://ollama.ai
ollama serve
ollama pull llama2:7b

# In another terminal
python -m uvicorn src.api.main:app --reload
```

### Running Tests

```bash
docker exec triathlon-coach-app pytest tests/ -v
# Or locally:
pytest tests/ -v
```

### Code Quality

```bash
# Format code
black src/
flake8 src/
mypy src/
```

## 🚀 Performance Tips

### Optimize for CPU-only:
- Use `llama2:7b` or `neural-chat:7b`
- Set `OLLAMA_NUM_THREAD=4` (match your CPU cores)
- Cache frequently accessed data in Redis

### Optimize for GPU:
- Use `llama2:13b` for better quality
- Set `CUDA_VISIBLE_DEVICES=0` for single GPU
- Increase `gpu_memory_allocation` in docker-compose.yml

### Reduce Memory Usage:
- Use `llama2:7b` instead of 13b
- Increase Redis TTL for longer caching
- Implement request queuing for concurrent requests

## 🐛 Troubleshooting

### Ollama won't start
```bash
# Check Ollama logs
docker-compose logs ollama

# Increase memory in Docker Desktop settings
# Try a smaller model: neural-chat:7b instead of 13b
```

### Strava authentication fails
```bash
# Verify credentials in .env
# Check refresh token hasn't expired
# Get new refresh token from Strava OAuth
```

### High memory usage
```bash
# Reduce model size
# Increase OLLAMA_NUM_THREAD for CPU
# Reduce batch size in CrewAI config
```

### Slow responses
```bash
# Use a smaller LLM model
# Enable Redis caching
# Reduce agent iterations: CREW_AI_MAX_ITERATIONS=5
```

## 📚 Learning Resources

- [CrewAI Documentation](https://docs.crewai.io/)
- [Ollama Documentation](https://github.com/ollama/ollama)
- [Strava API Reference](https://developers.strava.com/docs/reference/)
- [Garmin Connect Documentation](https://developer.garmin.com/)
- [MCP Protocol](https://modelcontextprotocol.io/)

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional MCP integrations (Zwift, Wahoo)
- More sophisticated analytics
- Web UI dashboard
- Mobile app integration
- Advanced prediction models

## 📄 License

MIT License - see LICENSE file

## ⚠️ Disclaimer

This tool is for personal training analysis only. Always consult with qualified coaches or medical professionals before making significant changes to your training regimen.

## 🎉 Support

- Issues: GitHub Issues
- Discussions: GitHub Discussions
- Email: support@example.com

---

**Built with ❤️ for triathletes who want AI coaching without cloud costs**
