"""
Baby Clips - Automatic highlight extraction (Opus Clip alternative)

Automatically extracts engaging clips from long videos using:
- Scene detection
- Audio transcription and sentiment analysis
- Content density analysis
"""

import subprocess
import uuid
from pathlib import Path
from typing import Optional, List, Dict
import structlog

logger = structlog.get_logger(__name__)

try:
    from scenedetect import VideoManager, SceneManager
    from scenedetect.detectors import ContentDetector
    SCENEDETECT_AVAILABLE = True
except ImportError:
    SCENEDETECT_AVAILABLE = False
    logger.warning("PySceneDetect not available. Install with: pip install scenedetect")

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("Whisper not available. Install with: pip install openai-whisper")

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    logger.warning("VADER not available. Install with: pip install vaderSentiment")


class BabyOpusClip:
    """
    Automatically extract highlight clips from long videos.
    
    Provides:
    - Scene detection
    - Sentiment-based moment detection
    - Auto-highlight extraction
    - Compilation creation
    """
    
    def __init__(
        self,
        output_dir: str = "./output/clips",
        whisper_model: str = "base",
        ffmpeg_path: str = "ffmpeg"
    ):
        """
        Initialize Baby Opus Clip tool.
        
        Args:
            output_dir: Directory for output files
            whisper_model: Whisper model size
            ffmpeg_path: Path to ffmpeg executable
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.whisper_model_name = whisper_model
        self.ffmpeg_path = ffmpeg_path
        
        self._whisper_model = None
        self._sentiment_analyzer = None
        
        if not SCENEDETECT_AVAILABLE:
            logger.warning("Scene detection will not be available")
        if not WHISPER_AVAILABLE:
            logger.warning("Transcription will not be available")
        if not VADER_AVAILABLE:
            logger.warning("Sentiment analysis will not be available")
    
    @property
    def available(self) -> bool:
        """
        Check if core highlight/transcription functionality is available.
        
        Core features (e.g., highlight extraction and engaging-moment detection)
        require Whisper, so this is True only when Whisper is available.
        """
        return WHISPER_AVAILABLE
    
    @property
    def can_detect_scenes(self) -> bool:
        """Return True if scene detection functionality is available."""
        return SCENEDETECT_AVAILABLE
    
    @property
    def can_transcribe(self) -> bool:
        """Return True if transcription functionality is available."""
        return WHISPER_AVAILABLE
    
    def _load_whisper_model(self):
        """Lazy load Whisper model."""
        if self._whisper_model is None and WHISPER_AVAILABLE:
            logger.info("Loading Whisper model", model=self.whisper_model_name)
            self._whisper_model = whisper.load_model(self.whisper_model_name)
        return self._whisper_model
    
    def _get_sentiment_analyzer(self):
        """Lazy load sentiment analyzer."""
        if self._sentiment_analyzer is None and VADER_AVAILABLE:
            self._sentiment_analyzer = SentimentIntensityAnalyzer()
        return self._sentiment_analyzer
    
    def detect_scenes(
        self,
        video_path: str,
        threshold: float = 30.0
    ) -> Optional[List[Dict]]:
        """
        Detect scene changes in video.
        
        Args:
            video_path: Path to video file
            threshold: Scene detection threshold (lower = more sensitive)
            
        Returns:
            List of scene dicts with start/end times or None if failed
        """
        if not SCENEDETECT_AVAILABLE:
            logger.error("PySceneDetect not available")
            return None
        
        video_manager = None
        try:
            video_manager = VideoManager([video_path])
            scene_manager = SceneManager()
            scene_manager.add_detector(ContentDetector(threshold=threshold))
            
            video_manager.start()
            scene_manager.detect_scenes(video_manager)
            
            scene_list = scene_manager.get_scene_list()
            
            scenes = []
            for i, (start_time, end_time) in enumerate(scene_list):
                scenes.append({
                    'index': i,
                    'start': start_time.get_seconds(),
                    'end': end_time.get_seconds(),
                    'duration': (end_time - start_time).get_seconds()
                })
            
            logger.info("Scenes detected", video=video_path, count=len(scenes))
            return scenes
            
        except Exception as e:
            logger.error("Scene detection failed", error=str(e))
            return None
        finally:
            if video_manager is not None:
                try:
                    video_manager.release()
                except Exception as e:
                    logger.warning("Failed to release video manager", error=str(e))
    
    def transcribe_video(
        self,
        video_path: str
    ) -> Optional[Dict]:
        """
        Transcribe video audio with timestamps.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Transcription dict with segments or None if failed
        """
        if not WHISPER_AVAILABLE:
            logger.error("Whisper not available")
            return None
        
        try:
            # Extract audio
            audio_path = str(self.output_dir / f"temp_audio_{uuid.uuid4().hex[:8]}.mp3")
            
            result = subprocess.run([
                self.ffmpeg_path, '-y',
                '-i', video_path,
                '-vn',
                '-acodec', 'libmp3lame',
                audio_path
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                logger.error("Audio extraction failed", stderr=result.stderr)
                return None
            
            try:
                # Transcribe
                model = self._load_whisper_model()
                result = model.transcribe(audio_path)
                
                logger.info("Video transcribed", video=video_path, segments=len(result.get('segments', [])))
                return result
                
            finally:
                # Clean up temp audio file
                Path(audio_path).unlink(missing_ok=True)
            
        except Exception as e:
            logger.error("Transcription failed", error=str(e))
            return None
    
    def find_engaging_moments(
        self,
        video_path: str,
        max_clips: int = 5,
        min_clip_length: float = 10.0,
        max_clip_length: float = 60.0
    ) -> Optional[List[Dict]]:
        """
        Find most engaging moments in video based on content analysis.
        
        Args:
            video_path: Path to video file
            max_clips: Maximum number of clips to extract
            min_clip_length: Minimum clip length in seconds
            max_clip_length: Maximum clip length in seconds
            
        Returns:
            List of moment dicts with start/end/score or None if failed
        """
        if not WHISPER_AVAILABLE:
            logger.error("Whisper not available")
            return None
        
        try:
            # Transcribe video
            transcription = self.transcribe_video(video_path)
            if not transcription:
                return None
            
            analyzer = self._get_sentiment_analyzer()
            if not analyzer:
                logger.warning("Sentiment analysis not available, using word count only")
            
            # Score each segment
            scored_segments = []
            for segment in transcription.get('segments', []):
                text = segment['text']
                start = segment['start']
                end = segment['end']
                duration = end - start
                
                # Skip if too short or too long
                if duration < min_clip_length or duration > max_clip_length:
                    continue
                
                # Calculate engagement score
                word_count = len(text.split())
                content_density = word_count / duration if duration > 0 else 0
                
                # Sentiment analysis if available
                if analyzer:
                    sentiment = analyzer.polarity_scores(text)
                    # Use absolute compound score (both positive and negative are engaging)
                    sentiment_score = abs(sentiment['compound'])
                else:
                    sentiment_score = 0.5  # Neutral if not available
                
                # Combined score
                engagement_score = (
                    sentiment_score * 0.6 +  # Emotional intensity
                    min(content_density / 3.0, 1.0) * 0.4  # Content density (normalized)
                )
                
                scored_segments.append({
                    'start': start,
                    'end': end,
                    'duration': duration,
                    'text': text,
                    'score': engagement_score,
                    'word_count': word_count
                })
            
            # Sort by score and return top moments
            scored_segments.sort(key=lambda x: x['score'], reverse=True)
            top_moments = scored_segments[:max_clips]
            
            # Sort by time for easier processing
            top_moments.sort(key=lambda x: x['start'])
            
            logger.info("Engaging moments found", video=video_path, count=len(top_moments))
            return top_moments
            
        except Exception as e:
            logger.error("Find engaging moments failed", error=str(e))
            return None
    
    def extract_highlights(
        self,
        video_path: str,
        output_dir: Optional[str] = None,
        max_clips: int = 5,
        clip_length: float = 30.0,
        padding: float = 2.0
    ) -> Optional[List[str]]:
        """
        Extract highlight clips from video.
        
        Args:
            video_path: Path to video file
            output_dir: Directory for output clips
            max_clips: Maximum number of clips
            clip_length: Target clip length in seconds
            padding: Extra seconds before/after moment
            
        Returns:
            List of output clip paths or None if failed
        """
        try:
            if output_dir is None:
                output_dir = str(self.output_dir / f"highlights_{uuid.uuid4().hex[:8]}")
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Find engaging moments
            moments = self.find_engaging_moments(
                video_path,
                max_clips=max_clips,
                min_clip_length=clip_length * 0.5,
                max_clip_length=clip_length * 2
            )
            
            if not moments:
                logger.warning("No engaging moments found")
                return None
            
            # Extract each clip
            clip_paths = []
            for i, moment in enumerate(moments):
                output_path = str(Path(output_dir) / f"clip_{i+1:02d}.mp4")
                
                # Calculate clip times with padding
                start = max(0, moment['start'] - padding)
                end = moment['end'] + padding
                duration = min(clip_length, end - start)
                
                # Extract clip using FFmpeg
                result = subprocess.run([
                    self.ffmpeg_path, '-y',
                    '-i', video_path,
                    '-ss', str(start),
                    '-t', str(duration),
                    '-c:v', 'libx264',
                    '-c:a', 'aac',
                    '-preset', 'fast',
                    output_path
                ], capture_output=True, text=True, timeout=600)
                
                if result.returncode != 0:
                    logger.warning("Failed to extract clip", index=i, stderr=result.stderr)
                    continue
                
                clip_paths.append(output_path)
                logger.info("Clip extracted", index=i, output=output_path)
            
            logger.info("Highlights extracted", video=video_path, count=len(clip_paths))
            return clip_paths
            
        except Exception as e:
            logger.error("Extract highlights failed", error=str(e))
            return None
    
    def create_compilation(
        self,
        clip_paths: List[str],
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create a compilation video from multiple clips.
        
        Args:
            clip_paths: List of clip paths
            output_path: Output video path
            
        Returns:
            Path to compilation video or None if failed
        """
        try:
            if not clip_paths:
                logger.error("No clips provided")
                return None
            
            if output_path is None:
                output_path = str(
                    self.output_dir / f"compilation_{uuid.uuid4().hex[:8]}.mp4"
                )
            
            # Create concat file for FFmpeg
            concat_file = str(self.output_dir / f"concat_{uuid.uuid4().hex[:8]}.txt")
            
            try:
                with open(concat_file, 'w') as f:
                    for clip_path in clip_paths:
                        f.write(f"file '{Path(clip_path).absolute()}'\n")
                
                # Concatenate using FFmpeg
                result = subprocess.run([
                    self.ffmpeg_path, '-y',
                    '-f', 'concat',
                    '-safe', '0',
                    '-i', concat_file,
                    '-c', 'copy',
                    output_path
                ], capture_output=True, text=True, timeout=600)
                
                if result.returncode != 0:
                    logger.error("FFmpeg compilation failed", stderr=result.stderr)
                    return None
                
                logger.info("Compilation created", output=output_path, clips=len(clip_paths))
                return output_path
            finally:
                # Clean up concat file
                Path(concat_file).unlink(missing_ok=True)
            
        except Exception as e:
            logger.error("Create compilation failed", error=str(e))
            return None
    
    def auto_generate_short(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        target_length: float = 30.0,
        platform: str = 'tiktok'
    ) -> Optional[str]:
        """
        Automatically generate a short-form video from long content.
        
        Args:
            video_path: Path to input video
            output_path: Output path
            target_length: Target video length in seconds
            platform: Target platform (tiktok, youtube_short, etc.)
            
        Returns:
            Path to output short video or None if failed
        """
        try:
            # Find best moment
            moments = self.find_engaging_moments(
                video_path,
                max_clips=1,
                min_clip_length=target_length * 0.8,
                max_clip_length=target_length * 1.2
            )
            
            if not moments:
                logger.warning("No suitable moment found for short")
                return None
            
            moment = moments[0]
            
            # Extract clip
            if output_path is None:
                output_path = str(
                    self.output_dir / f"short_{platform}_{uuid.uuid4().hex[:8]}.mp4"
                )
            
            start = max(0, moment['start'] - 1)
            duration = min(target_length, moment['duration'] + 2)
            
            # Platform-specific dimensions
            platform_sizes = {
                'tiktok': '1080:1920',
                'youtube_short': '1080:1920',
                'instagram_reel': '1080:1920',
            }
            size = platform_sizes.get(platform, '1080:1920')
            
            result = subprocess.run([
                self.ffmpeg_path, '-y',
                '-i', video_path,
                '-ss', str(start),
                '-t', str(duration),
                '-vf', f'scale={size}:force_original_aspect_ratio=increase,crop={size}',
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-preset', 'fast',
                output_path
            ], capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                logger.error("Short generation failed", stderr=result.stderr)
                return None
            
            logger.info("Short video generated", platform=platform, output=output_path)
            return output_path
            
        except Exception as e:
            logger.error("Auto generate short failed", error=str(e))
            return None
