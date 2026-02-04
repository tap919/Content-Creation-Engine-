# Go Gateway - Docker Build
# Placeholder Dockerfile for the Go API Gateway

FROM golang:1.22-alpine AS builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache git protobuf protobuf-dev

# Copy go mod files (go.sum may not exist for placeholder module)
COPY go.mod ./
COPY go.sum* ./
RUN go mod download || true

# Copy source code
COPY . .

# Build the gateway
RUN CGO_ENABLED=0 GOOS=linux go build -o gateway .

# Production stage
FROM alpine:3.19

WORKDIR /app

# Install runtime dependencies
RUN apk add --no-cache ca-certificates

# Copy binary from builder
COPY --from=builder /app/gateway .

# Expose ports
EXPOSE 8080 8081

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost:8080/health || exit 1

# Run the gateway
ENTRYPOINT ["./gateway"]
