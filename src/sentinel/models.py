"""
Sentinel Layer Models - Data structures for trend detection

These models represent the state and action spaces as defined in the
mathematical specification for the Agentic Content Factory.
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
import numpy as np


class TrendData(BaseModel):
    """
    Represents detected trend data from the Sentinel layer.
    
    Maps to state component: x_t ∈ R^d_trend (trend embedding)
    """
    id: str = Field(..., description="Unique identifier for the trend")
    topic: str = Field(..., description="Main topic/theme of the trend")
    source: str = Field(..., description="Source of the trend data")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Embedding vector (512-dim CLIP/BERT vector from biotech news)
    embedding: Optional[list[float]] = Field(
        default=None,
        description="Dense embedding vector for the trend"
    )
    
    # Statistical measures for HSE detection
    raw_score: float = Field(default=0.0, description="Raw trend score")
    deviation_from_mean: float = Field(
        default=0.0,
        description="Distance from rolling historical mean (||x_t - μ_hist||_2)"
    )
    threshold: float = Field(
        default=2.0,
        description="Standard deviation threshold for HSE detection (2σ)"
    )
    
    # Metadata
    keywords: list[str] = Field(default_factory=list)
    sentiment_score: float = Field(default=0.0, ge=-1.0, le=1.0)
    
    @property
    def is_high_signal(self) -> bool:
        """
        Determine if this trend qualifies as a High-Signal Event (HSE).
        
        HSE if ||x_t - μ_hist||_2 > 2σ
        """
        return self.deviation_from_mean > self.threshold
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


class CreativeBrief(BaseModel):
    """
    Creative brief generated from a high-signal trend.
    
    This is the output from the Sentinel layer that feeds into
    the Production Hive: b_t = LLM(x_t, θ_brand)
    """
    id: str = Field(..., description="Unique identifier for the brief")
    trend_id: str = Field(..., description="ID of the source trend")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Core brief content
    topic: str = Field(..., description="Main topic for content")
    headline: str = Field(..., description="Suggested headline/hook")
    summary: str = Field(..., description="Brief summary of the trend")
    talking_points: list[str] = Field(
        default_factory=list,
        description="Key points to cover"
    )
    
    # Brand alignment
    brand_aesthetic: str = Field(
        default="Code of the Streets",
        description="Target brand aesthetic"
    )
    tone: str = Field(default="informative", description="Content tone")
    
    # Production parameters
    target_duration_seconds: int = Field(
        default=15,
        description="Target video duration"
    )
    target_platforms: list[str] = Field(
        default_factory=lambda: ["instagram", "tiktok", "youtube_shorts"]
    )
    
    # Music parameters (θ_music ∈ Θ_music ⊂ R^5)
    music_tempo: float = Field(default=90.0, ge=60.0, le=180.0)
    music_key: str = Field(default="C minor")
    music_mood: str = Field(default="lo-fi chill")
    music_energy: float = Field(default=0.4, ge=0.0, le=1.0)
    music_danceability: float = Field(default=0.3, ge=0.0, le=1.0)
    
    # Text parameters (θ_text ∈ Θ_text ⊂ R^3)
    text_length: str = Field(default="medium")  # short, medium, long
    jargon_level: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="0=layman, 1=expert"
    )
    caption_style: str = Field(default="animated")  # static, animated, dynamic


class TrendHistory(BaseModel):
    """Rolling history of trends for statistical analysis."""
    
    trends: list[TrendData] = Field(default_factory=list)
    window_days: int = Field(default=7)
    
    @property
    def mean_embedding(self) -> Optional[np.ndarray]:
        """Calculate μ_hist from rolling 7-day history."""
        embeddings = [
            np.array(t.embedding) for t in self.trends 
            if t.embedding is not None
        ]
        if not embeddings:
            return None
        return np.mean(embeddings, axis=0)
    
    @property
    def std_embedding(self) -> Optional[float]:
        """Calculate σ from rolling 7-day history."""
        embeddings = [
            np.array(t.embedding) for t in self.trends 
            if t.embedding is not None
        ]
        if len(embeddings) < 2:
            return None
        # Calculate standard deviation of distances from mean
        mean = self.mean_embedding
        distances = [np.linalg.norm(e - mean) for e in embeddings]
        return float(np.std(distances))
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
