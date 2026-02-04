"""
Evolutionary Loop Models - Data structures for optimization

These models represent the engagement metrics and fitness functions
as defined in the mathematical specification.
"""

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field
import numpy as np


class EngagementMetrics(BaseModel):
    """
    Post-deployment engagement metrics.
    
    Represents: e_{t+1} ∈ R^4 (views, likes, shares, watch-time %)
    """
    content_id: str
    platform: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Core metrics
    views: int = Field(default=0, ge=0)
    likes: int = Field(default=0, ge=0)
    shares: int = Field(default=0, ge=0)
    comments: int = Field(default=0, ge=0)
    
    # Watch time metrics
    watch_time_percent: float = Field(
        default=0.0, 
        ge=0.0, 
        le=1.0,
        description="Average watch time as percentage of total duration"
    )
    
    # Derived metrics
    @property
    def like_rate(self) -> float:
        """Likes per view."""
        return self.likes / self.views if self.views > 0 else 0.0
    
    @property
    def share_rate(self) -> float:
        """Shares per view."""
        return self.shares / self.views if self.views > 0 else 0.0
    
    @property
    def engagement_rate(self) -> float:
        """Total engagement (likes + shares + comments) per view."""
        if self.views == 0:
            return 0.0
        return (self.likes + self.shares + self.comments) / self.views


class FitnessScore(BaseModel):
    """
    Fitness score for evolutionary optimization.
    
    Implements:
    f_t(θ_t) = 0.4 * (likes/views) + 0.3 * (shares/views) + 0.3 * watch% - 0.1 * cost(t)
    """
    content_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Component scores
    like_score: float = Field(default=0.0)
    share_score: float = Field(default=0.0)
    watch_score: float = Field(default=0.0)
    cost_penalty: float = Field(default=0.0)
    
    # Weights (from specification)
    w_likes: float = Field(default=0.4)
    w_shares: float = Field(default=0.3)
    w_watch: float = Field(default=0.3)
    w_cost: float = Field(default=0.1)
    
    # Historical comparison
    historical_average: float = Field(default=0.0)
    improvement_threshold: float = Field(default=1.2)  # 20% lift
    
    @property
    def total_fitness(self) -> float:
        """Calculate total fitness score."""
        return (
            self.w_likes * self.like_score +
            self.w_shares * self.share_score +
            self.w_watch * self.watch_score -
            self.w_cost * self.cost_penalty
        )
    
    @property
    def triggers_evolution(self) -> bool:
        """Check if fitness exceeds threshold for parameter evolution."""
        if self.historical_average == 0:
            return True  # First run always triggers
        return self.total_fitness > self.improvement_threshold * self.historical_average
    
    @classmethod
    def from_engagement(
        cls,
        content_id: str,
        metrics: EngagementMetrics,
        cost: float = 0.0,
        historical_avg: float = 0.0
    ) -> "FitnessScore":
        """Create fitness score from engagement metrics."""
        return cls(
            content_id=content_id,
            like_score=metrics.like_rate,
            share_score=metrics.share_rate,
            watch_score=metrics.watch_time_percent,
            cost_penalty=cost,
            historical_average=historical_avg,
        )


class BrandParameters(BaseModel):
    """
    Brand parameters that evolve based on engagement.
    
    Represents: θ_t = (θ_music, θ_text, θ_visual)
    """
    id: str
    generation: int = Field(default=0, description="Evolution generation")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Music parameters (θ_music ∈ Θ_music ⊂ R^5)
    music_tempo: float = Field(default=90.0, ge=60.0, le=180.0)
    music_energy: float = Field(default=0.4, ge=0.0, le=1.0)
    music_danceability: float = Field(default=0.3, ge=0.0, le=1.0)
    music_key_preference: int = Field(default=0, ge=0, le=11)  # 0-11 for C-B
    music_mood_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    
    # Text parameters (θ_text ∈ Θ_text ⊂ R^3)
    text_jargon_level: float = Field(default=0.3, ge=0.0, le=1.0)
    text_length_preference: float = Field(default=0.5, ge=0.0, le=1.0)
    text_caption_style_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    
    # Visual parameters
    visual_color_scheme: str = Field(default="red_black")
    visual_contrast: float = Field(default=0.7, ge=0.0, le=1.0)
    visual_saturation: float = Field(default=0.6, ge=0.0, le=1.0)
    
    # Fitness tracking
    fitness_history: list[float] = Field(default_factory=list)
    
    def to_vector(self) -> np.ndarray:
        """Convert parameters to optimization vector."""
        return np.array([
            (self.music_tempo - 60.0) / 120.0,  # Normalize [60,180] to [0,1]
            self.music_energy,
            self.music_danceability,
            self.music_mood_weight,
            self.text_jargon_level,
            self.text_length_preference,
            self.text_caption_style_weight,
            self.visual_contrast,
            self.visual_saturation,
        ])
    
    @classmethod
    def from_vector(cls, vector: np.ndarray, base_params: "BrandParameters") -> "BrandParameters":
        """Create parameters from optimization vector."""
        return cls(
            id=str(uuid.uuid4()),
            generation=base_params.generation + 1,
            music_tempo=float(np.clip(vector[0] * 120.0 + 60.0, 60.0, 180.0)),
            music_energy=float(np.clip(vector[1], 0.0, 1.0)),
            music_danceability=float(np.clip(vector[2], 0.0, 1.0)),
            music_mood_weight=float(np.clip(vector[3], 0.0, 1.0)),
            text_jargon_level=float(np.clip(vector[4], 0.0, 1.0)),
            text_length_preference=float(np.clip(vector[5], 0.0, 1.0)),
            text_caption_style_weight=float(np.clip(vector[6], 0.0, 1.0)),
            visual_contrast=float(np.clip(vector[7], 0.0, 1.0)),
            visual_saturation=float(np.clip(vector[8], 0.0, 1.0)),
            visual_color_scheme=base_params.visual_color_scheme,
            music_key_preference=base_params.music_key_preference,
            fitness_history=base_params.fitness_history.copy(),
        )
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


class EvolutionConfig(BaseModel):
    """Configuration for evolutionary algorithm."""
    
    # Population settings
    population_size: int = Field(default=10, description="N=10")
    elite_count: int = Field(default=3, description="k=3")
    
    # Hyperparameters (from specification)
    alpha: float = Field(default=0.1, description="Perturbation scale")
    beta: float = Field(default=0.7, description="Mutation rate")
    
    # Convergence
    max_generations: int = Field(default=100)
    fitness_threshold: float = Field(default=0.9)
    
    # Discount factor (γ = 0.95)
    discount_factor: float = Field(default=0.95)
