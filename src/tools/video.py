"""
Video Processing Tools

Provides wrappers for:
- FFmpeg: Video encoding, conversion, streaming, and manipulation
- MoviePy: Python library for programmatic video editing
"""

import subprocess
import uuid
from pathlib import Path
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)

# MoviePy import (optional, gracefully handle if not installed)
try:
    from moviepy.editor import (
        VideoFileClip,
        ImageClip,
        TextClip,
        CompositeVideoClip,
        AudioFileClip,
        concatenate_videoclips,
    )

    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    logger.warning("MoviePy not available. Install with: pip install moviepy")


class FFmpegTool:
    """
    FFmpeg wrapper for video processing operations.

    Provides methods for:
    - Resizing videos for different platforms
    - Adding watermarks
    - Converting formats
    - Merging audio and video
    - Extracting audio from video
    """

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        """
        Initialize FFmpeg tool.

        Args:
            ffmpeg_path: Path to FFmpeg executable (default: "ffmpeg")
        """
        self.ffmpeg_path = ffmpeg_path

    def resize_video(
        self,
        input_path: str,
        output_path: str,
        width: int,
        height: int,
    ) -> bool:
        """
        Resize video to specified dimensions.

        Args:
            input_path: Path to input video
            output_path: Path for output video
            width: Target width
            height: Target height

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = [
                self.ffmpeg_path,
                "-y",
                "-i",
                input_path,
                "-vf",
                f"scale={width}:{height}",
                "-c:a",
                "copy",
                output_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("FFmpeg resize failed", stderr=result.stderr)
                return False
            logger.info("Video resized", input=input_path, output=output_path)
            return True
        except Exception as e:
            logger.error("FFmpeg resize error", error=str(e))
            return False

    def resize_for_instagram(self, input_path: str, output_path: str) -> bool:
        """Resize video for Instagram Reels (9:16 aspect ratio)."""
        return self.resize_video(input_path, output_path, 1080, 1920)

    def resize_for_tiktok(self, input_path: str, output_path: str) -> bool:
        """Resize video for TikTok (9:16 aspect ratio)."""
        return self.resize_video(input_path, output_path, 1080, 1920)

    def resize_for_youtube_shorts(self, input_path: str, output_path: str) -> bool:
        """Resize video for YouTube Shorts (9:16 aspect ratio)."""
        return self.resize_video(input_path, output_path, 1080, 1920)

    def add_watermark(
        self,
        video_path: str,
        watermark_path: str,
        output_path: str,
        position: str = "bottom_right",
    ) -> bool:
        """
        Add watermark to video.

        Args:
            video_path: Path to input video
            watermark_path: Path to watermark image
            output_path: Path for output video
            position: Position of watermark (bottom_right, bottom_left, top_right, top_left)

        Returns:
            True if successful, False otherwise
        """
        position_map = {
            "bottom_right": "W-w-10:H-h-10",
            "bottom_left": "10:H-h-10",
            "top_right": "W-w-10:10",
            "top_left": "10:10",
        }
        overlay_pos = position_map.get(position, position_map["bottom_right"])

        try:
            cmd = [
                self.ffmpeg_path,
                "-y",
                "-i",
                video_path,
                "-i",
                watermark_path,
                "-filter_complex",
                f"overlay={overlay_pos}",
                output_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("FFmpeg watermark failed", stderr=result.stderr)
                return False
            logger.info("Watermark added", video=video_path, output=output_path)
            return True
        except Exception as e:
            logger.error("FFmpeg watermark error", error=str(e))
            return False

    def convert_format(
        self,
        input_path: str,
        output_path: str,
        video_codec: Optional[str] = None,
        audio_codec: Optional[str] = None,
    ) -> bool:
        """
        Convert video to different format.

        Args:
            input_path: Path to input video
            output_path: Path for output video (format determined by extension)
            video_codec: Video codec (e.g., "libx264", "libx265")
            audio_codec: Audio codec (e.g., "aac", "mp3")

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = [self.ffmpeg_path, "-y", "-i", input_path]
            if video_codec:
                cmd.extend(["-c:v", video_codec])
            if audio_codec:
                cmd.extend(["-c:a", audio_codec])
            cmd.append(output_path)

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("FFmpeg convert failed", stderr=result.stderr)
                return False
            logger.info("Video converted", input=input_path, output=output_path)
            return True
        except Exception as e:
            logger.error("FFmpeg convert error", error=str(e))
            return False

    def merge_audio_video(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
    ) -> bool:
        """
        Merge separate audio and video files.

        Args:
            video_path: Path to video file (can have existing audio which will be replaced)
            audio_path: Path to audio file
            output_path: Path for output video

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = [
                self.ffmpeg_path,
                "-y",
                "-i",
                video_path,
                "-i",
                audio_path,
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-shortest",
                output_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("FFmpeg merge failed", stderr=result.stderr)
                return False
            logger.info("Audio and video merged", output=output_path)
            return True
        except Exception as e:
            logger.error("FFmpeg merge error", error=str(e))
            return False

    def extract_audio(
        self,
        video_path: str,
        output_path: str,
        audio_format: str = "mp3",
    ) -> bool:
        """
        Extract audio from video file.

        Args:
            video_path: Path to video file
            output_path: Path for output audio file
            audio_format: Output audio format

        Returns:
            True if successful, False otherwise
        """
        try:
            # Map common audio formats to their FFmpeg codec names
            codec_map = {
                "mp3": "libmp3lame",
                "aac": "aac",
                "wav": "pcm_s16le",
                "ogg": "libvorbis",
                "flac": "flac",
                "copy": "copy",
            }
            codec = codec_map.get(audio_format, audio_format)

            cmd = [
                self.ffmpeg_path,
                "-y",
                "-i",
                video_path,
                "-vn",
                "-acodec",
                codec,
                output_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("FFmpeg extract audio failed", stderr=result.stderr)
                return False
            logger.info("Audio extracted", video=video_path, output=output_path)
            return True
        except Exception as e:
            logger.error("FFmpeg extract audio error", error=str(e))
            return False

    def get_video_info(self, video_path: str) -> Optional[dict]:
        """
        Get video metadata using FFprobe.

        Args:
            video_path: Path to video file

        Returns:
            Dictionary with video metadata or None if failed
        """
        try:
            cmd = [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                video_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("FFprobe failed", stderr=result.stderr)
                return None

            import json

            return json.loads(result.stdout)
        except Exception as e:
            logger.error("FFprobe error", error=str(e))
            return None


class MoviePyTool:
    """
    MoviePy wrapper for programmatic video editing.

    Provides methods for:
    - Adding text overlays/captions to videos
    - Creating videos from images
    - Concatenating video clips
    - Adding audio to video
    """

    def __init__(self, output_dir: str = "./output"):
        """
        Initialize MoviePy tool.

        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if not MOVIEPY_AVAILABLE:
            logger.warning("MoviePy not available - some features will be disabled")

    @property
    def available(self) -> bool:
        """Check if MoviePy is available."""
        return MOVIEPY_AVAILABLE

    def add_captions(
        self,
        video_path: str,
        captions: list[dict],
        output_path: Optional[str] = None,
        font: str = "Arial",
        fontsize: int = 40,
        color: str = "white",
    ) -> Optional[str]:
        """
        Add captions to video.

        Args:
            video_path: Path to input video
            captions: List of caption dicts with 'text', 'start', 'end' keys
            output_path: Path for output video (auto-generated if None)
            font: Font name
            fontsize: Font size
            color: Text color

        Returns:
            Path to output video or None if failed
        """
        if not MOVIEPY_AVAILABLE:
            logger.error("MoviePy not available")
            return None

        try:
            video = VideoFileClip(video_path)
            clips = [video]

            for caption in captions:
                txt_clip = TextClip(
                    caption["text"],
                    fontsize=fontsize,
                    color=color,
                    font=font,
                )
                txt_clip = txt_clip.set_position(("center", "bottom"))
                txt_clip = txt_clip.set_start(caption["start"])
                txt_clip = txt_clip.set_duration(caption["end"] - caption["start"])
                clips.append(txt_clip)

            final = CompositeVideoClip(clips)

            if output_path is None:
                output_path = str(
                    self.output_dir / f"captioned_{uuid.uuid4().hex[:8]}.mp4"
                )

            final.write_videofile(output_path, codec="libx264", audio_codec="aac")
            video.close()
            final.close()

            logger.info("Captions added", input=video_path, output=output_path)
            return output_path
        except Exception as e:
            logger.error("Add captions failed", error=str(e))
            return None

    def create_video_from_image(
        self,
        image_path: str,
        duration: float,
        output_path: Optional[str] = None,
        audio_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create video from a single image.

        Args:
            image_path: Path to image file
            duration: Duration in seconds
            output_path: Path for output video
            audio_path: Optional path to audio file to add

        Returns:
            Path to output video or None if failed
        """
        if not MOVIEPY_AVAILABLE:
            logger.error("MoviePy not available")
            return None

        try:
            clip = ImageClip(image_path).set_duration(duration)

            if audio_path:
                audio = AudioFileClip(audio_path).set_duration(duration)
                clip = clip.set_audio(audio)

            if output_path is None:
                output_path = str(
                    self.output_dir / f"image_video_{uuid.uuid4().hex[:8]}.mp4"
                )

            clip.write_videofile(output_path, fps=24, codec="libx264")
            clip.close()

            logger.info("Video created from image", image=image_path, output=output_path)
            return output_path
        except Exception as e:
            logger.error("Create video from image failed", error=str(e))
            return None

    def concatenate_videos(
        self,
        video_paths: list[str],
        output_path: Optional[str] = None,
        transition: Optional[str] = None,
    ) -> Optional[str]:
        """
        Concatenate multiple video files.

        Args:
            video_paths: List of video file paths
            output_path: Path for output video
            transition: Optional transition effect (not yet implemented)

        Returns:
            Path to output video or None if failed
        """
        if not MOVIEPY_AVAILABLE:
            logger.error("MoviePy not available")
            return None

        try:
            clips = [VideoFileClip(path) for path in video_paths]
            final = concatenate_videoclips(clips, method="compose")

            if output_path is None:
                output_path = str(
                    self.output_dir / f"concatenated_{uuid.uuid4().hex[:8]}.mp4"
                )

            final.write_videofile(output_path, codec="libx264", audio_codec="aac")

            for clip in clips:
                clip.close()
            final.close()

            logger.info(
                "Videos concatenated", count=len(video_paths), output=output_path
            )
            return output_path
        except Exception as e:
            logger.error("Concatenate videos failed", error=str(e))
            return None

    def add_text_overlay(
        self,
        video_path: str,
        text: str,
        position: tuple[str, str] = ("center", "top"),
        fontsize: int = 70,
        color: str = "white",
        duration: Optional[float] = None,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Add text overlay to video.

        Args:
            video_path: Path to input video
            text: Text to overlay
            position: Position tuple (horizontal, vertical)
            fontsize: Font size
            color: Text color
            duration: Duration of text (None = full video)
            output_path: Path for output video

        Returns:
            Path to output video or None if failed
        """
        if not MOVIEPY_AVAILABLE:
            logger.error("MoviePy not available")
            return None

        try:
            video = VideoFileClip(video_path)
            txt_clip = TextClip(text, fontsize=fontsize, color=color)
            txt_clip = txt_clip.set_position(position)

            if duration is None:
                txt_clip = txt_clip.set_duration(video.duration)
            else:
                txt_clip = txt_clip.set_duration(duration)

            final = CompositeVideoClip([video, txt_clip])

            if output_path is None:
                output_path = str(
                    self.output_dir / f"overlay_{uuid.uuid4().hex[:8]}.mp4"
                )

            final.write_videofile(output_path, codec="libx264", audio_codec="aac")
            video.close()
            final.close()

            logger.info("Text overlay added", input=video_path, output=output_path)
            return output_path
        except Exception as e:
            logger.error("Add text overlay failed", error=str(e))
            return None
