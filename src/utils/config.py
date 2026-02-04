"""
Configuration Management

Handles loading and validation of configuration for the Agentic Content Factory.
"""

from pathlib import Path
from typing import Optional
import yaml
from pydantic import BaseModel, ConfigDict, Field


class GRPCConfig(BaseModel):
    """gRPC server configuration."""
    
    enabled: bool = Field(default=True)
    port: int = Field(default=50051)
    max_workers: int = Field(default=10)
    max_message_length: int = Field(default=104857600)  # 100MB


class ServiceConfig(BaseModel):
    """Configuration for an individual service."""
    
    host: str = Field(default="localhost")
    port: int = Field(default=50051)
    providers: list[str] = Field(default_factory=list)


class ServicesConfig(BaseModel):
    """Configuration for all services in the polyglot architecture."""
    
    grpc: GRPCConfig = Field(default_factory=GRPCConfig)
    video_service: ServiceConfig = Field(
        default_factory=lambda: ServiceConfig(
            port=50052,
            providers=["flux1", "sora", "veo", "runway"]
        )
    )
    audio_service: ServiceConfig = Field(
        default_factory=lambda: ServiceConfig(
            port=50053,
            providers=["musicgen", "elevenlabs", "azure_speech", "amazon_polly"]
        )
    )
    avatar_service: ServiceConfig = Field(
        default_factory=lambda: ServiceConfig(
            port=50054,
            providers=["d_id", "tavus"]
        )
    )


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""
    
    enabled: bool = Field(default=True)
    requests_per_minute: int = Field(default=60)
    burst_size: int = Field(default=10)


class AuthConfig(BaseModel):
    """Authentication configuration."""
    
    enabled: bool = Field(default=False)
    jwt_expiry_hours: int = Field(default=24)


class CORSConfig(BaseModel):
    """CORS configuration."""
    
    allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:8080",
            "tauri://localhost",
        ]
    )
    allowed_methods: list[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE"]
    )
    allowed_headers: list[str] = Field(
        default_factory=lambda: ["Authorization", "Content-Type"]
    )


class GatewayConfig(BaseModel):
    """API Gateway configuration."""
    
    host: str = Field(default="0.0.0.0")
    rest_port: int = Field(default=8080)
    websocket_port: int = Field(default=8081)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    cors: CORSConfig = Field(default_factory=CORSConfig)


class WorkflowConfig(BaseModel):
    """Workflow orchestration configuration."""
    
    engine: str = Field(default="internal")  # Options: internal, prefect, luigi
    max_concurrent_jobs: int = Field(default=5)
    job_timeout_seconds: int = Field(default=300)


class Config(BaseModel):
    """Main configuration for the Agentic Content Factory."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    # General settings
    app_name: str = Field(default="Agentic Content Factory")
    environment: str = Field(default="development")
    debug: bool = Field(default=True)
    
    # Output directories
    output_dir: str = Field(default="./output")
    
    # Brand settings
    brand_aesthetic: str = Field(default="Code of the Streets")
    brand_name: str = Field(default="Bio-Hacker Update")
    
    # Content cycle settings
    cycle_interval_seconds: int = Field(default=3600)  # 1 hour
    
    # Trend sources
    trend_sources: list[str] = Field(
        default_factory=lambda: [
            "biotech_news",
            "pubmed",
            "twitter",
            "reddit_biotech",
        ]
    )
    
    # Deployment platforms
    deployment_platforms: list[str] = Field(
        default_factory=lambda: [
            "instagram",
            "tiktok",
            "youtube_shorts",
        ]
    )
    
    # API Keys (loaded from environment)
    openai_api_key: Optional[str] = Field(default=None)
    twitter_api_key: Optional[str] = Field(default=None)
    
    # Model settings
    embedding_model: str = Field(default="all-MiniLM-L6-v2")
    llm_model: str = Field(default="gpt-4")
    
    # Production settings
    max_image_variations: int = Field(default=5)
    target_video_duration: int = Field(default=15)
    
    # Polyglot architecture settings
    services: ServicesConfig = Field(default_factory=ServicesConfig)
    gateway: GatewayConfig = Field(default_factory=GatewayConfig)
    workflow: WorkflowConfig = Field(default_factory=WorkflowConfig)


def load_config(config_path: Path) -> Config:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        Config object with loaded settings
    """
    with open(config_path, "r") as f:
        data = yaml.safe_load(f)
    
    return Config(**data) if data else Config()
