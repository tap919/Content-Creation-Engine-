"""Tests for the Evolutionary Loop."""

import pytest
import numpy as np

from src.evolution.models import (
    EngagementMetrics, FitnessScore, BrandParameters
)
from src.evolution.evolution import EvolutionaryLoop
from src.utils.config import Config


class TestEngagementMetrics:
    """Tests for EngagementMetrics model."""
    
    def test_metrics_creation(self):
        """Test creating engagement metrics."""
        metrics = EngagementMetrics(
            content_id="test-123",
            platform="instagram",
            views=1000,
            likes=100,
            shares=50,
        )
        
        assert metrics.like_rate == 0.1
        assert metrics.share_rate == 0.05
    
    def test_engagement_rate(self):
        """Test engagement rate calculation."""
        metrics = EngagementMetrics(
            content_id="test-123",
            platform="instagram",
            views=1000,
            likes=100,
            shares=50,
            comments=25,
        )
        
        # (100 + 50 + 25) / 1000 = 0.175
        assert metrics.engagement_rate == 0.175
    
    def test_zero_views(self):
        """Test handling of zero views."""
        metrics = EngagementMetrics(
            content_id="test-123",
            platform="instagram",
            views=0,
            likes=0,
        )
        
        assert metrics.like_rate == 0.0
        assert metrics.engagement_rate == 0.0


class TestFitnessScore:
    """Tests for FitnessScore model."""
    
    def test_fitness_calculation(self):
        """Test fitness score calculation."""
        fitness = FitnessScore(
            content_id="test-123",
            like_score=0.1,    # 0.4 * 0.1 = 0.04
            share_score=0.05,  # 0.3 * 0.05 = 0.015
            watch_score=0.8,   # 0.3 * 0.8 = 0.24
            cost_penalty=0.1,  # 0.1 * 0.1 = 0.01
        )
        
        # Expected: 0.04 + 0.015 + 0.24 - 0.01 = 0.285
        expected = 0.04 + 0.015 + 0.24 - 0.01
        assert abs(fitness.total_fitness - expected) < 0.001
    
    def test_triggers_evolution(self):
        """Test evolution trigger logic."""
        # Should trigger with 0 historical average
        fitness = FitnessScore(
            content_id="test-123",
            like_score=0.1,
            share_score=0.05,
            watch_score=0.8,
            historical_average=0.0,
        )
        assert fitness.triggers_evolution
        
        # Should not trigger with low improvement
        fitness.historical_average = 0.5
        assert not fitness.triggers_evolution
    
    def test_from_engagement(self):
        """Test creating fitness from engagement."""
        metrics = EngagementMetrics(
            content_id="test-123",
            platform="instagram",
            views=1000,
            likes=100,
            shares=50,
            watch_time_percent=0.75,
        )
        
        fitness = FitnessScore.from_engagement(
            content_id="test-123",
            metrics=metrics,
            cost=0.1,
        )
        
        assert fitness.like_score == 0.1
        assert fitness.share_score == 0.05
        assert fitness.watch_score == 0.75


class TestBrandParameters:
    """Tests for BrandParameters model."""
    
    def test_parameters_creation(self):
        """Test creating brand parameters."""
        params = BrandParameters(
            id="params-123",
            generation=0,
        )
        
        assert params.music_tempo == 90.0
        assert params.music_energy == 0.4
        assert params.generation == 0
    
    def test_to_vector(self):
        """Test converting to optimization vector."""
        params = BrandParameters(
            id="params-123",
            music_tempo=90.0,
            music_energy=0.5,
        )
        
        vector = params.to_vector()
        
        assert len(vector) == 9
        assert 0 <= vector[0] <= 1  # Normalized tempo
        assert vector[1] == 0.5  # Energy
    
    def test_from_vector(self):
        """Test creating from optimization vector."""
        base = BrandParameters(id="base", generation=5)
        vector = np.array([0.5, 0.6, 0.4, 0.5, 0.3, 0.5, 0.5, 0.7, 0.6])
        
        new_params = BrandParameters.from_vector(vector, base)
        
        assert new_params.generation == 6
        assert abs(new_params.music_energy - 0.6) < 0.001


class TestEvolutionaryLoop:
    """Tests for EvolutionaryLoop."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        config = Config()
        config.deployment_platforms = ["instagram"]
        return config
    
    @pytest.fixture
    def evolution(self, config):
        """Create Evolutionary loop."""
        return EvolutionaryLoop(config)
    
    @pytest.mark.asyncio
    async def test_initialization(self, evolution):
        """Test loop initialization."""
        await evolution.initialize()
        assert evolution._initialized
    
    @pytest.mark.asyncio
    async def test_schedule_fitness_check(self, evolution):
        """Test scheduling fitness check."""
        await evolution.initialize()
        
        await evolution.schedule_fitness_check("content-123")
        
        assert "content-123" in evolution.pending_content
    
    @pytest.mark.asyncio
    async def test_collect_engagement(self, evolution):
        """Test engagement collection."""
        await evolution.initialize()
        
        metrics = await evolution.collect_engagement("content-123", "instagram")
        
        assert metrics.content_id == "content-123"
        assert metrics.views > 0
    
    @pytest.mark.asyncio
    async def test_evaluate_fitness(self, evolution):
        """Test fitness evaluation."""
        await evolution.initialize()
        
        fitness = await evolution.evaluate_fitness("content-123")
        
        assert fitness.content_id == "content-123"
        assert fitness.total_fitness > 0
    
    @pytest.mark.asyncio
    async def test_evolve_parameters(self, evolution):
        """Test parameter evolution."""
        await evolution.initialize()
        
        # Create triggering fitness
        fitness = FitnessScore(
            content_id="test-123",
            like_score=0.2,
            share_score=0.1,
            watch_score=0.9,
            historical_average=0.0,
        )
        
        initial_gen = evolution.current_params.generation
        new_params = await evolution.evolve_parameters(fitness)
        
        assert new_params.generation == initial_gen + 1
