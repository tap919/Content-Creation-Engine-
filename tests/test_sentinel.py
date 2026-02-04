"""Tests for the Sentinel Layer."""

import pytest
import numpy as np

from src.sentinel.models import TrendData, CreativeBrief, TrendHistory
from src.sentinel.sentinel import SentinelLayer
from src.utils.config import Config


class TestTrendData:
    """Tests for TrendData model."""
    
    def test_trend_data_creation(self):
        """Test creating a TrendData instance."""
        trend = TrendData(
            id="test-123",
            topic="CRISPR",
            source="biotech_news",
        )
        
        assert trend.id == "test-123"
        assert trend.topic == "CRISPR"
        assert trend.source == "biotech_news"
        assert not trend.is_high_signal  # Default deviation is 0
    
    def test_high_signal_detection(self):
        """Test high signal event detection."""
        # Below threshold
        low_signal = TrendData(
            id="low",
            topic="Test",
            source="test",
            deviation_from_mean=1.5,
            threshold=2.0,
        )
        assert not low_signal.is_high_signal
        
        # Above threshold
        high_signal = TrendData(
            id="high",
            topic="Test",
            source="test",
            deviation_from_mean=2.5,
            threshold=2.0,
        )
        assert high_signal.is_high_signal


class TestCreativeBrief:
    """Tests for CreativeBrief model."""
    
    def test_brief_creation(self):
        """Test creating a CreativeBrief instance."""
        brief = CreativeBrief(
            id="brief-123",
            trend_id="trend-123",
            topic="CRISPR",
            headline="Breaking: CRISPR Update",
            summary="New developments in gene editing",
        )
        
        assert brief.id == "brief-123"
        assert brief.topic == "CRISPR"
        assert brief.target_duration_seconds == 15  # Default
        assert brief.music_mood == "lo-fi chill"  # Default
    
    def test_brief_music_parameters(self):
        """Test music parameter constraints."""
        brief = CreativeBrief(
            id="brief-123",
            trend_id="trend-123",
            topic="Test",
            headline="Test",
            summary="Test",
            music_tempo=85.0,
            music_energy=0.5,
        )
        
        assert 60.0 <= brief.music_tempo <= 180.0
        assert 0.0 <= brief.music_energy <= 1.0


class TestTrendHistory:
    """Tests for TrendHistory model."""
    
    def test_empty_history(self):
        """Test empty trend history."""
        history = TrendHistory()
        
        assert history.mean_embedding is None
        assert history.std_embedding is None
    
    def test_history_statistics(self):
        """Test computing statistics from history."""
        history = TrendHistory()
        
        # Add some trends with embeddings
        for i in range(5):
            trend = TrendData(
                id=f"trend-{i}",
                topic="Test",
                source="test",
                embedding=list(np.random.randn(512).astype(float)),
            )
            history.trends.append(trend)
        
        assert history.mean_embedding is not None
        assert len(history.mean_embedding) == 512


class TestSentinelLayer:
    """Tests for SentinelLayer."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config()
    
    @pytest.fixture
    def sentinel(self, config):
        """Create Sentinel layer instance."""
        return SentinelLayer(config)
    
    @pytest.mark.asyncio
    async def test_initialization(self, sentinel):
        """Test Sentinel layer initialization."""
        await sentinel.initialize()
        assert sentinel._initialized
    
    @pytest.mark.asyncio
    async def test_detect_trends(self, sentinel):
        """Test trend detection."""
        await sentinel.initialize()
        
        trend = await sentinel.detect_trends()
        
        assert trend is not None
        assert trend.id is not None
        assert trend.topic is not None
        assert trend.embedding is not None
    
    @pytest.mark.asyncio
    async def test_generate_brief(self, sentinel):
        """Test brief generation from trend."""
        await sentinel.initialize()
        
        trend = TrendData(
            id="test-trend",
            topic="CRISPR",
            source="test",
            deviation_from_mean=3.0,  # High signal
        )
        
        brief = await sentinel.generate_brief(trend)
        
        assert brief is not None
        assert brief.trend_id == trend.id
        assert brief.topic == trend.topic
