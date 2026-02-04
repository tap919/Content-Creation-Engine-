"""
API Server - FastAPI HTTP Interface

Provides REST API endpoints for the Agentic Content Factory.
"""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import structlog

from src.utils.config import Config
from src.sentinel import SentinelLayer
from src.hive import ProductionHive
from src.evolution import EvolutionaryLoop

logger = structlog.get_logger(__name__)

# Global factory instance
_factory = None


class ContentRequest(BaseModel):
    """Request to generate content."""
    topic: Optional[str] = None
    force_generation: bool = False


class ContentResponse(BaseModel):
    """Response from content generation."""
    content_id: str
    status: str
    topic: Optional[str] = None
    video_url: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    components: dict


class ParametersResponse(BaseModel):
    """Current brand parameters response."""
    generation: int
    music_tempo: float
    music_energy: float
    text_jargon_level: float
    fitness_average: float


def create_app(config: Config) -> FastAPI:
    """Create and configure FastAPI application."""
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifespan handler."""
        global _factory
        
        # Initialize components
        logger.info("Starting API server")
        
        _factory = {
            "config": config,
            "sentinel": SentinelLayer(config),
            "hive": ProductionHive(config),
            "evolution": EvolutionaryLoop(config),
        }
        
        await _factory["sentinel"].initialize()
        await _factory["hive"].initialize()
        await _factory["evolution"].initialize()
        
        yield
        
        # Cleanup
        logger.info("Shutting down API server")
        await _factory["sentinel"].cleanup()
        await _factory["hive"].cleanup()
        await _factory["evolution"].cleanup()
    
    app = FastAPI(
        title="Agentic Content Factory",
        description="AI-powered multi-agent content creation engine",
        version="0.1.0",
        lifespan=lifespan,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint."""
        return HealthResponse(
            status="healthy",
            version="0.1.0",
            components={
                "sentinel": "ok",
                "hive": "ok",
                "evolution": "ok",
            }
        )
    
    @app.post("/content/generate", response_model=ContentResponse)
    async def generate_content(
        request: ContentRequest,
        background_tasks: BackgroundTasks
    ):
        """
        Generate new content.
        
        Triggers a full content creation cycle:
        1. Detect trends (or use provided topic)
        2. Generate creative brief
        3. Produce content via multi-agent hive
        4. Schedule engagement tracking
        """
        if _factory is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        try:
            # Step 1: Detect trends
            sentinel = _factory["sentinel"]
            trend_data = await sentinel.detect_trends()
            
            if not trend_data.is_high_signal and not request.force_generation:
                return ContentResponse(
                    content_id="",
                    status="skipped",
                    topic=trend_data.topic,
                )
            
            # Step 2: Generate brief
            brief = await sentinel.generate_brief(trend_data)
            
            # Step 3: Produce content
            hive = _factory["hive"]
            content = await hive.produce(brief)
            
            # Step 4: Schedule engagement tracking
            evolution = _factory["evolution"]
            await evolution.schedule_fitness_check(content.id)
            
            return ContentResponse(
                content_id=content.id,
                status="success",
                topic=brief.topic,
                video_url=str(content.video_path) if content.video_path else None,
            )
            
        except Exception as e:
            logger.error("Content generation failed", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/parameters", response_model=ParametersResponse)
    async def get_parameters():
        """Get current evolved brand parameters."""
        if _factory is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        evolution = _factory["evolution"]
        params = evolution.get_current_parameters()
        
        fitness_avg = (
            sum(params.fitness_history) / len(params.fitness_history)
            if params.fitness_history else 0.0
        )
        
        return ParametersResponse(
            generation=params.generation,
            music_tempo=params.music_tempo,
            music_energy=params.music_energy,
            text_jargon_level=params.text_jargon_level,
            fitness_average=fitness_avg,
        )
    
    @app.post("/evolve")
    async def trigger_evolution():
        """Manually trigger parameter evolution."""
        if _factory is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        evolution = _factory["evolution"]
        
        # Get pending content for evaluation
        pending = list(evolution.pending_content.keys())
        
        if not pending:
            return {"status": "no_pending_content"}
        
        new_params = await evolution.run_evolution_cycle(pending)
        
        return {
            "status": "evolved",
            "new_generation": new_params.generation,
        }
    
    return app
