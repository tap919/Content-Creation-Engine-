"""
API Server - FastAPI HTTP Interface

Provides REST API endpoints for the Agentic Content Factory.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, List
import errno
import os
import shutil
import uuid

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field
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


class ApiKeysRequest(BaseModel):
    """Request model for API keys."""
    openai: Optional[str] = Field(default=None, description="OpenAI API key")
    elevenlabs: Optional[str] = Field(default=None, description="ElevenLabs API key")
    replicate: Optional[str] = Field(default=None, description="Replicate API token")
    twitter: Optional[str] = Field(default=None, description="Twitter Bearer Token")
    youtube: Optional[str] = Field(default=None, description="YouTube API key")


class PreferencesRequest(BaseModel):
    """Request model for user preferences."""
    auto_generate: Optional[bool] = Field(default=None)
    auto_post: Optional[bool] = Field(default=None)
    email_notifications: Optional[bool] = Field(default=None)
    evolution_mode: Optional[bool] = Field(default=None)
    cycle_interval: Optional[int] = Field(default=None, ge=1800, le=86400)


# Dependency to get factory instance
async def get_factory():
    """Dependency that provides the factory instance."""
    if _factory is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return _factory


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
    
    # Add CORS middleware with specific origins from config
    allowed_origins = config.gateway.cors.allowed_origins if config.gateway and config.gateway.cors else [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
        "tauri://localhost",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=config.gateway.cors.allowed_methods if config.gateway and config.gateway.cors else ["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=config.gateway.cors.allowed_headers if config.gateway and config.gateway.cors else ["Authorization", "Content-Type"],
    )
    
    # Mount static files directory
    static_path = Path(__file__).parent.parent / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    
    # Serve dashboard HTML template
    template_path = Path(__file__).parent.parent / "templates" / "dashboard.html"
    
    @app.get("/", response_class=HTMLResponse)
    async def dashboard():
        """Serve the main dashboard UI."""
        if template_path.exists():
            return FileResponse(str(template_path), media_type="text/html")
        return HTMLResponse("<h1>Dashboard template not found</h1>", status_code=404)
    
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
                    content_id="skipped",
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
            
        except HTTPException as http_exc:
            # Preserve existing HTTP errors (e.g., 4xx/5xx) raised by downstream components
            raise http_exc

        except Exception:
            # Log full traceback for debugging while returning a generic error to clients
            logger.exception("Content generation failed")
            raise HTTPException(status_code=500, detail="Internal server error")
    
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
    
    # File upload endpoint
    @app.post("/api/upload")
    async def upload_file(file: UploadFile = File(...), factory: dict = Depends(get_factory)):
        """
        Upload a file for content processing.
        
        Supports various file types: video, audio, images, documents, data files.
        """
        # Allowed file extensions
        allowed_extensions = {
            # Video
            '.mp4', '.mov', '.avi', '.mkv', '.webm',
            # Audio
            '.mp3', '.wav', '.ogg', '.flac',
            # Images
            '.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg',
            # Documents
            '.pdf', '.txt', '.doc', '.docx',
            # Data
            '.csv', '.json', '.xml'
        }
        
        # Check file extension (sanitize filename to remove any path components)
        safe_original_name = os.path.basename(file.filename) if file.filename else ''
        file_ext = Path(safe_original_name).suffix.lower() if safe_original_name else ''
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type not supported. Allowed: {', '.join(sorted(allowed_extensions))}"
            )
        
        # Create uploads directory
        upload_dir = Path(factory["config"].output_dir) / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        safe_filename = f"{file_id}{file_ext}"
        file_path = upload_dir / safe_filename
        
        # Save file with proper resource cleanup and error handling
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except PermissionError:
            logger.exception("Permission denied when saving uploaded file")
            raise HTTPException(status_code=403, detail="Permission denied")
        except OSError as e:
            logger.exception("OS error when saving uploaded file")
            if e.errno == errno.ENOSPC:
                raise HTTPException(status_code=507, detail="Insufficient storage")
            raise HTTPException(status_code=500, detail="Failed to save file")
        except Exception:
            logger.exception("Failed to save uploaded file")
            raise HTTPException(status_code=500, detail="Failed to save file")
        finally:
            await file.close()
        
        # Return only file_id, not the full file path (security)
        return {
            "status": "success",
            "file_id": file_id,
            "filename": safe_original_name,
            "content_type": file.content_type
        }
    
    # Settings endpoints
    @app.get("/api/settings")
    async def get_settings(factory: dict = Depends(get_factory)):
        """Get current application settings."""
        config = factory["config"]
        return {
            "brand_name": config.brand_name,
            "brand_aesthetic": config.brand_aesthetic,
            "cycle_interval_seconds": config.cycle_interval_seconds,
            "deployment_platforms": config.deployment_platforms,
            "trend_sources": config.trend_sources,
            "apiKeys": {
                # Only return masked versions for security
                "openai": "••••••••" if config.openai_api_key else None,
            },
            "preferences": {
                # Note: In production, these would be loaded from persistent storage
                "auto_generate": True,
                "auto_post": False,
                "email_notifications": True,
                "evolution_mode": True
            }
        }
    
    @app.post("/api/settings/api-keys")
    async def save_api_keys(keys: ApiKeysRequest):
        """
        Save API keys (handled securely server-side).
        
        Note: In production, these would be encrypted and stored securely.
        Currently a placeholder that acknowledges the save request.
        """
        # Log only the key names that were provided, not values
        provided_keys = [k for k, v in keys.model_dump().items() if v is not None]
        logger.info("API keys update requested", keys=provided_keys)
        return {"status": "success", "message": "API keys saved"}
    
    @app.patch("/api/settings/preferences")
    async def update_preferences(preferences: PreferencesRequest):
        """
        Update user preferences.
        
        Note: In production, these would be persisted to a database.
        Currently a placeholder that acknowledges the update request.
        """
        updated = {k: v for k, v in preferences.model_dump().items() if v is not None}
        logger.info("Preferences update requested", preferences=list(updated.keys()))
        return {"status": "success", "updated": updated}
    
    @app.post("/api/connections/{service}/disconnect")
    async def disconnect_service(service: str):
        """Disconnect an OAuth service."""
        logger.info("Service disconnection requested", service=service)
        return {"status": "success", "service": service, "connected": False}
    
    @app.get("/api/oauth/{service}")
    async def oauth_redirect(service: str):
        """Initiate OAuth flow for a service."""
        # Explicitly indicate that OAuth is not yet implemented for this service
        raise HTTPException(
            status_code=501,
            detail=f"OAuth integration for '{service}' is not yet implemented. "
                   "Please try again in a future version.",
        )
    
    return app
