# Go API Gateway

This directory contains the Go API Gateway service for the Agentic Content Factory.

## Architecture Role

The Go Gateway serves as the **API Gateway & Control Layer** in the polyglot architecture:

```
Rust Client (Tauri) ──► Go Gateway (REST/WebSocket) ──► Python Services (gRPC)
                              │
                              ├── Authentication & JWT
                              ├── Rate Limiting
                              ├── Load Balancing
                              └── WebSocket for real-time updates
```

## Features

- **REST API**: Single, clean REST API for the frontend
- **WebSocket**: Real-time progress updates (e.g., "Video 45% generated")
- **gRPC Client**: Routes requests to Python AI services
- **Authentication**: JWT-based authentication
- **Rate Limiting**: Configurable rate limiting per endpoint
- **Traffic Management**: Load balancing across Python services

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/content` | Create new content |
| GET | `/api/v1/content/:id` | Get content status |
| GET | `/api/v1/parameters` | Get current brand parameters |
| POST | `/api/v1/evolve` | Trigger parameter evolution |
| WS | `/ws/progress/:id` | Real-time progress updates |

## Configuration

Environment variables:
- `PYTHON_ORCHESTRATOR_ADDR`: Address of Python orchestrator service (default: `orchestrator:50051`)
- `PYTHON_VIDEO_SERVICE_ADDR`: Address of video service (default: `video-service:50052`)
- `PYTHON_AUDIO_SERVICE_ADDR`: Address of audio service (default: `audio-service:50053`)
- `JWT_SECRET`: Secret for JWT signing
- `REDIS_URL`: Redis URL for session management

## Development

```bash
# Install dependencies
go mod download

# Generate gRPC client code from protos
protoc --go_out=. --go-grpc_out=. ../protos/content_factory.proto

# Run the gateway
go run main.go

# Build for production
go build -o gateway main.go
```

## Docker

```bash
# Build image
docker build -t content-factory-gateway .

# Run container
docker run -p 8080:8080 -p 8081:8081 content-factory-gateway
```

## Example Handler (Reference)

```go
// handlers/create_video.go
func HandleCreateVideo(w http.ResponseWriter, r *http.Request) {
    var req VideoRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, "Invalid request", http.StatusBadRequest)
        return
    }
    
    // Forward the request to the Python video service via gRPC
    grpcResp, err := pythonVideoClient.Render(r.Context(), &grpcProto.VideoRequest{
        Prompt: req.Prompt,
        Style:  req.Style,
    })
    
    // Return a job ID to the frontend for status polling
    json.NewEncoder(w).Encode(map[string]string{"jobId": grpcResp.JobId})
}
```
