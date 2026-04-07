"""
Advanced Content Repurposing Engine.

Handles intelligent video analysis, clip detection, and multi-platform formatting.
"""

import structlog
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import json

logger = structlog.get_logger(__name__)


@dataclass
class VideoClip:
    """Represents a detected video clip."""
    start_time: float
    end_time: float
    duration: float
    score: float
    transcript: Optional[str] = None
    reason: Optional[str] = None
    platform_recommendations: List[str] = None

    def __post_init__(self):
        if self.platform_recommendations is None:
            self.platform_recommendations = []


@dataclass
class PlatformFormat:
    """Platform-specific format requirements."""
    name: str
    aspect_ratio: Tuple[int, int]
    min_duration: float
    max_duration: float
    resolution: Tuple[int, int]
    fps: int
    caption_max_length: int
    hashtags_recommended: int


# Platform format specifications
PLATFORM_FORMATS = {
    "tiktok": PlatformFormat(
        name="TikTok",
        aspect_ratio=(9, 16),
        min_duration=5,
        max_duration=60,
        resolution=(1080, 1920),
        fps=30,
        caption_max_length=2200,
        hashtags_recommended=5,
    ),
    "instagram_reels": PlatformFormat(
        name="Instagram Reels",
        aspect_ratio=(9, 16),
        min_duration=3,
        max_duration=90,
        resolution=(1080, 1920),
        fps=30,
        caption_max_length=2200,
        hashtags_recommended=5,
    ),
    "youtube_shorts": PlatformFormat(
        name="YouTube Shorts",
        aspect_ratio=(9, 16),
        min_duration=5,
        max_duration=60,
        resolution=(1080, 1920),
        fps=30,
        caption_max_length=100,
        hashtags_recommended=3,
    ),
    "youtube": PlatformFormat(
        name="YouTube",
        aspect_ratio=(16, 9),
        min_duration=60,
        max_duration=3600,
        resolution=(1920, 1080),
        fps=30,
        caption_max_length=5000,
        hashtags_recommended=15,
    ),
    "linkedin": PlatformFormat(
        name="LinkedIn",
        aspect_ratio=(1, 1),
        min_duration=3,
        max_duration=600,
        resolution=(1080, 1080),
        fps=30,
        caption_max_length=3000,
        hashtags_recommended=3,
    ),
    "twitter": PlatformFormat(
        name="Twitter/X",
        aspect_ratio=(16, 9),
        min_duration=5,
        max_duration=140,
        resolution=(1280, 720),
        fps=30,
        caption_max_length=280,
        hashtags_recommended=2,
    ),
}


class AdvancedRepurposingEngine:
    """
    Advanced engine for intelligent content repurposing.

    Features:
    - Scene detection and clip extraction
    - Sentiment and engagement prediction
    - Automatic platform-specific formatting
    - Caption generation optimized per platform
    """

    def __init__(self, config, brand_dna_service):
        """
        Initialize the Advanced Repurposing Engine.

        Args:
            config: Application configuration
            brand_dna_service: Brand DNA service for consistent styling
        """
        self.config = config
        self.brand_dna = brand_dna_service
        logger.info("Advanced Repurposing Engine initialized")

    async def detect_clips(
        self,
        video_path: Path,
        min_clip_duration: float = 5.0,
        max_clip_duration: float = 60.0,
        target_clip_count: int = 5,
    ) -> List[VideoClip]:
        """
        Detect potential viral clips from a long-form video.

        Uses scene detection, audio analysis, and sentiment scoring.

        Args:
            video_path: Path to source video
            min_clip_duration: Minimum clip duration in seconds
            max_clip_duration: Maximum clip duration in seconds
            target_clip_count: Desired number of clips to extract

        Returns:
            List of VideoClip objects sorted by score
        """
        logger.info(
            "Detecting clips in video",
            video_path=str(video_path),
            target_count=target_clip_count
        )

        clips = []

        try:
            # Step 1: Scene detection using scenedetect
            scenes = await self._detect_scenes(video_path)
            logger.info(f"Detected {len(scenes)} scenes")

            # Step 2: Analyze each scene for engagement potential
            for i, scene in enumerate(scenes):
                duration = scene["end"] - scene["start"]

                # Skip scenes that are too short or too long
                if duration < min_clip_duration or duration > max_clip_duration:
                    continue

                # Score the scene
                score = await self._score_scene(video_path, scene)

                # Create clip
                clip = VideoClip(
                    start_time=scene["start"],
                    end_time=scene["end"],
                    duration=duration,
                    score=score,
                    reason=scene.get("reason", "High engagement potential"),
                )

                clips.append(clip)

            # Step 3: Sort by score and return top clips
            clips.sort(key=lambda c: c.score, reverse=True)
            top_clips = clips[:target_clip_count]

            # Step 4: Add platform recommendations
            for clip in top_clips:
                clip.platform_recommendations = self._recommend_platforms(clip)

            logger.info(f"Selected {len(top_clips)} top clips from {len(clips)} candidates")

            return top_clips

        except Exception as e:
            logger.error("Clip detection failed", error=str(e))
            raise

    async def _detect_scenes(self, video_path: Path) -> List[Dict[str, Any]]:
        """
        Detect scene changes in video.

        Args:
            video_path: Path to video file

        Returns:
            List of scenes with start/end times
        """
        try:
            from scenedetect import open_video, SceneManager
            from scenedetect.detectors import ContentDetector

            video = open_video(str(video_path))
            scene_manager = SceneManager()
            scene_manager.add_detector(ContentDetector(threshold=27.0))

            # Detect scenes
            scene_manager.detect_scenes(video)
            scene_list = scene_manager.get_scene_list()

            scenes = []
            for i, scene in enumerate(scene_list):
                scenes.append({
                    "start": scene[0].get_seconds(),
                    "end": scene[1].get_seconds(),
                    "scene_num": i + 1,
                })

            return scenes

        except ImportError:
            logger.warning("scenedetect not installed, using fallback method")
            # Fallback: simple time-based segmentation
            return await self._fallback_segmentation(video_path)
        except Exception as e:
            logger.error("Scene detection failed", error=str(e))
            return await self._fallback_segmentation(video_path)

    async def _fallback_segmentation(self, video_path: Path) -> List[Dict[str, Any]]:
        """
        Fallback segmentation using fixed intervals.

        Args:
            video_path: Path to video file

        Returns:
            List of fixed-duration segments
        """
        from moviepy.editor import VideoFileClip

        video = VideoFileClip(str(video_path))
        duration = video.duration
        video.close()

        # Create 30-second segments
        segment_duration = 30
        scenes = []

        for i in range(0, int(duration), segment_duration):
            scenes.append({
                "start": float(i),
                "end": min(float(i + segment_duration), duration),
                "scene_num": len(scenes) + 1,
            })

        return scenes

    async def _score_scene(self, video_path: Path, scene: Dict[str, Any]) -> float:
        """
        Score a scene's engagement potential.

        Args:
            video_path: Path to video file
            scene: Scene information

        Returns:
            Score between 0 and 1
        """
        score = 0.5  # Base score

        # Duration scoring (prefer 15-45 second clips)
        duration = scene["end"] - scene["start"]
        if 15 <= duration <= 45:
            score += 0.2
        elif 10 <= duration <= 60:
            score += 0.1

        # Scene position scoring (middle scenes often have key content)
        # This would require knowing total video duration
        # For now, slight bonus for non-first scenes
        if scene.get("scene_num", 0) > 1:
            score += 0.1

        # TODO: Add audio analysis (speech rate, music presence)
        # TODO: Add visual analysis (face detection, motion)
        # TODO: Add transcript sentiment analysis

        return min(score, 1.0)

    def _recommend_platforms(self, clip: VideoClip) -> List[str]:
        """
        Recommend platforms based on clip characteristics.

        Args:
            clip: VideoClip to analyze

        Returns:
            List of recommended platform names
        """
        recommendations = []

        # Short clips (5-60s) -> TikTok, Reels, Shorts
        if 5 <= clip.duration <= 60:
            recommendations.extend(["tiktok", "instagram_reels", "youtube_shorts"])

        # Medium clips (1-3 min) -> YouTube, LinkedIn
        elif 60 < clip.duration <= 180:
            recommendations.extend(["youtube", "linkedin"])

        # Long clips -> YouTube only
        else:
            recommendations.append("youtube")

        return recommendations

    async def format_for_platform(
        self,
        video_path: Path,
        platform: str,
        output_path: Path,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Format video for specific platform requirements.

        Args:
            video_path: Path to source video
            platform: Target platform name
            output_path: Where to save formatted video
            start_time: Optional start time for clipping
            end_time: Optional end time for clipping

        Returns:
            Dictionary with formatting results
        """
        if platform not in PLATFORM_FORMATS:
            raise ValueError(f"Unknown platform: {platform}")

        platform_spec = PLATFORM_FORMATS[platform]
        logger.info(
            "Formatting video for platform",
            platform=platform,
            aspect_ratio=platform_spec.aspect_ratio
        )

        try:
            from moviepy.editor import VideoFileClip

            # Load video
            video = VideoFileClip(str(video_path))

            # Clip if needed
            if start_time is not None and end_time is not None:
                video = video.subclip(start_time, end_time)

            # Resize to platform aspect ratio
            target_width, target_height = platform_spec.resolution
            aspect_ratio = platform_spec.aspect_ratio[0] / platform_spec.aspect_ratio[1]

            # Calculate crop/resize
            video_aspect = video.w / video.h

            if abs(video_aspect - aspect_ratio) > 0.01:
                # Need to crop or pad
                if video_aspect > aspect_ratio:
                    # Video is wider, crop sides
                    new_width = int(video.h * aspect_ratio)
                    x_center = video.w / 2
                    x1 = int(x_center - new_width / 2)
                    video = video.crop(x1=x1, width=new_width)
                else:
                    # Video is taller, crop top/bottom
                    new_height = int(video.w / aspect_ratio)
                    y_center = video.h / 2
                    y1 = int(y_center - new_height / 2)
                    video = video.crop(y1=y1, height=new_height)

            # Resize to target resolution
            video = video.resize(newsize=(target_width, target_height))

            # Set FPS
            video = video.set_fps(platform_spec.fps)

            # Add brand elements (watermark, colors)
            video = await self._apply_brand_elements(video, platform)

            # Write output
            video.write_videofile(
                str(output_path),
                codec="libx264",
                audio_codec="aac",
                fps=platform_spec.fps,
                preset="medium",
            )

            video.close()

            logger.info("Video formatted successfully", output=str(output_path))

            return {
                "path": str(output_path),
                "platform": platform,
                "resolution": platform_spec.resolution,
                "aspect_ratio": platform_spec.aspect_ratio,
                "duration": end_time - start_time if start_time and end_time else None,
            }

        except Exception as e:
            logger.error("Platform formatting failed", error=str(e), platform=platform)
            raise

    async def _apply_brand_elements(self, video, platform: str):
        """
        Apply brand elements to video (watermark, colors, etc.).

        Args:
            video: MoviePy video clip
            platform: Target platform

        Returns:
            Modified video clip
        """
        # Get brand colors
        brand_colors = self.brand_dna.get_brand_colors()

        # TODO: Add watermark/logo
        # TODO: Add brand-colored borders if needed
        # TODO: Add intro/outro based on platform

        return video

    async def generate_platform_caption(
        self,
        original_caption: str,
        platform: str,
        keywords: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate platform-optimized caption.

        Args:
            original_caption: Source caption
            platform: Target platform
            keywords: Optional keywords for hashtags

        Returns:
            Dictionary with caption and metadata
        """
        if platform not in PLATFORM_FORMATS:
            raise ValueError(f"Unknown platform: {platform}")

        platform_spec = PLATFORM_FORMATS[platform]

        logger.info("Generating caption for platform", platform=platform)

        # Truncate to platform limits
        caption = original_caption[:platform_spec.caption_max_length]

        # Generate hashtags
        hashtags = await self._generate_hashtags(
            caption,
            keywords or [],
            platform_spec.hashtags_recommended
        )

        # Platform-specific formatting
        if platform == "twitter":
            # Twitter needs to be concise
            if len(caption) > 240:
                caption = caption[:237] + "..."
        elif platform in ["tiktok", "instagram_reels"]:
            # Add call-to-action
            if "follow" not in caption.lower():
                caption += "\n\nFollow for more!"
        elif platform == "linkedin":
            # Professional tone
            caption = self.brand_dna.apply_brand_to_text(caption, context="linkedin")

        # Combine caption and hashtags
        full_caption = f"{caption}\n\n{' '.join(hashtags)}"

        return {
            "caption": full_caption,
            "hashtags": hashtags,
            "platform": platform,
            "length": len(full_caption),
        }

    async def _generate_hashtags(
        self,
        text: str,
        keywords: List[str],
        count: int
    ) -> List[str]:
        """
        Generate relevant hashtags.

        Args:
            text: Text content
            keywords: Additional keywords
            count: Number of hashtags to generate

        Returns:
            List of hashtags
        """
        hashtags = []

        # Use provided keywords
        for keyword in keywords[:count]:
            hashtags.append(f"#{keyword.replace(' ', '')}")

        # TODO: Use NLP to extract additional keywords from text
        # TODO: Add trending hashtags for the platform

        # Fill with generic hashtags if needed
        generic_hashtags = ["#content", "#viral", "#fyp", "#trending"]
        while len(hashtags) < count:
            for tag in generic_hashtags:
                if tag not in hashtags:
                    hashtags.append(tag)
                    if len(hashtags) >= count:
                        break

        return hashtags[:count]

    async def batch_repurpose(
        self,
        video_path: Path,
        target_platforms: List[str],
        output_dir: Path,
        original_caption: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        One-click repurposing to multiple platforms.

        Args:
            video_path: Source video path
            target_platforms: List of target platforms
            output_dir: Directory for output files
            original_caption: Original video caption

        Returns:
            Dictionary with all repurposed content
        """
        logger.info(
            "Starting batch repurposing",
            video=str(video_path),
            platforms=target_platforms
        )

        output_dir.mkdir(parents=True, exist_ok=True)
        results = {}

        try:
            # Detect clips
            clips = await self.detect_clips(video_path)

            for platform in target_platforms:
                platform_results = []

                for i, clip in enumerate(clips):
                    # Skip if clip not recommended for this platform
                    if platform not in clip.platform_recommendations:
                        continue

                    # Format video
                    output_path = output_dir / f"{platform}_clip_{i+1}.mp4"
                    formatted = await self.format_for_platform(
                        video_path,
                        platform,
                        output_path,
                        clip.start_time,
                        clip.end_time,
                    )

                    # Generate caption
                    caption = await self.generate_platform_caption(
                        original_caption or "Check out this clip!",
                        platform,
                    )

                    platform_results.append({
                        "clip_number": i + 1,
                        "video": formatted,
                        "caption": caption,
                        "score": clip.score,
                    })

                results[platform] = platform_results

            logger.info("Batch repurposing completed", total_clips=sum(len(r) for r in results.values()))

            return {
                "status": "success",
                "platforms": results,
                "total_clips": sum(len(r) for r in results.values()),
            }

        except Exception as e:
            logger.error("Batch repurposing failed", error=str(e))
            raise
