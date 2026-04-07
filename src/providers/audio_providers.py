"""
Audio provider implementations.

Includes open-source and paid audio service providers.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import structlog

from .base import TranscriptionProvider, AudioProvider, ProviderConfig

logger = structlog.get_logger(__name__)


class WhisperTranscriptionProvider(TranscriptionProvider):
    """OpenAI Whisper transcription provider (open-source)."""

    def __init__(self, config: ProviderConfig):
        """
        Initialize Whisper provider.

        Args:
            config: Provider configuration with model size (tiny, base, small, medium, large)
        """
        super().__init__(config)
        self.model = None
        self.model_size = config.model or "base"

    async def initialize(self) -> None:
        """Load the Whisper model."""
        try:
            import whisper
            logger.info("Loading Whisper model", model_size=self.model_size)
            self.model = whisper.load_model(self.model_size)
            logger.info("Whisper model loaded successfully")
        except ImportError:
            logger.error("Whisper not installed. Install with: pip install openai-whisper")
            raise
        except Exception as e:
            logger.error("Failed to load Whisper model", error=str(e))
            raise

    async def cleanup(self) -> None:
        """Clean up model resources."""
        if self.model is not None:
            del self.model
            self.model = None
            logger.info("Whisper model unloaded")

    async def health_check(self) -> Dict[str, Any]:
        """Check if Whisper is available."""
        return {
            "status": "healthy" if self.model is not None else "not_initialized",
            "provider": self.name,
            "model": self.model_size,
        }

    async def transcribe(
        self,
        audio_path: Path,
        language: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio using Whisper.

        Args:
            audio_path: Path to audio file
            language: Optional language code (e.g., 'en', 'es')
            options: Additional options like task='translate'

        Returns:
            Dictionary with transcription results
        """
        if self.model is None:
            raise RuntimeError("Whisper model not initialized")

        try:
            logger.info("Transcribing audio", audio_path=str(audio_path), language=language)

            # Prepare options
            transcribe_options = {
                "language": language,
                "task": "transcribe",
            }
            if options:
                transcribe_options.update(options)

            # Transcribe
            result = self.model.transcribe(str(audio_path), **transcribe_options)

            # Format response
            return {
                "text": result["text"],
                "segments": [
                    {
                        "start": seg["start"],
                        "end": seg["end"],
                        "text": seg["text"],
                    }
                    for seg in result["segments"]
                ],
                "language": result.get("language", language),
                "confidence": 1.0,  # Whisper doesn't provide confidence scores
            }

        except Exception as e:
            logger.error("Whisper transcription failed", error=str(e))
            raise


class CoquiTTSProvider(AudioProvider):
    """Coqui TTS provider for text-to-speech (open-source)."""

    def __init__(self, config: ProviderConfig):
        """
        Initialize Coqui TTS provider.

        Args:
            config: Provider configuration with model name
        """
        super().__init__(config)
        self.tts = None
        self.model_name = config.model or "tts_models/en/ljspeech/tacotron2-DDC"

    async def initialize(self) -> None:
        """Load the TTS model."""
        try:
            from TTS.api import TTS
            logger.info("Loading Coqui TTS model", model=self.model_name)
            self.tts = TTS(self.model_name)
            logger.info("Coqui TTS model loaded successfully")
        except ImportError:
            logger.error("Coqui TTS not installed. Install with: pip install TTS")
            raise
        except Exception as e:
            logger.error("Failed to load Coqui TTS model", error=str(e))
            raise

    async def cleanup(self) -> None:
        """Clean up TTS resources."""
        if self.tts is not None:
            del self.tts
            self.tts = None
            logger.info("Coqui TTS model unloaded")

    async def health_check(self) -> Dict[str, Any]:
        """Check if Coqui TTS is available."""
        return {
            "status": "healthy" if self.tts is not None else "not_initialized",
            "provider": self.name,
            "model": self.model_name,
        }

    async def generate_speech(
        self,
        text: str,
        voice: str,
        output_path: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate speech using Coqui TTS.

        Args:
            text: Text to convert to speech
            voice: Voice identifier or path to reference audio for cloning
            output_path: Where to save the audio file
            options: Additional options

        Returns:
            Dictionary with generation results
        """
        if self.tts is None:
            raise RuntimeError("Coqui TTS model not initialized")

        try:
            logger.info("Generating speech", text_length=len(text), voice=voice)

            # Check if voice is a path (for voice cloning) or a model voice
            if Path(voice).exists():
                # Voice cloning
                self.tts.tts_to_file(
                    text=text,
                    speaker_wav=voice,
                    file_path=str(output_path),
                    **(options or {})
                )
            else:
                # Standard TTS
                self.tts.tts_to_file(
                    text=text,
                    file_path=str(output_path),
                    **(options or {})
                )

            logger.info("Speech generated successfully", output=str(output_path))

            return {
                "path": str(output_path),
                "duration": 0.0,  # Would need to parse audio to get duration
                "format": output_path.suffix.lstrip('.'),
            }

        except Exception as e:
            logger.error("Coqui TTS generation failed", error=str(e))
            raise

    async def generate_music(
        self,
        prompt: str,
        duration: float,
        output_path: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Coqui TTS does not support music generation.

        Raises:
            NotImplementedError
        """
        raise NotImplementedError("Coqui TTS does not support music generation")


class AudioCraftMusicProvider(AudioProvider):
    """AudioCraft/MusicGen provider for music generation (open-source)."""

    def __init__(self, config: ProviderConfig):
        """
        Initialize AudioCraft provider.

        Args:
            config: Provider configuration with model size
        """
        super().__init__(config)
        self.model = None
        self.model_size = config.model or "medium"

    async def initialize(self) -> None:
        """Load the MusicGen model."""
        try:
            from audiocraft.models import MusicGen
            logger.info("Loading MusicGen model", model_size=self.model_size)
            self.model = MusicGen.get_pretrained(f"facebook/musicgen-{self.model_size}")
            logger.info("MusicGen model loaded successfully")
        except ImportError:
            logger.error("AudioCraft not installed. Install with: pip install audiocraft")
            raise
        except Exception as e:
            logger.error("Failed to load MusicGen model", error=str(e))
            raise

    async def cleanup(self) -> None:
        """Clean up model resources."""
        if self.model is not None:
            del self.model
            self.model = None
            logger.info("MusicGen model unloaded")

    async def health_check(self) -> Dict[str, Any]:
        """Check if MusicGen is available."""
        return {
            "status": "healthy" if self.model is not None else "not_initialized",
            "provider": self.name,
            "model": self.model_size,
        }

    async def generate_speech(
        self,
        text: str,
        voice: str,
        output_path: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        MusicGen does not support speech generation.

        Raises:
            NotImplementedError
        """
        raise NotImplementedError("MusicGen does not support speech generation")

    async def generate_music(
        self,
        prompt: str,
        duration: float,
        output_path: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate music using MusicGen.

        Args:
            prompt: Description of desired music
            duration: Duration in seconds
            output_path: Where to save the audio file
            options: Additional options

        Returns:
            Dictionary with generation results
        """
        if self.model is None:
            raise RuntimeError("MusicGen model not initialized")

        try:
            import torchaudio
            logger.info("Generating music", prompt=prompt, duration=duration)

            # Set generation parameters
            self.model.set_generation_params(duration=duration)

            # Generate
            wav = self.model.generate([prompt])

            # Save audio
            torchaudio.save(str(output_path), wav[0].cpu(), self.model.sample_rate)

            logger.info("Music generated successfully", output=str(output_path))

            return {
                "path": str(output_path),
                "duration": duration,
                "format": output_path.suffix.lstrip('.'),
                "sample_rate": self.model.sample_rate,
            }

        except Exception as e:
            logger.error("MusicGen generation failed", error=str(e))
            raise
