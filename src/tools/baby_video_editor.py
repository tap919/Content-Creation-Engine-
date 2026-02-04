"""
Baby Video Editor - Simple CapCut alternative

Provides video editing capabilities using FFmpeg and MoviePy:
- Quick video editing and trimming
- Caption/subtitle overlay
- Clip concatenation with transitions
- Platform-specific resizing
- Music/audio overlay
"""

import subprocess
import uuid
from pathlib import Path
from typing import Optional, List, Dict
import structlog

logger = structlog.get_logger(__name__)

try:
    from moviepy.editor import (
        VideoFileClip,
        TextClip,
        CompositeVideoClip,
        concatenate_videoclips,
        AudioFileClip,
    )
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    logger.warning("MoviePy not available. Install with: pip install moviepy")


class BabyCapCut:
    """
    Simple CapCut alternative for quick video editing.
    
    Provides:
    - Video trimming and cutting
    - Caption/subtitle overlay
    - Concatenate clips with transitions
    - Resize for social platforms
    - Add background music
    """
    
    PLATFORM_SIZES = {
        'tiktok': (1080, 1920),
        'instagram_reel': (1080, 1920),
        'youtube_short': (1080, 1920),
        'youtube_video': (1920, 1080),
        'instagram_feed': (1080, 1080),
    }
    
    def __init__(
        self,
        output_dir: str = "./output/videos",
        ffmpeg_path: str = "ffmpeg"
    ):
        """
        Initialize Baby CapCut tool.
        
        Args:
            output_dir: Directory for output files
            ffmpeg_path: Path to ffmpeg executable
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.ffmpeg_path = ffmpeg_path
        
        if not MOVIEPY_AVAILABLE:
            logger.warning("MoviePy not available - some features will be disabled")
    
    @property
    def available(self) -> bool:
        """Check if tool is available."""
        return MOVIEPY_AVAILABLE
    
    def trim_video(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Trim video to specified time range using FFmpeg for speed.
        
        Args:
            video_path: Input video path
            start_time: Start time in seconds
            end_time: End time in seconds
            output_path: Output path
            
        Returns:
            Path to trimmed video or None if failed
        """
        try:
            if output_path is None:
                output_path = str(
                    self.output_dir / f"trimmed_{uuid.uuid4().hex[:8]}.mp4"
                )
            
            duration = end_time - start_time
            
            cmd = [
                self.ffmpeg_path, '-y',
                '-i', video_path,
                '-ss', str(start_time),
                '-t', str(duration),
                '-c', 'copy',  # Copy codec for fast processing
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                logger.error("FFmpeg trim failed", stderr=result.stderr)
                return None
            
            logger.info("Video trimmed", input=video_path, output=output_path)
            return output_path
            
        except Exception as e:
            logger.error("Trim video failed", error=str(e))
            return None
    
    def add_captions(
        self,
        video_path: str,
        captions: List[Dict],
        output_path: Optional[str] = None,
        font_size: int = 50,
        font_color: str = 'white',
    ) -> Optional[str]:
        """
        Add captions/subtitles to video.
        
        Args:
            video_path: Input video path
            captions: List of caption dicts with 'text', 'start', 'end'
            output_path: Output path
            font_size: Font size for captions
            font_color: Font color
            
        Returns:
            Path to captioned video or None if failed
        """
        if not MOVIEPY_AVAILABLE:
            logger.error("MoviePy not available")
            return None
        
        video = None
        txt_clips = []
        final = None
        
        try:
            video = VideoFileClip(video_path)
            clips = [video]
            
            for caption in captions:
                txt_clip = TextClip(
                    caption['text'],
                    fontsize=font_size,
                    color=font_color,
                    stroke_color='black',
                    stroke_width=2,
                    method='caption',
                    size=(int(video.w * 0.9), None)
                )
                txt_clip = txt_clip.set_position(('center', 0.8), relative=True)
                txt_clip = txt_clip.set_start(caption['start'])
                
                duration = caption['end'] - caption['start']
                txt_clip = txt_clip.set_duration(duration)
                
                txt_clips.append(txt_clip)
                clips.append(txt_clip)
            
            final = CompositeVideoClip(clips)
            
            if output_path is None:
                output_path = str(
                    self.output_dir / f"captioned_{uuid.uuid4().hex[:8]}.mp4"
                )
            
            # Use unique temp audio file to avoid collisions
            temp_audio = str(self.output_dir / f"temp-audio-{uuid.uuid4().hex[:8]}.m4a")
            
            final.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile=temp_audio,
                remove_temp=True
            )
            
            logger.info("Captions added", input=video_path, output=output_path)
            return output_path
            
        except Exception as e:
            logger.error("Add captions failed", error=str(e))
            return None
        finally:
            # Clean up
            for clip in txt_clips:
                try:
                    clip.close()
                except Exception as e:
                    logger.warning("Failed to close text clip during cleanup", error=str(e))
            if final:
                try:
                    final.close()
                except Exception as e:
                    logger.warning("Failed to close final composite clip during cleanup", error=str(e))
            if video:
                try:
                    video.close()
                except Exception as e:
                    logger.warning("Failed to close video clip during cleanup", error=str(e))
    
    def resize_for_platform(
        self,
        video_path: str,
        platform: str,
        output_path: Optional[str] = None,
        crop: bool = True,
    ) -> Optional[str]:
        """
        Resize video for specific social media platform.
        
        Args:
            video_path: Input video path
            platform: Platform name (tiktok, instagram_reel, etc.)
            output_path: Output path
            crop: Whether to crop or letterbox
            
        Returns:
            Path to resized video or None if failed
        """
        try:
            dimensions = self.PLATFORM_SIZES.get(platform, (1080, 1920))
            width, height = dimensions
            
            if output_path is None:
                output_path = str(
                    self.output_dir / f"{platform}_{uuid.uuid4().hex[:8]}.mp4"
                )
            
            if crop:
                # Crop to exact size (may cut edges)
                filter_str = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"
            else:
                # Letterbox (add black bars if needed)
                filter_str = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
            
            cmd = [
                self.ffmpeg_path, '-y',
                '-i', video_path,
                '-vf', filter_str,
                '-c:a', 'copy',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                logger.error("FFmpeg resize failed", stderr=result.stderr)
                return None
            
            logger.info("Video resized", platform=platform, output=output_path)
            return output_path
            
        except Exception as e:
            logger.error("Resize for platform failed", error=str(e))
            return None
    
    def concatenate_videos(
        self,
        video_paths: List[str],
        output_path: Optional[str] = None,
        transition_duration: float = 0.5,
    ) -> Optional[str]:
        """
        Concatenate multiple videos with crossfade transitions.
        
        Args:
            video_paths: List of video paths
            output_path: Output path
            transition_duration: Duration of crossfade in seconds
            
        Returns:
            Path to concatenated video or None if failed
        """
        if not MOVIEPY_AVAILABLE:
            logger.error("MoviePy not available")
            return None
        
        clips = []
        final = None
        
        try:
            # Load all clips
            clips = [VideoFileClip(path) for path in video_paths]
            
            # Apply crossfade to all clips except first
            final_clips = [clips[0]]
            for clip in clips[1:]:
                final_clips.append(clip.crossfadein(transition_duration))
            
            # Concatenate
            final = concatenate_videoclips(final_clips, method='compose')
            
            if output_path is None:
                output_path = str(
                    self.output_dir / f"concatenated_{uuid.uuid4().hex[:8]}.mp4"
                )
            
            # Use unique temp audio file to avoid collisions
            temp_audio = str(self.output_dir / f"temp-audio-{uuid.uuid4().hex[:8]}.m4a")
            
            final.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile=temp_audio,
                remove_temp=True
            )
            
            logger.info("Videos concatenated", count=len(video_paths), output=output_path)
            return output_path
            
        except Exception as e:
            logger.error("Concatenate videos failed", error=str(e))
            return None
        finally:
            # Clean up
            if final:
                try:
                    final.close()
                except Exception as e:
                    logger.debug("Failed to close final concatenated clip", error=str(e), exc_info=True)
            for clip in clips:
                try:
                    clip.close()
                except Exception as e:
                    logger.debug("Failed to close video clip during cleanup", error=str(e), exc_info=True)
    
    def add_background_music(
        self,
        video_path: str,
        audio_path: str,
        output_path: Optional[str] = None,
        audio_volume: float = 0.3,
    ) -> Optional[str]:
        """
        Add background music to video, mixing with existing audio.
        
        Args:
            video_path: Input video path
            audio_path: Background music path
            output_path: Output path
            audio_volume: Background music volume (0-1)
            
        Returns:
            Path to output video or None if failed
        """
        if not MOVIEPY_AVAILABLE:
            logger.error("MoviePy not available")
            return None
        
        video = None
        background_music = None
        final = None
        
        try:
            video = VideoFileClip(video_path)
            background_music = AudioFileClip(audio_path)
            
            # Loop music if shorter than video
            if background_music.duration < video.duration:
                n_loops = int(video.duration / background_music.duration) + 1
                background_music = background_music.loop(n=n_loops)
            
            # Trim music to video length
            background_music = background_music.subclip(0, video.duration)
            
            # Adjust volume
            background_music = background_music.volumex(audio_volume)
            
            # Mix with original audio if exists
            if video.audio:
                from moviepy.audio.AudioClip import CompositeAudioClip
                final_audio = CompositeAudioClip([video.audio, background_music])
            else:
                final_audio = background_music
            
            # Set audio to video
            final = video.set_audio(final_audio)
            
            if output_path is None:
                output_path = str(
                    self.output_dir / f"with_music_{uuid.uuid4().hex[:8]}.mp4"
                )
            
            final.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile=f"temp-audio-{uuid.uuid4().hex}.m4a",
                remove_temp=True
            )
            
            logger.info("Background music added", output=output_path)
            return output_path
            
        except Exception as e:
            logger.error("Add background music failed", error=str(e))
            return None
        finally:
            # Clean up
            if final:
                try:
                    final.close()
                except Exception as e:
                    logger.debug("Failed to close final video clip", error=str(e))
            if video:
                try:
                    video.close()
                except Exception as e:
                    logger.debug("Failed to close video clip", error=str(e))
            if background_music:
                try:
                    background_music.close()
                except Exception as e:
                    logger.debug("Failed to close background music clip", error=str(e))
    
    def speed_up_video(
        self,
        video_path: str,
        speed_factor: float = 2.0,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Speed up or slow down video.
        
        Args:
            video_path: Input video path
            speed_factor: Speed multiplier (2.0 = 2x faster, 0.5 = 2x slower)
            output_path: Output path
            
        Returns:
            Path to output video or None if failed
        """
        try:
            # Validate speed_factor
            if speed_factor <= 0:
                logger.error("Invalid speed_factor", value=speed_factor)
                return None
            
            if speed_factor < 0.1 or speed_factor > 10.0:
                logger.warning("Speed factor out of recommended range (0.1-10.0)", value=speed_factor)
            
            if output_path is None:
                output_path = str(
                    self.output_dir / f"speed_{speed_factor}x_{uuid.uuid4().hex[:8]}.mp4"
                )
            
            # FFmpeg uses PTS (presentation timestamp) for speed
            # setpts for video, atempo for audio
            pts_value = 1.0 / speed_factor
            
            # Audio tempo can only be 0.5-2.0, so chain if needed
            audio_filter = self._get_audio_tempo_filter(speed_factor)
            
            # Try with audio first; if it fails (no audio stream), try video only
            cmd = [
                self.ffmpeg_path, '-y',
                '-i', video_path,
                '-filter_complex',
                f"[0:v]setpts={pts_value}*PTS[v];[0:a]{audio_filter}[a]",
                '-map', '[v]',
                '-map', '[a]',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            # If it failed due to no audio, try video-only
            if result.returncode != 0 and ('does not contain any stream' in result.stderr or 
                                          'matches no streams' in result.stderr):
                logger.info("No audio stream detected, processing video only")
                cmd = [
                    self.ffmpeg_path, '-y',
                    '-i', video_path,
                    '-filter:v', f"setpts={pts_value}*PTS",
                    '-an',  # No audio
                    output_path
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                logger.error("FFmpeg speed change failed", stderr=result.stderr)
                return None
            
            logger.info("Video speed changed", factor=speed_factor, output=output_path)
            return output_path
            
        except Exception as e:
            logger.error("Speed up video failed", error=str(e))
            return None
    
    def _get_audio_tempo_filter(self, speed_factor: float) -> str:
        """Generate audio tempo filter chain for speed changes."""
        if speed_factor == 1.0:
            return "anull"
        
        # atempo filter only supports 0.5-2.0 range
        # Chain multiple filters if needed
        filters = []
        remaining = speed_factor
        
        while remaining > 2.0:
            filters.append("atempo=2.0")
            remaining /= 2.0
        
        while remaining < 0.5:
            filters.append("atempo=0.5")
            remaining /= 0.5
        
        if remaining != 1.0:
            filters.append(f"atempo={remaining:.3f}")
        
        return ','.join(filters) if filters else "anull"
    
    def extract_clip(
        self,
        video_path: str,
        start_time: float,
        duration: float,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Extract a specific clip from video (alias for trim_video with duration).
        
        Args:
            video_path: Input video path
            start_time: Start time in seconds
            duration: Clip duration in seconds
            output_path: Output path
            
        Returns:
            Path to extracted clip or None if failed
        """
        return self.trim_video(video_path, start_time, start_time + duration, output_path)
