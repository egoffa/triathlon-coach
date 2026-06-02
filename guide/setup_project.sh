#!/bin/bash

# Triathlon Coach AI - Project Setup Script
# This script sets up the complete project structure

set -e

echo "================================"
echo "🏊 Triathlon Coach AI Setup"
echo "================================"

PROJECT_NAME="triathlon-coach"

# Create main directories
echo "📁 Creating project structure..."
mkdir -p $PROJECT_NAME/{src/{agents,data,llm,api,utils},config,tests,docker,notebooks,logs}

# Create __init__.py files
touch $PROJECT_NAME/src/__init__.py
touch $PROJECT_NAME/src/agents/__init__.py
touch $PROJECT_NAME/src/data/__init__.py
touch $PROJECT_NAME/src/llm/__init__.py
touch $PROJECT_NAME/src/api/__init__.py
touch $PROJECT_NAME/src/utils/__init__.py
touch $PROJECT_NAME/tests/__init__.py

# Copy source files
echo "📝 Adding source code files..."
cp src_utils_config.py $PROJECT_NAME/src/utils/config.py
cp src_utils_logger.py $PROJECT_NAME/src/utils/logger.py
cp src_data_models.py $PROJECT_NAME/src/data/models.py
cp src_data_strava_client.py $PROJECT_NAME/src/data/strava_client.py
cp src_llm_ollama_handler.py $PROJECT_NAME/src/llm/ollama_handler.py
cp src_api_main.py $PROJECT_NAME/src/api/main.py
cp src_agents_base_agent.py $PROJECT_NAME/src/agents/base_agent.py
cp src_agents_coach_agent.py $PROJECT_NAME/src/agents/coach_agent.py

# Copy configuration files
echo "⚙️  Adding configuration files..."
cp requirements.txt $PROJECT_NAME/
cp docker-compose.yml $PROJECT_NAME/
cp Dockerfile.app $PROJECT_NAME/docker/
cp Dockerfile.ollama $PROJECT_NAME/docker/
cp .env.example $PROJECT_NAME/
cp .gitignore $PROJECT_NAME/
cp .dockerignore $PROJECT_NAME/

# Copy documentation
echo "📚 Adding documentation..."
cp README.md $PROJECT_NAME/
cp ARCHITECTURE.md $PROJECT_NAME/
cp FRAMEWORK_GUIDE.md $PROJECT_NAME/
cp QUICK_REFERENCE.md $PROJECT_NAME/
cp GETTING_STARTED.md $PROJECT_NAME/

# Copy tests
echo "🧪 Adding test files..."
cp tests_test_api.py $PROJECT_NAME/tests/test_api.py

# Initialize git
echo "🔧 Initializing git repository..."
cd $PROJECT_NAME
git init
git add .
git commit -m "Initial project structure - v1.0"

echo ""
echo "================================"
echo "✅ Setup Complete!"
echo "================================"
echo ""
echo "📖 Next Steps:"
echo "1. cd $PROJECT_NAME"
echo "2. cp .env.example .env"
echo "3. Edit .env with your Strava credentials"
echo "4. docker-compose up --build"
echo ""
echo "📚 Documentation:"
echo "- Start with: README.md"
echo "- Setup guide: GETTING_STARTED.md"
echo "- Architecture: ARCHITECTURE.md"
echo "- Quick ref: QUICK_REFERENCE.md"
echo ""
echo "Happy training! 🏊🚴🏃"
