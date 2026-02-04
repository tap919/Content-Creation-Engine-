"""Tests for the Production Hive."""

import pytest
from pathlib import Path

from src.hive.models import (
    AgentResult, AgentRole,
    ImageVariation, HiveReward
)
from src.hive.agents import VisualistAgent
from src.hive.hive import ProductionHive
from src.sentinel.models import CreativeBrief
from src.utils.config import Config


class TestAgentResult:
    """Tests for AgentResult model."""
    
    def test_agent_result_creation(self):
        """Test creating an AgentResult."""
        result = AgentResult(
            agent_role=AgentRole.VISUALIST,
            success=True,
            quality_score=0.85,
        )
        
        assert result.agent_role == AgentRole.VISUALIST
        assert result.success
        assert result.quality_score == 0.85


class TestImageVariation:
    """Tests for ImageVariation model."""
    
    def test_image_variation_creation(self):
        """Test creating an ImageVariation."""
        variation = ImageVariation(
            id="img-123",
            path=Path("/tmp/test.png"),
            prompt_used="test prompt",
            brand_alignment_score=0.9,
        )
        
        assert variation.id == "img-123"
        assert variation.brand_alignment_score == 0.9
        assert not variation.selected


class TestHiveReward:
    """Tests for HiveReward calculation."""
    
    def test_reward_calculation(self):
        """Test hive reward calculation."""
        reward = HiveReward(
            content_id="test-123",
            clip_similarity=0.8,
            music_perturbation_penalty=0.2,
            text_perturbation_penalty=0.1,
        )
        
        # r = 0.8 - 0.1*0.2 - 0.1*0.1 = 0.8 - 0.02 - 0.01 = 0.77
        expected = 0.8 - 0.1 * 0.2 - 0.1 * 0.1
        assert abs(reward.total_reward - expected) < 0.001


class TestVisualistAgent:
    """Tests for VisualistAgent."""
    
    @pytest.fixture
    def config(self, tmp_path):
        """Create test configuration."""
        config = Config()
        config.output_dir = str(tmp_path)
        return config
    
    @pytest.fixture
    def agent(self, config):
        """Create Visualist agent."""
        return VisualistAgent(config, num_variations=3)
    
    @pytest.fixture
    def brief(self):
        """Create test brief."""
        return CreativeBrief(
            id="brief-123",
            trend_id="trend-123",
            topic="CRISPR",
            headline="Breaking: CRISPR Update",
            summary="Test summary",
        )
    
    @pytest.mark.asyncio
    async def test_initialization(self, agent):
        """Test agent initialization."""
        await agent.initialize()
        assert agent._initialized
    
    @pytest.mark.asyncio
    async def test_execute(self, agent, brief):
        """Test image generation."""
        await agent.initialize()
        
        result = await agent.execute(brief)
        
        assert result.success
        assert result.agent_role == AgentRole.VISUALIST
        assert len(result.output_paths) == 3


class TestProductionHive:
    """Tests for ProductionHive orchestrator."""
    
    @pytest.fixture
    def config(self, tmp_path):
        """Create test configuration."""
        config = Config()
        config.output_dir = str(tmp_path)
        return config
    
    @pytest.fixture
    def hive(self, config):
        """Create Production Hive."""
        return ProductionHive(config)
    
    @pytest.fixture
    def brief(self):
        """Create test brief."""
        return CreativeBrief(
            id="brief-123",
            trend_id="trend-123",
            topic="CRISPR",
            headline="Breaking: CRISPR Update",
            summary="Test summary",
        )
    
    @pytest.mark.asyncio
    async def test_initialization(self, hive):
        """Test hive initialization."""
        await hive.initialize()
        assert hive._initialized
    
    @pytest.mark.asyncio
    async def test_produce(self, hive, brief):
        """Test content production pipeline."""
        await hive.initialize()
        
        content = await hive.produce(brief)
        
        assert content is not None
        assert content.id is not None
        assert content.brief_id == brief.id
        assert content.overall_quality_score > 0
        assert len(content.agent_results) == 4  # All 4 agents
