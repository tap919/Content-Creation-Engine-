"""
Social Media Service - gRPC service for social media posting and scheduling

Handles social media integrations:
- Postiz for multi-platform scheduling via REST API
- ImPosting for Instagram and Twitter automation
- InstaPy for Instagram bot automation

This service exposes a gRPC interface for the Go API Gateway.
"""

import argparse
import asyncio
import uuid
from pathlib import Path
from typing import Optional, List

import structlog

logger = structlog.get_logger(__name__)

# gRPC imports (optional, gracefully handle if not installed)
try:
    from grpc import aio

    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False
    logger.warning("gRPC not available. Install with: pip install grpcio grpcio-tools")


class SocialMediaProvider:
    """Base class for social media posting providers."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    async def post(self, **kwargs) -> dict:
        """Post content to social media."""
        raise NotImplementedError


class PostizProvider(SocialMediaProvider):
    """Postiz multi-platform scheduling provider."""

    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.postiz.com"):
        super().__init__(api_key)
        self.base_url = base_url

    async def create_post(
        self,
        content: str,
        platforms: List[str],
        media_urls: Optional[List[str]] = None,
        scheduled_at: Optional[str] = None,
    ) -> dict:
        """
        Create and schedule a post via Postiz API.
        
        Args:
            content: Post caption/text content
            platforms: List of platform names (instagram, tiktok, youtube, etc.)
            media_urls: List of media file URLs to attach
            scheduled_at: ISO 8601 timestamp for scheduling (optional, posts immediately if None)
            
        Returns:
            Response dict with post_id, status, and platform results
        """
        logger.info(
            "PostizProvider creating post",
            platforms=platforms,
            content_length=len(content),
            media_count=len(media_urls) if media_urls else 0,
        )
        # Placeholder - in production, call Postiz API:
        # POST https://api.postiz.com/public/v1/posts
        # Headers: Authorization: Bearer <api_key>
        # {
        #   "content": content,
        #   "attachments": media_urls,
        #   "platforms": platforms,
        #   "scheduledAt": scheduled_at
        # }
        
        return {
            "post_id": str(uuid.uuid4()),
            "status": "scheduled" if scheduled_at else "published",
            "platforms": {platform: {"status": "success", "url": f"https://{platform}.com/post/123"} 
                         for platform in platforms},
            "scheduled_at": scheduled_at,
            "provider": "postiz",
        }

    async def list_integrations(self) -> dict:
        """List connected social media integrations."""
        logger.info("PostizProvider listing integrations")
        # Placeholder - in production, call Postiz API:
        # GET https://api.postiz.com/public/v1/integrations
        return {
            "integrations": [
                {"platform": "instagram", "connected": True, "username": "demo_user"},
                {"platform": "tiktok", "connected": True, "username": "demo_user"},
                {"platform": "youtube", "connected": False},
            ]
        }

    async def get_post_analytics(self, post_id: str) -> dict:
        """Get analytics for a posted content."""
        logger.info("PostizProvider getting analytics", post_id=post_id)
        # Placeholder - in production, fetch from Postiz
        return {
            "post_id": post_id,
            "views": 1500,
            "likes": 250,
            "comments": 45,
            "shares": 30,
            "engagement_rate": 0.216,
        }


class ImPostingProvider(SocialMediaProvider):
    """ImPosting Django app for Instagram and Twitter automation."""

    def __init__(self, api_key: Optional[str] = None, base_url: str = "http://localhost:8001"):
        super().__init__(api_key)
        self.base_url = base_url

    async def upload_media(self, media_path: str) -> dict:
        """
        Upload media file to ImPosting.
        
        Args:
            media_path: Path to media file to upload
            
        Returns:
            Response dict with media_id and URL
        """
        logger.info("ImPostingProvider uploading media", media_path=media_path)
        # Placeholder - in production:
        # POST http://localhost:8001/api/upload
        # multipart/form-data with file
        
        return {
            "media_id": str(uuid.uuid4()),
            "media_url": f"/media/{uuid.uuid4().hex[:8]}.mp4",
            "status": "uploaded",
        }

    async def schedule_post(
        self,
        platform: str,
        post_data: dict,
        scheduled_at: str,
    ) -> dict:
        """
        Schedule a post via ImPosting.
        
        Args:
            platform: Platform name (instagram, twitter)
            post_data: Post data including media_id, caption, etc.
            scheduled_at: ISO 8601 timestamp for scheduling
            
        Returns:
            Response dict with schedule_id and status
        """
        logger.info(
            "ImPostingProvider scheduling post",
            platform=platform,
            scheduled_at=scheduled_at,
        )
        # Placeholder - in production:
        # POST http://localhost:8001/api/schedule
        # {
        #   "platform": platform,
        #   "post_data": post_data,
        #   "scheduled_at": scheduled_at
        # }
        
        return {
            "schedule_id": str(uuid.uuid4()),
            "status": "scheduled",
            "scheduled_at": scheduled_at,
            "platform": platform,
            "provider": "imposting",
        }

    async def get_oauth_url(self, platform: str, callback_url: str) -> dict:
        """Get OAuth URL for platform authentication."""
        logger.info("ImPostingProvider getting OAuth URL", platform=platform)
        # Placeholder - in production, generate OAuth URL
        return {
            "oauth_url": f"https://{platform}.com/oauth/authorize?callback={callback_url}",
            "state": str(uuid.uuid4()),
        }


class InstaPyProvider(SocialMediaProvider):
    """InstaPy Instagram automation provider."""

    async def post_photo(
        self,
        photo_path: str,
        caption: str,
        hashtags: Optional[List[str]] = None,
    ) -> dict:
        """
        Post photo to Instagram using InstaPy.
        
        Args:
            photo_path: Path to photo file
            caption: Photo caption
            hashtags: List of hashtags (without #)
            
        Returns:
            Response dict with post_id and status
        """
        logger.info(
            "InstaPyProvider posting photo",
            caption_length=len(caption),
            hashtag_count=len(hashtags) if hashtags else 0,
        )
        # Placeholder - in production:
        # from instapy import InstaPy
        # session = InstaPy(username, password)
        # session.login()
        # session.upload_photo(photo_path, caption)
        
        full_caption = caption
        if hashtags:
            full_caption += " " + " ".join(f"#{tag}" for tag in hashtags)
        
        return {
            "post_id": str(uuid.uuid4()),
            "status": "published",
            "url": f"https://instagram.com/p/{uuid.uuid4().hex[:11]}",
            "provider": "instapy",
        }

    async def post_video(
        self,
        video_path: str,
        caption: str,
        hashtags: Optional[List[str]] = None,
    ) -> dict:
        """
        Post video/reel to Instagram using InstaPy.
        
        Args:
            video_path: Path to video file
            caption: Video caption
            hashtags: List of hashtags (without #)
            
        Returns:
            Response dict with post_id and status
        """
        logger.info(
            "InstaPyProvider posting video",
            caption_length=len(caption),
            hashtag_count=len(hashtags) if hashtags else 0,
        )
        # Placeholder - in production:
        # session.upload_video(video_path, caption)
        
        full_caption = caption
        if hashtags:
            full_caption += " " + " ".join(f"#{tag}" for tag in hashtags)
        
        return {
            "post_id": str(uuid.uuid4()),
            "status": "published",
            "url": f"https://instagram.com/reel/{uuid.uuid4().hex[:11]}",
            "provider": "instapy",
        }

    async def auto_engage(
        self,
        target_hashtags: List[str],
        like_count: int = 10,
        comment_templates: Optional[List[str]] = None,
    ) -> dict:
        """
        Auto-engage with posts (like, comment, follow) based on hashtags.
        
        Args:
            target_hashtags: Hashtags to target for engagement
            like_count: Number of posts to like
            comment_templates: Optional comment templates to use
            
        Returns:
            Response dict with engagement stats
        """
        logger.info(
            "InstaPyProvider auto-engaging",
            hashtags=target_hashtags,
            like_count=like_count,
        )
        # Placeholder - in production:
        # session.like_by_tags(target_hashtags, amount=like_count)
        # session.set_do_comment(True, percentage=50)
        # session.set_comments(comment_templates)
        
        return {
            "likes": like_count,
            "comments": like_count // 2 if comment_templates else 0,
            "follows": like_count // 5,
            "status": "completed",
            "provider": "instapy",
        }


class SocialMediaServicer:
    """
    Social Media Service gRPC Implementation.

    Handles social media posting and scheduling requests from the Go API Gateway.
    Supports multiple social media platforms and posting tools.
    """

    def __init__(self, output_dir: str = "./output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize providers
        self.postiz = PostizProvider()
        self.imposting = ImPostingProvider()
        self.instapy = InstaPyProvider()

        # Job tracking
        self.jobs: dict[str, dict] = {}

        logger.info("SocialMediaServicer initialized")

    async def post_content(self, request: dict) -> dict:
        """
        Handle social media posting request.

        Args:
            request: Post request with content, platforms, media, scheduling.

        Returns:
            Post response with job_id, status, and platform results.
        """
        job_id = str(uuid.uuid4())
        provider = request.get("provider", "postiz")
        platforms = request.get("platforms", [])

        logger.info(
            "SocialMediaServicer.post_content",
            job_id=job_id,
            provider=provider,
            platforms=platforms,
        )

        # Store job
        self.jobs[job_id] = {
            "status": "processing",
            "request": request,
            "type": "social_media_post",
            "created_at": asyncio.get_event_loop().time(),
        }

        try:
            result = None

            if provider == "postiz":
                result = await self.postiz.create_post(
                    content=request.get("content", ""),
                    platforms=platforms,
                    media_urls=request.get("media_urls", []),
                    scheduled_at=request.get("scheduled_at"),
                )
            elif provider == "imposting":
                # For ImPosting, need to upload media first, then schedule
                if request.get("media_path"):
                    upload_result = await self.imposting.upload_media(
                        request.get("media_path")
                    )
                    post_data = {
                        "media_id": upload_result.get("media_id"),
                        "caption": request.get("content", ""),
                    }
                else:
                    post_data = {"caption": request.get("content", "")}

                # ImPosting handles one platform at a time
                platform = platforms[0] if platforms else "instagram"
                result = await self.imposting.schedule_post(
                    platform=platform,
                    post_data=post_data,
                    scheduled_at=request.get("scheduled_at", ""),
                )
            elif provider == "instapy":
                # InstaPy for Instagram-specific posts
                media_path = request.get("media_path", "")
                caption = request.get("content", "")
                hashtags = request.get("hashtags", [])

                if media_path.endswith((".mp4", ".mov", ".avi")):
                    result = await self.instapy.post_video(
                        video_path=media_path,
                        caption=caption,
                        hashtags=hashtags,
                    )
                else:
                    result = await self.instapy.post_photo(
                        photo_path=media_path,
                        caption=caption,
                        hashtags=hashtags,
                    )
            else:
                raise ValueError(f"Unknown provider: {provider}")

            # Update job
            self.jobs[job_id].update(
                {
                    "status": "completed",
                    "result": result,
                }
            )

            return {
                "job_id": job_id,
                "status": result.get("status", "completed"),
                "post_id": result.get("post_id", result.get("schedule_id")),
                "platforms": result.get("platforms", {}),
                "provider": result.get("provider"),
            }

        except Exception as e:
            logger.error("Social media posting failed", job_id=job_id, error=str(e))
            self.jobs[job_id]["status"] = "failed"
            self.jobs[job_id]["error"] = str(e)

            return {
                "job_id": job_id,
                "status": "failed",
                "error_message": str(e),
            }

    async def get_analytics(self, request: dict) -> dict:
        """
        Get analytics for posted content.

        Args:
            request: Analytics request with post_id and provider.

        Returns:
            Analytics response with engagement metrics.
        """
        post_id = request.get("post_id", "")
        provider = request.get("provider", "postiz")

        logger.info(
            "SocialMediaServicer.get_analytics",
            post_id=post_id,
            provider=provider,
        )

        try:
            if provider == "postiz":
                result = await self.postiz.get_post_analytics(post_id)
            else:
                # Other providers might not support analytics
                result = {
                    "post_id": post_id,
                    "error": f"Analytics not supported for provider: {provider}",
                }

            return result

        except Exception as e:
            logger.error("Analytics retrieval failed", post_id=post_id, error=str(e))
            return {
                "post_id": post_id,
                "error_message": str(e),
            }

    async def auto_engage(self, request: dict) -> dict:
        """
        Perform automated engagement (likes, comments, follows).

        Args:
            request: Engagement request with hashtags and settings.

        Returns:
            Engagement response with statistics.
        """
        job_id = str(uuid.uuid4())
        hashtags = request.get("hashtags", [])

        logger.info(
            "SocialMediaServicer.auto_engage",
            job_id=job_id,
            hashtags=hashtags,
        )

        # Store job
        self.jobs[job_id] = {
            "status": "processing",
            "request": request,
            "type": "auto_engage",
            "created_at": asyncio.get_event_loop().time(),
        }

        try:
            result = await self.instapy.auto_engage(
                target_hashtags=hashtags,
                like_count=request.get("like_count", 10),
                comment_templates=request.get("comment_templates"),
            )

            # Update job
            self.jobs[job_id].update(
                {
                    "status": "completed",
                    "result": result,
                }
            )

            return {
                "job_id": job_id,
                "status": "completed",
                "likes": result.get("likes", 0),
                "comments": result.get("comments", 0),
                "follows": result.get("follows", 0),
            }

        except Exception as e:
            logger.error("Auto-engagement failed", job_id=job_id, error=str(e))
            self.jobs[job_id]["status"] = "failed"
            self.jobs[job_id]["error"] = str(e)

            return {
                "job_id": job_id,
                "status": "failed",
                "error_message": str(e),
            }

    async def get_job_status(self, job_id: str) -> dict:
        """Get status of a social media job."""
        job = self.jobs.get(job_id)
        if not job:
            return {"job_id": job_id, "status": "not_found"}

        return {
            "job_id": job_id,
            "status": job["status"],
            "progress_percent": 100.0 if job["status"] == "completed" else 50.0,
            "error_message": job.get("error"),
        }


async def serve(port: int = 50055) -> None:
    """Run the social media service gRPC server."""
    if not GRPC_AVAILABLE:
        logger.error("gRPC not available. Cannot start social media service server.")
        return

    logger.info("Starting Social Media Service", port=port)

    # In production, this would create a service instance and register it with the
    # gRPC server using the generated gRPC bindings, for example:
    #   servicer = SocialMediaServicer()
    #   social_media_pb2_grpc.add_SocialMediaServiceServicer_to_server(servicer, server)

    # Set up and start the gRPC server
    server = aio.server()
    server.add_insecure_port(f"[::]:{port}")

    logger.info("Starting gRPC server for Social Media Service", port=port)
    await server.start()
    logger.info("Social Media Service gRPC server started", port=port)

    try:
        # Wait until the server is terminated (e.g., via signal)
        await server.wait_for_termination()
    finally:
        logger.info("Shutting down Social Media Service gRPC server", port=port)
        # Gracefully stop the server, allowing existing RPCs to finish
        await server.stop(grace=None)


def main():
    """Main entry point for social media service."""
    parser = argparse.ArgumentParser(description="Social Media Service gRPC Server")
    parser.add_argument("--port", type=int, default=50055, help="gRPC port")
    args = parser.parse_args()

    asyncio.run(serve(args.port))


if __name__ == "__main__":
    main()
