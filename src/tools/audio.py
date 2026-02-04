"""
Audio Processing Tools

Provides wrappers for:
- Pydub: Audio manipulation (trim, adjust volume, convert formats)
- Librosa: Audio analysis and feature extraction
- Whisper: Automatic speech recognition for captions
"""

import uuid
from pathlib import Path
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)

# Pydub import (optional)
try:
    from pydub import AudioSegment
    from pydub.silence import split_on_silence

    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    logger.warning("Pydub not available. Install with: pip install pydub")

# Librosa import (optional)
try:
    import librosa
    import numpy as np

    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    logger.warning("Librosa not available. Install with: pip install librosa")

# Whisper import (optional)
try:
    import whisper

    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("Whisper not available. Install with: pip install openai-whisper")


class PydubTool:
    """
    Pydub wrapper for audio manipulation.

    Provides methods for:
    - Converting audio formats
    - Normalizing volume
    - Trimming silence
    - Merging audio files
    - Adjusting volume
    """

    def __init__(self, output_dir: str = "./output/audio"):
        """
        Initialize Pydub tool.

        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @property
    def available(self) -> bool:
        """Check if Pydub is available."""
        return PYDUB_AVAILABLE

    def convert_format(
        self,
        input_path: str,
        output_format: str,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Convert audio to different format.

        Args:
            input_path: Path to input audio file
            output_format: Target format (mp3, wav, ogg, flac)
            output_path: Path for output file (auto-generated if None)

        Returns:
            Path to output file or None if failed
        """
        if not PYDUB_AVAILABLE:
            logger.error("Pydub not available")
            return None

        try:
            audio = AudioSegment.from_file(input_path)

            if output_path is None:
                output_path = str(
                    self.output_dir / f"converted_{uuid.uuid4().hex[:8]}.{output_format}"
                )

            audio.export(output_path, format=output_format)
            logger.info(
                "Audio converted", input=input_path, output=output_path, format=output_format
            )
            return output_path
        except Exception as e:
            logger.error("Audio convert failed", error=str(e))
            return None

    def normalize(
        self,
        input_path: str,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Normalize audio volume.

        Args:
            input_path: Path to input audio file
            output_path: Path for output file (auto-generated if None)

        Returns:
            Path to output file or None if failed
        """
        if not PYDUB_AVAILABLE:
            logger.error("Pydub not available")
            return None

        try:
            audio = AudioSegment.from_file(input_path)
            normalized = audio.normalize()

            if output_path is None:
                ext = Path(input_path).suffix
                output_path = str(
                    self.output_dir / f"normalized_{uuid.uuid4().hex[:8]}{ext}"
                )

            normalized.export(output_path, format=Path(output_path).suffix[1:])
            logger.info("Audio normalized", input=input_path, output=output_path)
            return output_path
        except Exception as e:
            logger.error("Audio normalize failed", error=str(e))
            return None

    def trim_silence(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        min_silence_len: int = 500,
        silence_thresh: int = -40,
    ) -> Optional[str]:
        """
        Remove silence from audio.

        Args:
            input_path: Path to input audio file
            output_path: Path for output file
            min_silence_len: Minimum silence length in ms to consider
            silence_thresh: Silence threshold in dB

        Returns:
            Path to output file or None if failed
        """
        if not PYDUB_AVAILABLE:
            logger.error("Pydub not available")
            return None

        try:
            audio = AudioSegment.from_file(input_path)
            chunks = split_on_silence(
                audio,
                min_silence_len=min_silence_len,
                silence_thresh=silence_thresh,
            )

            if not chunks:
                logger.warning("No non-silent chunks found")
                return None

            # Concatenate non-silent chunks
            result = chunks[0]
            for chunk in chunks[1:]:
                result += chunk

            if output_path is None:
                ext = Path(input_path).suffix
                output_path = str(
                    self.output_dir / f"trimmed_{uuid.uuid4().hex[:8]}{ext}"
                )

            result.export(output_path, format=Path(output_path).suffix[1:])
            logger.info("Silence trimmed", input=input_path, output=output_path)
            return output_path
        except Exception as e:
            logger.error("Trim silence failed", error=str(e))
            return None

    def merge_audio(
        self,
        audio_paths: list[str],
        output_path: Optional[str] = None,
        crossfade: int = 0,
    ) -> Optional[str]:
        """
        Merge multiple audio files.

        Args:
            audio_paths: List of audio file paths
            output_path: Path for output file
            crossfade: Crossfade duration in ms between clips

        Returns:
            Path to output file or None if failed
        """
        if not PYDUB_AVAILABLE:
            logger.error("Pydub not available")
            return None

        try:
            if not audio_paths:
                logger.error("No audio files to merge")
                return None

            result = AudioSegment.from_file(audio_paths[0])

            for path in audio_paths[1:]:
                audio = AudioSegment.from_file(path)
                if crossfade > 0:
                    result = result.append(audio, crossfade=crossfade)
                else:
                    result += audio

            if output_path is None:
                output_path = str(
                    self.output_dir / f"merged_{uuid.uuid4().hex[:8]}.mp3"
                )

            result.export(output_path, format=Path(output_path).suffix[1:])
            logger.info(
                "Audio files merged", count=len(audio_paths), output=output_path
            )
            return output_path
        except Exception as e:
            logger.error("Merge audio failed", error=str(e))
            return None

    def adjust_volume(
        self,
        input_path: str,
        db_change: float,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Adjust audio volume.

        Args:
            input_path: Path to input audio file
            db_change: Volume change in dB (positive = louder, negative = quieter)
            output_path: Path for output file

        Returns:
            Path to output file or None if failed
        """
        if not PYDUB_AVAILABLE:
            logger.error("Pydub not available")
            return None

        try:
            audio = AudioSegment.from_file(input_path)
            adjusted = audio + db_change

            if output_path is None:
                ext = Path(input_path).suffix
                output_path = str(
                    self.output_dir / f"volume_{uuid.uuid4().hex[:8]}{ext}"
                )

            adjusted.export(output_path, format=Path(output_path).suffix[1:])
            logger.info(
                "Volume adjusted", input=input_path, db_change=db_change, output=output_path
            )
            return output_path
        except Exception as e:
            logger.error("Adjust volume failed", error=str(e))
            return None

    def get_duration(self, audio_path: str) -> Optional[float]:
        """
        Get audio duration in seconds.

        Args:
            audio_path: Path to audio file

        Returns:
            Duration in seconds or None if failed
        """
        if not PYDUB_AVAILABLE:
            logger.error("Pydub not available")
            return None

        try:
            audio = AudioSegment.from_file(audio_path)
            return len(audio) / 1000.0
        except Exception as e:
            logger.error("Get duration failed", error=str(e))
            return None


class LibrosaTool:
    """
    Librosa wrapper for audio analysis.

    Provides methods for:
    - Tempo/BPM detection
    - Beat tracking
    - Audio quality assessment
    - Feature extraction
    """

    def __init__(self):
        """Initialize Librosa tool."""
        pass

    @property
    def available(self) -> bool:
        """Check if Librosa is available."""
        return LIBROSA_AVAILABLE

    def detect_tempo(self, audio_path: str) -> Optional[float]:
        """
        Detect tempo (BPM) of audio.

        Args:
            audio_path: Path to audio file

        Returns:
            Tempo in BPM or None if failed
        """
        if not LIBROSA_AVAILABLE:
            logger.error("Librosa not available")
            return None

        try:
            y, sr = librosa.load(audio_path)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            # Handle both scalar and array return types from librosa
            tempo_value = float(tempo[0]) if hasattr(tempo, "__len__") else float(tempo)
            logger.info("Tempo detected", audio=audio_path, bpm=tempo_value)
            return tempo_value
        except Exception as e:
            logger.error("Tempo detection failed", error=str(e))
            return None

    def get_beat_times(self, audio_path: str) -> Optional[list[float]]:
        """
        Get beat timestamps in audio.

        Args:
            audio_path: Path to audio file

        Returns:
            List of beat times in seconds or None if failed
        """
        if not LIBROSA_AVAILABLE:
            logger.error("Librosa not available")
            return None

        try:
            y, sr = librosa.load(audio_path)
            _, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
            beat_times = librosa.frames_to_time(beat_frames, sr=sr)
            logger.info("Beats detected", audio=audio_path, count=len(beat_times))
            return beat_times.tolist()
        except Exception as e:
            logger.error("Beat detection failed", error=str(e))
            return None

    def analyze_audio(self, audio_path: str) -> Optional[dict]:
        """
        Comprehensive audio analysis.

        Args:
            audio_path: Path to audio file

        Returns:
            Dictionary with audio features or None if failed
        """
        if not LIBROSA_AVAILABLE:
            logger.error("Librosa not available")
            return None

        try:
            y, sr = librosa.load(audio_path)

            # Basic features
            tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
            tempo_value = float(tempo[0]) if hasattr(tempo, "__len__") else float(tempo)

            # Spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]

            # RMS energy
            rms = librosa.feature.rms(y=y)[0]

            # Zero crossing rate
            zcr = librosa.feature.zero_crossing_rate(y)[0]

            analysis = {
                "tempo_bpm": tempo_value,
                "beat_count": len(beat_frames),
                "duration_seconds": float(librosa.get_duration(y=y, sr=sr)),
                "sample_rate": sr,
                "spectral_centroid_mean": float(np.mean(spectral_centroids)),
                "spectral_rolloff_mean": float(np.mean(spectral_rolloff)),
                "rms_mean": float(np.mean(rms)),
                "rms_std": float(np.std(rms)),
                "zero_crossing_rate_mean": float(np.mean(zcr)),
            }

            logger.info("Audio analyzed", audio=audio_path)
            return analysis
        except Exception as e:
            logger.error("Audio analysis failed", error=str(e))
            return None

    def get_duration(self, audio_path: str) -> Optional[float]:
        """
        Get audio duration.

        Args:
            audio_path: Path to audio file

        Returns:
            Duration in seconds or None if failed
        """
        if not LIBROSA_AVAILABLE:
            logger.error("Librosa not available")
            return None

        try:
            return float(librosa.get_duration(filename=audio_path))
        except Exception as e:
            logger.error("Get duration failed", error=str(e))
            return None


class WhisperTool:
    """
    OpenAI Whisper wrapper for speech recognition.

    Provides methods for:
    - Transcription (speech to text)
    - Generating captions with timestamps
    - Creating SRT subtitle files
    """

    def __init__(self, model_name: str = "base", output_dir: str = "./output/captions"):
        """
        Initialize Whisper tool.

        Args:
            model_name: Whisper model size (tiny, base, small, medium, large)
            output_dir: Directory for output files
        """
        self.model_name = model_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._model = None

    @property
    def available(self) -> bool:
        """Check if Whisper is available."""
        return WHISPER_AVAILABLE

    def _load_model(self):
        """Lazy load the Whisper model."""
        if self._model is None and WHISPER_AVAILABLE:
            logger.info("Loading Whisper model", model=self.model_name)
            self._model = whisper.load_model(self.model_name)
        return self._model

    def transcribe(self, audio_path: str) -> Optional[dict]:
        """
        Transcribe audio to text.

        Args:
            audio_path: Path to audio file

        Returns:
            Transcription result dict with 'text' and 'segments' or None if failed
        """
        if not WHISPER_AVAILABLE:
            logger.error("Whisper not available")
            return None

        try:
            model = self._load_model()
            result = model.transcribe(audio_path)
            logger.info(
                "Audio transcribed",
                audio=audio_path,
                text_length=len(result.get("text", "")),
            )
            return result
        except Exception as e:
            logger.error("Transcription failed", error=str(e))
            return None

    def generate_captions(
        self,
        audio_path: str,
    ) -> Optional[list[dict]]:
        """
        Generate captions with timestamps.

        Args:
            audio_path: Path to audio file

        Returns:
            List of caption dicts with 'text', 'start', 'end' or None if failed
        """
        if not WHISPER_AVAILABLE:
            logger.error("Whisper not available")
            return None

        try:
            result = self.transcribe(audio_path)
            if not result:
                return None

            captions = []
            for segment in result.get("segments", []):
                captions.append({
                    "text": segment["text"].strip(),
                    "start": segment["start"],
                    "end": segment["end"],
                })

            logger.info("Captions generated", audio=audio_path, count=len(captions))
            return captions
        except Exception as e:
            logger.error("Caption generation failed", error=str(e))
            return None

    def create_srt(
        self,
        audio_path: str,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create SRT subtitle file from audio.

        Args:
            audio_path: Path to audio file
            output_path: Path for output SRT file

        Returns:
            Path to SRT file or None if failed
        """
        if not WHISPER_AVAILABLE:
            logger.error("Whisper not available")
            return None

        try:
            result = self.transcribe(audio_path)
            if not result:
                return None

            if output_path is None:
                output_path = str(
                    self.output_dir / f"captions_{uuid.uuid4().hex[:8]}.srt"
                )

            with open(output_path, "w") as f:
                for i, segment in enumerate(result.get("segments", []), 1):
                    # Format timestamps for SRT
                    start = self._format_srt_time(segment["start"])
                    end = self._format_srt_time(segment["end"])
                    text = segment["text"].strip()

                    f.write(f"{i}\n")
                    f.write(f"{start} --> {end}\n")
                    f.write(f"{text}\n\n")

            logger.info("SRT file created", audio=audio_path, output=output_path)
            return output_path
        except Exception as e:
            logger.error("SRT creation failed", error=str(e))
            return None

    def _format_srt_time(self, seconds: float) -> str:
        """Format seconds as SRT timestamp (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
