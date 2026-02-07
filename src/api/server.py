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


class CampaignCreateRequest(BaseModel):
    """Request model for creating a campaign."""
    name: str = Field(..., min_length=1, max_length=200, description="Campaign name")
    goal: Optional[str] = Field(default=None, max_length=1000, description="Campaign goal")
    audience: Optional[str] = Field(default=None, max_length=500, description="Target audience")
    platforms: List[str] = Field(default_factory=list, description="Target platforms")
    contentCount: Optional[int] = Field(default=10, ge=1, le=100, description="Number of content pieces")
    contentTypes: Optional[List[str]] = Field(default_factory=list, description="Types of content to create")
    tone: Optional[str] = Field(default="professional", description="Content tone")
    startDate: Optional[str] = Field(default=None, description="Campaign start date")
    endDate: Optional[str] = Field(default=None, description="Campaign end date")
    frequency: Optional[str] = Field(default="every-other-day", description="Publishing frequency")
    autoPublish: Optional[bool] = Field(default=False, description="Auto-publish content")


class CampaignUpdateRequest(BaseModel):
    """Request model for updating a campaign."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=200, description="Campaign name")
    goal: Optional[str] = Field(default=None, max_length=1000, description="Campaign goal")
    audience: Optional[str] = Field(default=None, max_length=500, description="Target audience")
    platforms: Optional[List[str]] = Field(default=None, description="Target platforms")
    contentCount: Optional[int] = Field(default=None, ge=1, le=100, description="Number of content pieces")
    tone: Optional[str] = Field(default=None, description="Content tone")
    startDate: Optional[str] = Field(default=None, description="Campaign start date")
    endDate: Optional[str] = Field(default=None, description="Campaign end date")
    frequency: Optional[str] = Field(default=None, description="Publishing frequency")
    autoPublish: Optional[bool] = Field(default=None, description="Auto-publish content")
    status: Optional[str] = Field(default=None, description="Campaign status")


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
    
    # Campaign workflow endpoints
    @app.get("/api/campaigns")
    async def list_campaigns():
        """
        List all campaigns.
        
        Returns demo campaign data. In production, this would fetch from a database.
        """
        return {
            "campaigns": [
                {
                    "id": "camp-001",
                    "name": "Product Launch - AI Tool v2.0",
                    "status": "running",
                    "content_count": 12,
                    "published_count": 8,
                    "platforms": ["youtube", "instagram", "tiktok", "twitter"],
                    "start_date": "2024-01-15",
                    "end_date": "2024-02-15",
                    "progress": 65
                },
                {
                    "id": "camp-002",
                    "name": "Educational Series - AI Basics",
                    "status": "scheduled",
                    "content_count": 8,
                    "published_count": 0,
                    "platforms": ["youtube", "linkedin", "twitter"],
                    "start_date": "2024-02-01",
                    "end_date": "2024-02-28",
                    "progress": 0
                }
            ]
        }
    
    @app.post("/api/campaigns")
    async def create_campaign(campaign: CampaignCreateRequest):
        """
        Create a new campaign workflow.
        
        Accepts campaign configuration and sets up automated content generation pipeline.
        """
        campaign_id = str(uuid.uuid4())[:8]
        
        logger.info(
            "Campaign created",
            campaign_id=campaign_id,
            name=campaign.name,
            platforms=campaign.platforms
        )
        
        return {
            "status": "success",
            "campaign_id": f"camp-{campaign_id}",
            "message": f"Campaign '{campaign.name}' created successfully"
        }
    
    @app.get("/api/campaigns/{campaign_id}")
    async def get_campaign(campaign_id: str):
        """Get details of a specific campaign."""
        # Demo response
        return {
            "id": campaign_id,
            "name": "Demo Campaign",
            "status": "running",
            "content_count": 10,
            "published_count": 5,
            "progress": 50,
            "content_items": [
                {"id": "content-1", "type": "video", "status": "published", "platform": "youtube"},
                {"id": "content-2", "type": "image", "status": "published", "platform": "instagram"},
                {"id": "content-3", "type": "video", "status": "scheduled", "platform": "tiktok"}
            ]
        }
    
    @app.patch("/api/campaigns/{campaign_id}")
    async def update_campaign(campaign_id: str, updates: CampaignUpdateRequest):
        """Update campaign settings."""
        updated_fields = {k: v for k, v in updates.model_dump().items() if v is not None}
        logger.info("Campaign updated", campaign_id=campaign_id, updates=list(updated_fields.keys()))
        return {"status": "success", "campaign_id": campaign_id, "updated": updated_fields}
    
    @app.delete("/api/campaigns/{campaign_id}")
    async def delete_campaign(campaign_id: str):
        """Delete a campaign."""
        logger.info("Campaign deleted", campaign_id=campaign_id)
        return {"status": "success", "message": f"Campaign {campaign_id} deleted"}
    
    # Brand DNA endpoints
    @app.get("/api/brand")
    async def get_brand_dna(factory: dict = Depends(get_factory)):
        """Get current brand DNA configuration."""
        config = factory["config"]
        return {
            "colors": {
                "primary": config.brand_dna.primary_color,
                "secondary": config.brand_dna.secondary_color,
                "accent": config.brand_dna.accent_color,
                "background": config.brand_dna.background_color,
                "text": config.brand_dna.text_color,
            },
            "fonts": {
                "primary": config.brand_dna.primary_font,
                "secondary": config.brand_dna.secondary_font,
            },
            "logo": {
                "url": config.brand_dna.logo_url,
                "position": config.brand_dna.logo_position,
            },
            "tone": {
                "voice": config.brand_dna.tone_of_voice,
                "style": config.brand_dna.content_style,
            },
            "visual": {
                "animation": config.brand_dna.animation_style,
                "transition": config.brand_dna.transition_style,
            }
        }
    
    @app.post("/api/brand")
    async def update_brand_dna(brand_data: dict, factory: dict = Depends(get_factory)):
        """Update brand DNA configuration."""
        logger.info("Brand DNA update requested", fields=list(brand_data.keys()))
        
        # Apply updates to in-memory config so subsequent GETs reflect the change
        config = factory["config"]
        brand_dna = config.brand_dna
        
        # Update brand DNA fields
        for key, value in brand_data.items():
            if hasattr(brand_dna, key):
                setattr(brand_dna, key, value)
        
        # In production, this would persist to database
        return {"status": "success", "updated": brand_data}
    
    class RepurposeRequest(BaseModel):
        """Request model for content repurposing."""
        content_id: str = Field(..., description="ID of content to repurpose")
        platforms: List[str] = Field(..., description="Target platforms")
    
    # Content Repurposing endpoints
    @app.post("/api/repurpose")
    async def repurpose_content(
        request: RepurposeRequest,
        factory: dict = Depends(get_factory)
    ):
        """Repurpose content for multiple platforms."""
        logger.info(
            "Content repurposing requested",
            content_id=request.content_id,
            platforms=request.platforms
        )
        
        # In production, would use actual repurposing service
        return {
            "status": "success",
            "content_id": request.content_id,
            "platforms": request.platforms,
            "variants_created": len(request.platforms)
        }
    
    # Creative Spark endpoints
    @app.post("/api/ideas/generate")
    async def generate_ideas(
        niche: str,
        content_type: str = "video",
        num_ideas: int = 5
    ):
        """Generate creative content ideas."""
        logger.info(
            "Idea generation requested",
            niche=niche,
            type=content_type,
            count=num_ideas
        )
        
        # Placeholder response - in production would use CreativeSparkService
        ideas = []
        for i in range(num_ideas):
            ideas.append({
                "id": f"idea_{i+1}",
                "title": f"Creative idea {i+1} for {niche}",
                "hook": f"Engaging hook for {niche} content",
                "format": "educational",
                "estimated_time": "30-60 seconds"
            })
        
        return {
            "status": "success",
            "niche": niche,
            "ideas": ideas
        }
    
    class HooksRequest(BaseModel):
        """Request model for hook generation."""
        topic: str = Field(..., description="Topic for hook generation")
        platform: str = Field(default="tiktok", description="Target platform")
        num_hooks: int = Field(default=5, ge=1, le=20, description="Number of hooks to generate")
    
    @app.post("/api/ideas/hooks")
    async def generate_hooks(request: HooksRequest):
        """Generate engaging hooks for a topic."""
        topic = request.topic
        platform = request.platform
        num_hooks = request.num_hooks
        logger.info("Hook generation requested", topic=topic, platform=platform)
        
        hooks = [
            f"Wait, you didn't know this about {topic}?",
            f"POV: You just discovered {topic}",
            f"Nobody talks about this {topic} secret...",
            f"Stop doing {topic} wrong! Here's why...",
            f"This {topic} hack changed everything"
        ]
        
        return {
            "status": "success",
            "topic": topic,
            "platform": platform,
            "hooks": hooks[:num_hooks]
        }
    
    @app.post("/api/ideas/outline")
    async def generate_script_outline(idea_id: str):
        """Generate a script outline for an idea."""
        logger.info("Script outline requested", idea_id=idea_id)
        
        return {
            "status": "success",
            "idea_id": idea_id,
            "outline": {
                "hook": "Grab attention in first 3 seconds",
                "structure": [
                    {"section": "Problem", "content": "Identify the issue"},
                    {"section": "Solution", "content": "Present the answer"},
                    {"section": "Example", "content": "Show real application"},
                    {"section": "CTA", "content": "Call to action"}
                ],
                "visual_cues": [
                    "Use on-screen text for key points",
                    "Show B-roll footage",
                    "Add captions for accessibility"
                ]
            }
        }
    
    # Avatar endpoints
    @app.post("/api/avatar/create")
    async def create_avatar(
        photos: List[UploadFile] = File(...),
        style: str = "realistic"
    ):
        """Create avatar from uploaded photos."""
        logger.info("Avatar creation requested", num_photos=len(photos), style=style)
        
        return {
            "status": "success",
            "avatar_id": f"avatar_{uuid.uuid4().hex[:8]}",
            "style": style,
            "training_status": "processing"
        }
    
    @app.get("/api/avatars")
    async def list_avatars():
        """List all created avatars."""
        return {
            "avatars": [
                {
                    "id": "avatar_001",
                    "name": "Professional Avatar",
                    "style": "realistic",
                    "status": "ready",
                    "created_at": "2024-01-15T10:00:00Z"
                },
                {
                    "id": "avatar_002",
                    "name": "Casual Avatar",
                    "style": "animated",
                    "status": "ready",
                    "created_at": "2024-01-20T14:30:00Z"
                }
            ]
        }
    
    @app.post("/api/avatar/{avatar_id}/generate")
    async def generate_avatar_video(
        avatar_id: str,
        script: str,
        background: str = "default"
    ):
        """Generate video with avatar."""
        logger.info(
            "Avatar video generation requested",
            avatar_id=avatar_id,
            script_length=len(script)
        )
        
        return {
            "status": "success",
            "avatar_id": avatar_id,
            "job_id": str(uuid.uuid4()),
            "video_url": f"/output/avatars/{avatar_id}_video.mp4"
        }
    
    return app
