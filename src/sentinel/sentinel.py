"""
Sentinel Layer - Trend Detection and Brief Generation

The Sentinel Layer acts as the "perception" layer of the content factory.
It observes the environment (trends) and generates creative briefs when
high-signal events are detected.

Implementation of: Φ(E_t; φ) and HSE detection
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Optional

import structlog
import numpy as np

from src.utils.config import Config
from .models import TrendData, CreativeBrief, TrendHistory

logger = structlog.get_logger(__name__)


class TrendScraper:
    """Scrapes trends from various sources (social media, news, forums)."""
    
    def __init__(self, config: Config):
        self.config = config
        self.sources = config.trend_sources
        
    async def scrape_biotech_news(self) -> list[dict]:
        """Scrape biotech news and trends."""
        # Placeholder for actual scraping implementation
        # In production, this would use n8n workflows or direct API calls
        logger.info("Scraping biotech news sources")
        return []
    
    async def scrape_social_sentiment(self) -> list[dict]:
        """Scrape social media for trending topics."""
        logger.info("Scraping social media sentiment")
        return []
    
    async def scrape_all(self) -> list[dict]:
        """Scrape all configured sources."""
        results = await asyncio.gather(
            self.scrape_biotech_news(),
            self.scrape_social_sentiment(),
            return_exceptions=True
        )
        
        all_trends = []
        for result in results:
            if isinstance(result, Exception):
                logger.error("Scraping error", error=str(result))
                continue
            all_trends.extend(result)
        
        return all_trends


class TrendEmbedder:
    """
    Generates embeddings for trend data.
    
    Implements: Φ(E_t; φ) where Φ is a fixed embedder
    (n8n/LangChain scraper → LLM summary → embedding)
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.embedding_dim = 512  # CLIP/BERT dimension
        self._model = None
        
    async def initialize(self):
        """Load embedding model."""
        logger.info("Initializing trend embedder")
        # In production, load sentence-transformers or CLIP model
        # self._model = SentenceTransformer('all-MiniLM-L6-v2')
        
    async def embed(self, text: str) -> list[float]:
        """
        Generate embedding vector for text.
        
        Returns:
            512-dimensional embedding vector
        """
        # Placeholder: Generate random embedding for development
        # In production, use actual embedding model
        if self._model is None:
            return list(np.random.randn(self.embedding_dim).astype(float))
        
        # return self._model.encode(text).tolist()
        return list(np.random.randn(self.embedding_dim).astype(float))


class SentinelLayer:
    """
    Main Sentinel Layer orchestrator.
    
    Coordinates trend scraping, embedding, HSE detection, and brief generation.
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.scraper = TrendScraper(config)
        self.embedder = TrendEmbedder(config)
        self.history = TrendHistory(window_days=7)
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize the Sentinel layer."""
        logger.info("Initializing Sentinel Layer")
        await self.embedder.initialize()
        self._initialized = True
        
    async def cleanup(self) -> None:
        """Cleanup resources."""
        logger.info("Cleaning up Sentinel Layer")
        
    async def detect_trends(self) -> TrendData:
        """
        Detect current trends and analyze for high-signal events.
        
        Implements the HSE detection: ||x_t - μ_hist||_2 > 2σ
        
        Returns:
            TrendData with is_high_signal property set
        """
        if not self._initialized:
            raise RuntimeError("Sentinel layer not initialized")
        
        logger.info("Starting trend detection")
        
        # Scrape current trends
        raw_trends = await self.scraper.scrape_all()
        
        # For development, generate synthetic trend if no real data
        if not raw_trends:
            raw_trends = [self._generate_synthetic_trend()]
        
        # Process the most prominent trend
        trend_text = raw_trends[0].get("text", "Synthetic biotech trend")
        trend_topic = raw_trends[0].get("topic", "CRISPR breakthrough")
        
        # Generate embedding
        embedding = await self.embedder.embed(trend_text)
        
        # Calculate deviation from historical mean
        deviation = self._calculate_deviation(embedding)
        std = self.history.std_embedding or 1.0  # Default to 1.0 if no history
        
        trend_data = TrendData(
            id=str(uuid.uuid4()),
            topic=trend_topic,
            source=raw_trends[0].get("source", "synthetic"),
            embedding=embedding,
            raw_score=raw_trends[0].get("score", 0.5),
            deviation_from_mean=deviation / std if std > 0 else deviation,
            threshold=2.0,
            keywords=raw_trends[0].get("keywords", ["biotech", "science"]),
            sentiment_score=raw_trends[0].get("sentiment", 0.0)
        )
        
        # Add to history
        self.history.trends.append(trend_data)
        self._prune_history()
        
        logger.info(
            "Trend detected",
            topic=trend_data.topic,
            is_high_signal=trend_data.is_high_signal,
            deviation=trend_data.deviation_from_mean
        )
        
        return trend_data
    
    def _calculate_deviation(self, embedding: list[float]) -> float:
        """Calculate ||x_t - μ_hist||_2."""
        embedding_arr = np.array(embedding)
        mean = self.history.mean_embedding
        
        if mean is None:
            # No history yet, consider it high signal
            return 3.0  # Above threshold
        
        return float(np.linalg.norm(embedding_arr - mean))
    
    def _prune_history(self) -> None:
        """Remove trends older than window_days."""
        cutoff = datetime.utcnow() - timedelta(days=self.history.window_days)
        self.history.trends = [
            t for t in self.history.trends 
            if t.timestamp > cutoff
        ]
    
    def _generate_synthetic_trend(self) -> dict:
        """Generate synthetic trend for development/testing."""
        topics = [
            ("CRISPR gene editing breakthrough", "CRISPR"),
            ("mRNA vaccine developments", "mRNA"),
            ("AI drug discovery advancement", "AI-Pharma"),
            ("Synthetic biology milestone", "SynBio"),
            ("Longevity research update", "Longevity"),
        ]
        topic_full, topic_short = topics[np.random.randint(len(topics))]
        
        return {
            "text": f"Breaking: {topic_full} shows promising results in latest trials",
            "topic": topic_short,
            "source": "synthetic",
            "score": np.random.uniform(0.3, 0.9),
            "keywords": ["biotech", topic_short.lower(), "research"],
            "sentiment": np.random.uniform(-0.2, 0.8)
        }
    
    async def generate_brief(self, trend: TrendData) -> CreativeBrief:
        """
        Generate creative brief from trend data.
        
        Implements: b_t = LLM(x_t, θ_brand)
        
        Args:
            trend: Detected high-signal trend
            
        Returns:
            CreativeBrief for production hive
        """
        logger.info("Generating creative brief", trend_id=trend.id)
        
        # In production, use LLM to generate brief
        # For now, create a structured brief
        
        brief = CreativeBrief(
            id=str(uuid.uuid4()),
            trend_id=trend.id,
            topic=trend.topic,
            headline=f"Breaking: {trend.topic} Update",
            summary=f"Latest developments in {trend.topic} research",
            talking_points=[
                f"Key finding in {trend.topic}",
                "Scientific implications",
                "Future applications",
            ],
            brand_aesthetic=self.config.brand_aesthetic,
            tone="informative yet engaging",
            target_duration_seconds=15,
            music_tempo=85.0,
            music_mood="lo-fi chill",
            text_length="medium",
            jargon_level=0.4,
        )
        
        logger.info("Brief generated", brief_id=brief.id, topic=brief.topic)
        return brief
