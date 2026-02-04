// Package main provides a placeholder implementation of the Go API Gateway.
//
// This is a minimal implementation to allow the Docker build to succeed.
// The full implementation will include:
// - REST API endpoints
// - WebSocket support for real-time updates
// - gRPC client for Python services
// - JWT authentication
// - Rate limiting
//
// See README.md for architecture details and planned features.
package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
)

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	http.HandleFunc("/health", healthHandler)
	http.HandleFunc("/", rootHandler)

	log.Printf("Go API Gateway starting on port %s (placeholder implementation)", port)
	log.Printf("This is a placeholder. Full implementation pending.")

	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"status":  "healthy",
		"service": "go-gateway",
		"note":    "placeholder implementation",
	})
}

func rootHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"service": "Content Factory Go API Gateway",
		"status":  "placeholder",
		"message": "Full implementation pending. See go-gateway/README.md for details.",
	})
}
