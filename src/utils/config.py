"""
Configuration Management

Handles loading and validation of configuration for the Agentic Content Factory.
"""

from pathlib import Path
from typing import Optional
import yaml
from pydantic import BaseModel, Field


class Config(BaseModel):
    """Main configuration for the Agentic Content Factory."""
    
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
    
    class model_config:
        env_file = ".env"
        env_file_encoding = "utf-8"


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
