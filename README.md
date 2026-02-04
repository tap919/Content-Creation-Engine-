# Agentic Content Factory

An AI-powered multi-agent content creation engine that automates the entire content production pipeline from trend detection to video generation.

## 🎯 Overview

The Agentic Content Factory implements a "Bio-Digital Creative Reflex" - a system that acts as a digital nervous system for content creation. It doesn't just schedule posts; it observes trends, mutates content strategy through evolutionary algorithms, and executes production autonomously.

## 🏗️ Architecture

The system uses a **polyglot architecture** combining Rust, Go, and Python to leverage the unique strengths of each language:

```
┌─────────────────────────────────────────────────────────────────┐
│              Rust Client (Tauri) - PLANNED                      │
│         Desktop UI • Local File Management • API Key Storage    │
│         (Not yet implemented - see Architecture file)           │
└─────────────────────────────────────────────────────────────────┘
                              │ REST / WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Go API Gateway (Placeholder)                       │
│        Authentication • Rate Limiting • WebSocket Updates       │
│              Request Routing • Traffic Management               │
└─────────────────────────────────────────────────────────────────┘
                              │ gRPC
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Python AI Services                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │Video Service │  │Audio Service │  │Avatar Service│         │
│  │FLUX.1, Sora, │  │MusicGen,     │  │(Planned)     │         │
│  │Veo, Runway   │  │ElevenLabs    │  │D-ID, Tavus   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │ API Calls
                              ▼
                      External AI APIs
```

> **Note:** The Rust/Tauri client and Go gateway are planned components described in the 
> Architecture file. The Go gateway has a placeholder implementation; the Rust client 
> will be developed separately. Currently, the Python orchestrator provides direct REST API access.

### Core Layers

#### 1. Sentinel Layer (Perception)
- **Trend Detection**: Scrapes social media, news sources, and forums for trending topics
- **High-Signal Event Detection**: Uses statistical analysis to identify significant trends
- **Brief Generation**: Creates creative briefs from detected trends using LLM

#### 2. Production Hive (Creation)
Multi-agent system with specialized AI agents:
- **Agent A (Visualist)**: Generates image variations using FLUX.1/Stable Diffusion
- **Agent B (Critic)**: Evaluates images using Vision-Language Models
- **Agent C (Editor)**: Assembles video using MoviePy with text overlays
- **Agent D (Audio)**: Generates background music using MusicGen

#### 3. Evolutionary Loop (Optimization)
- **Engagement Tracking**: Monitors likes, shares, watch time across platforms
- **Fitness Evaluation**: Calculates fitness scores using weighted metrics
- **Parameter Evolution**: Evolves brand parameters using evolutionary algorithms

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Docker (optional)
- FFmpeg (for video processing)
- Go 1.22+ (for gateway service)

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
# API Server mode (Python orchestrator)
python -m src.main --mode api --port 8000

# Worker mode (background content generation)
python -m src.main --mode worker

# Single cycle mode (one content generation)
python -m src.main --mode single
```

### Using Docker

> **Breaking change:** The Docker service previously named `api` has been renamed to 
> `orchestrator`. Update any existing scripts or commands accordingly.

```bash
# Build and run default services (orchestrator, worker, redis, db)
docker-compose up --build

# Run with Go gateway and separate Python services
docker-compose --profile gateway --profile services up --build

# Run only the Python orchestrator
docker-compose up orchestrator
```

See the comments in `docker-compose.yml` for detailed information about available profiles.

## 📡 API Endpoints

### Python Orchestrator (REST API)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/content/generate` | POST | Trigger content generation |
| `/parameters` | GET | Get current brand parameters |
| `/evolve` | POST | Manually trigger parameter evolution |

### Go Gateway (when enabled)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/content` | POST | Create new content |
| `/api/v1/content/:id` | GET | Get content status |
| `/api/v1/parameters` | GET | Get current brand parameters |
| `/ws/progress/:id` | WebSocket | Real-time progress updates |

### Example: Generate Content

```bash
curl -X POST http://localhost:8000/content/generate \
  -H "Content-Type: application/json" \
  -d '{"force_generation": true}'
```

## 🔗 Service Communication

The services communicate using **gRPC with Protocol Buffers**:

```protobuf
// Example: Video render request
service VideoService {
  rpc Render(VideoRenderRequest) returns (VideoRenderResponse);
  rpc GetJobStatus(JobStatusRequest) returns (JobStatusResponse);
}
```

Protocol Buffer definitions are in `/protos/content_factory.proto`.

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
├── protos/            # gRPC Protocol Buffer definitions
├── go-gateway/        # Go API Gateway (REST/WebSocket)
├── src/
│   ├── sentinel/      # Trend detection layer
│   ├── hive/          # Content production agents
│   ├── evolution/     # Parameter optimization
│   ├── services/      # Python gRPC services
│   │   ├── video_service.py
│   │   └── audio_service.py
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
| **Frontend** | Rust (Tauri) |
| **API Gateway** | Go |
| **AI Services** | Python |
| **Inter-Service Comm** | gRPC + Protocol Buffers |
| **Orchestrator** | CrewAI |
| **API Framework** | FastAPI |
| **Video Editing** | MoviePy |
| **Image Generation** | FLUX.1 / ComfyUI |
| **Audio Generation** | MusicGen / AudioCraft |
| **TTS** | ElevenLabs, Azure Speech |
| **Workflow Automation** | n8n / Prefect |
| **Embeddings** | Sentence Transformers |
| **Task Queue** | Celery + Redis |

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests.

---

Built with ❤️ for the creative community
