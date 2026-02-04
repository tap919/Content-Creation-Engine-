# Agentic Content Factory

An AI-powered multi-agent content creation engine that automates the entire content production pipeline from trend detection to video generation.

## 🎯 Overview

The Agentic Content Factory implements a "Bio-Digital Creative Reflex" - a system that acts as a digital nervous system for content creation. It doesn't just schedule posts; it observes trends, mutates content strategy through evolutionary algorithms, and executes production autonomously.

## 🏗️ Architecture

The system consists of three core layers:

### 1. Sentinel Layer (Perception)
- **Trend Detection**: Scrapes social media, news sources, and forums for trending topics
- **High-Signal Event Detection**: Uses statistical analysis to identify significant trends
- **Brief Generation**: Creates creative briefs from detected trends using LLM

### 2. Production Hive (Creation)
Multi-agent system with specialized AI agents:
- **Agent A (Visualist)**: Generates image variations using FLUX.1/Stable Diffusion
- **Agent B (Critic)**: Evaluates images using Vision-Language Models
- **Agent C (Editor)**: Assembles video using MoviePy with text overlays
- **Agent D (Audio)**: Generates background music using MusicGen

### 3. Evolutionary Loop (Optimization)
- **Engagement Tracking**: Monitors likes, shares, watch time across platforms
- **Fitness Evaluation**: Calculates fitness scores using weighted metrics
- **Parameter Evolution**: Evolves brand parameters using evolutionary algorithms

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Docker (optional)
- FFmpeg (for video processing)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/Content-Creation-Engine-.git
cd Content-Creation-Engine-

# Run the build script
./scripts/build.sh

# Or manually:
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configuration

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Fill in your API keys in `.env`

3. Customize `config/config.yaml` for your brand settings

### Running

```bash
# API Server mode
python -m src.main --mode api --port 8000

# Worker mode (background content generation)
python -m src.main --mode worker

# Single cycle mode (one content generation)
python -m src.main --mode single
```

### Using Docker

```bash
# Build and run all services
docker-compose up --build

# Run only the API server
docker-compose up api
```

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/content/generate` | POST | Trigger content generation |
| `/parameters` | GET | Get current brand parameters |
| `/evolve` | POST | Manually trigger parameter evolution |

### Example: Generate Content

```bash
curl -X POST http://localhost:8000/content/generate \
  -H "Content-Type: application/json" \
  -d '{"force_generation": true}'
```

## 🧮 Mathematical Specification

The system implements a discrete-time Markov decision process (MDP) with:

- **State**: Trend embedding (512-dim) + Music params (R^5) + Text params (R^3)
- **Action**: Topic selection + parameter perturbations
- **Reward**: Hive proxy reward + engagement fitness

Fitness function:
```
f(θ) = 0.4 * (likes/views) + 0.3 * (shares/views) + 0.3 * watch% - 0.1 * cost
```

Evolutionary step (population N=10, elite k=3):
```
θ_{t+1} = (1-β) * θ_elite + β * M(θ_elite, η)
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## 📁 Project Structure

```
Content-Creation-Engine-/
├── src/
│   ├── sentinel/       # Trend detection layer
│   ├── hive/          # Content production agents
│   ├── evolution/     # Parameter optimization
│   ├── api/           # FastAPI server
│   ├── utils/         # Configuration & utilities
│   └── main.py        # Entry point
├── config/            # Configuration files
├── tests/             # Test suite
├── scripts/           # Build & run scripts
├── Dockerfile         # Container build
└── docker-compose.yml # Full stack deployment
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Orchestrator | CrewAI |
| API Framework | FastAPI |
| Video Editing | MoviePy |
| Image Generation | FLUX.1 / ComfyUI |
| Audio Generation | MusicGen / AudioCraft |
| Workflow Automation | n8n |
| Embeddings | Sentence Transformers |
| Task Queue | Celery + Redis |

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests.

---

Built with ❤️ for the creative community
