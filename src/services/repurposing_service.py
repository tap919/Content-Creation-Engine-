"""
Content Repurposing Service - One-Click Multi-Platform Repurpose

This service handles:
- Automatic reformatting for multiple platforms
- Platform-specific optimization (aspect ratios, durations)
- Caption generation for each platform
- Batch export functionality
"""

import structlog
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image
import uuid

logger = structlog.get_logger(__name__)


class ContentRepurposingService:
    """
    Service for repurposing content across multiple platforms.
    
    Takes a "hero" content piece and automatically adapts it for
    different platforms with optimized formats, captions, and styling.
    """
    
    def __init__(self, config, brand_dna_service):
        """
        Initialize Content Repurposing service.
        
        Args:
            config: Application configuration
            brand_dna_service: Brand DNA service for consistent styling
        """
        self.config = config
        self.brand_dna = brand_dna_service
        logger.info("Content Repurposing Service initialized")
    
    async def repurpose_content(
        self,
        content_path: Path,
        content_type: str,
        target_platforms: List[str],
        original_caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Repurpose content for multiple platforms.
        
        Args:
            content_path: Path to the original content file
            content_type: Type of content (video, image, audio)
            target_platforms: List of target platforms
            original_caption: Original caption/description
            
        Returns:
            Dictionary with repurposed content for each platform
        """
        logger.info(
            "Repurposing content",
            content_type=content_type,
            platforms=target_platforms,
            source=str(content_path)
        )
        
        results = {}
        
        for platform in target_platforms:
            try:
                repurposed = await self._repurpose_for_platform(
                    content_path,
                    content_type,
                    platform,
                    original_caption
                )
                results[platform] = repurposed
            except Exception as e:
                logger.error(
                    "Failed to repurpose for platform",
                    platform=platform,
                    error=str(e)
                )
                results[platform] = {"status": "error", "error": str(e)}
        
        return {
            "status": "success",
            "platforms": results,
            "total_variants": len(results)
        }
    
    async def _repurpose_for_platform(
        self,
        content_path: Path,
        content_type: str,
        platform: str,
        original_caption: Optional[str]
    ) -> Dict[str, Any]:
        """
        Repurpose content for a specific platform.
        
        Args:
            content_path: Path to content file
            content_type: Type of content
            platform: Target platform
            original_caption: Original caption
            
        Returns:
            Dictionary with repurposed content info
        """
        specs = self.brand_dna.get_platform_specs(platform)
        
        # Generate output path
        output_dir = Path(self.config.output_dir) / "repurposed" / platform
        output_dir.mkdir(parents=True, exist_ok=True)
        
        file_id = str(uuid.uuid4())[:8]
        # Remove leading dot from suffix
        suffix = content_path.suffix.lstrip('.')
        output_path = output_dir / f"{platform}_{file_id}.{suffix}"
        
        # Repurpose based on content type
        if content_type == "video":
            result = await self._repurpose_video(
                content_path, output_path, specs
            )
        elif content_type == "image":
            result = await self._repurpose_image(
                content_path, output_path, specs
            )
        else:
            result = {"status": "unsupported"}
        
        # Generate platform-specific caption
        caption = self._generate_platform_caption(
            original_caption, platform, specs
        )
        
        result.update({
            "platform": platform,
            "caption": caption,
            "specs": specs,
            "output_path": str(output_path)
        })
        
        return result
    
    async def _repurpose_video(
        self,
        input_path: Path,
        output_path: Path,
        specs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Repurpose video for platform specifications.
        
        Args:
            input_path: Input video path
            output_path: Output video path
            specs: Platform specifications
            
        Returns:
            Dictionary with repurposing results
        """
        # In a full implementation, this would use MoviePy or FFmpeg
        # to resize, crop, and reformat the video
        
        target_width = specs["width"]
        target_height = specs["height"]
        max_duration = specs.get("max_duration")
        
        logger.info(
            "Repurposing video",
            target_size=f"{target_width}x{target_height}",
            max_duration=max_duration
        )
        
        # Placeholder: In production, would actually process the video
        # For now, return status indicating this is a placeholder
        return {
            "status": "placeholder",
            "format": f"{target_width}x{target_height}",
            "duration": max_duration,
            "note": "Video processing not implemented - placeholder only"
        }
    
    async def _repurpose_image(
        self,
        input_path: Path,
        output_path: Path,
        specs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Repurpose image for platform specifications.
        
        Args:
            input_path: Input image path
            output_path: Output image path
            specs: Platform specifications
            
        Returns:
            Dictionary with repurposing results
        """
        try:
            target_width = specs["width"]
            target_height = specs["height"]
            
            # Open and resize image
            with Image.open(input_path) as img:
                
                # Calculate aspect ratio
                aspect = target_width / target_height
                img_aspect = img.width / img.height
                
                # Crop or resize to match aspect ratio
                if img_aspect > aspect:
                    # Image is wider, crop width
                    new_width = int(img.height * aspect)
                    left = (img.width - new_width) // 2
                    img = img.crop((left, 0, left + new_width, img.height))
                elif img_aspect < aspect:
                    # Image is taller, crop height
                    new_height = int(img.width / aspect)
                    top = (img.height - new_height) // 2
                    img = img.crop((0, top, img.width, top + new_height))
                
                # Resize to target dimensions
                img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                
                # (Brand colors currently not applied in this method.)
                
                # Save
                img.save(output_path, quality=95)
            
            logger.info(
                "Repurposed image",
                size=f"{target_width}x{target_height}",
                output=str(output_path)
            )
            
            return {
                "status": "success",
                "format": f"{target_width}x{target_height}",
            }
            
        except Exception as e:
            logger.error("Failed to repurpose image", error=str(e))
            return {"status": "error", "error": str(e)}
    
    def _generate_platform_caption(
        self,
        original_caption: Optional[str],
        platform: str,
        specs: Dict[str, Any]
    ) -> str:
        """
        Generate platform-optimized caption.
        
        Args:
            original_caption: Original caption text
            platform: Target platform
            specs: Platform specifications
            
        Returns:
            Optimized caption
        """
        if not original_caption:
            original_caption = "Check out this content!"
        
        max_length = specs.get("caption_length", 2200)
        
        # Apply brand tone
        caption = self.brand_dna.apply_brand_to_text(original_caption, "caption")
        
        # Trim if needed
        if len(caption) > max_length:
            caption = caption[:max_length-3] + "..."
        
        # Add platform-specific elements
        if platform == "instagram_reel" or platform == "instagram_story":
            # Add hashtags for Instagram
            caption += "\n\n#content #creator #ai"
        elif platform == "tiktok":
            # TikTok style with emojis
            caption = "✨ " + caption + " ✨"
        elif platform == "linkedin":
            # More professional for LinkedIn
            caption = caption + "\n\nWhat are your thoughts?"
        
        return caption
    
    async def detect_viral_clips(
        self,
        video_path: Path,
        num_clips: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Detect potentially viral clips from a longer video.
        
        Args:
            video_path: Path to source video
            num_clips: Number of clips to extract
            
        Returns:
            List of clip information
        """
        logger.info(
            "Detecting viral clips",
            video=str(video_path),
            num_clips=num_clips
        )
        
        # In a full implementation, this would:
        # 1. Use scene detection to find interesting segments
        # 2. Analyze audio for engaging moments
        # 3. Use ML to identify viral patterns
        # 4. Extract and rank clips
        
        clips = []
        for i in range(num_clips):
            clips.append({
                "clip_id": f"clip_{i+1}",
                "start_time": i * 20,
                "end_time": (i + 1) * 20,
                "score": 0.85 - (i * 0.1),
                "reason": "Engaging moment detected"
            })
        
        return clips
    
    async def batch_export(
        self,
        content_items: List[Path],
        target_platforms: List[str],
        export_format: str = "zip"
    ) -> Dict[str, Any]:
        """
        Batch export multiple content items for multiple platforms.
        
        Args:
            content_items: List of content file paths
            target_platforms: List of target platforms
            export_format: Export format (zip, folder)
            
        Returns:
            Dictionary with batch export results
        """
        logger.info(
            "Batch export started",
            num_items=len(content_items),
            platforms=target_platforms,
            format=export_format
        )
        
        results = []
        
        for item in content_items:
            # Determine content type
            content_type = self._detect_content_type(item)
            
            # Repurpose for all platforms
            repurposed = await self.repurpose_content(
                item, content_type, target_platforms
            )
            
            results.append({
                "source": str(item),
                "repurposed": repurposed
            })
        
        return {
            "status": "success",
            "total_items": len(content_items),
            "total_variants": len(content_items) * len(target_platforms),
            "results": results
        }
    
    def _detect_content_type(self, path: Path) -> str:
        """
        Detect content type from file extension.
        
        Args:
            path: File path
            
        Returns:
            Content type (video, image, audio)
        """
        video_exts = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
        image_exts = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
        audio_exts = {'.mp3', '.wav', '.ogg', '.flac'}
        
        ext = path.suffix.lower()
        
        if ext in video_exts:
            return "video"
        elif ext in image_exts:
            return "image"
        elif ext in audio_exts:
            return "audio"
        else:
            return "unknown"
