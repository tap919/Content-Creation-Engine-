"""
Base provider interfaces and abstract classes.

Defines the contract that all service providers must implement,
enabling easy switching between different providers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from pathlib import Path
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ProviderConfig:
    """Configuration for a service provider."""
    name: str
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    model: Optional[str] = None
    options: Dict[str, Any] = None

    def __post_init__(self):
        if self.options is None:
            self.options = {}


class BaseProvider(ABC):
    """Base class for all service providers."""

    def __init__(self, config: ProviderConfig):
        """
        Initialize the provider.

        Args:
            config: Provider configuration
        """
        self.config = config
        self.name = config.name
        logger.info(f"Initializing {self.__class__.__name__}", provider=config.name)

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider (load models, check API, etc.)."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources."""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check provider health and availability.

        Returns:
            Dictionary with status information
        """
        pass


class TranscriptionProvider(BaseProvider):
    """Provider for audio transcription services."""

    @abstractmethod
    async def transcribe(
        self,
        audio_path: Path,
        language: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio to text.

        Args:
            audio_path: Path to audio file
            language: Optional language code
            options: Additional provider-specific options

        Returns:
            Dictionary with:
                - text: Transcribed text
                - segments: List of timestamped segments
                - language: Detected language
                - confidence: Confidence score
        """
        pass


class AudioProvider(BaseProvider):
    """Provider for audio generation services."""

    @abstractmethod
    async def generate_speech(
        self,
        text: str,
        voice: str,
        output_path: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate speech from text.

        Args:
            text: Text to convert to speech
            voice: Voice identifier
            output_path: Where to save the audio file
            options: Additional provider-specific options

        Returns:
            Dictionary with:
                - path: Path to generated audio
                - duration: Duration in seconds
                - format: Audio format
        """
        pass

    @abstractmethod
    async def generate_music(
        self,
        prompt: str,
        duration: float,
        output_path: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate music from text prompt.

        Args:
            prompt: Description of desired music
            duration: Duration in seconds
            output_path: Where to save the audio file
            options: Additional provider-specific options

        Returns:
            Dictionary with generation results
        """
        pass


class VideoProvider(BaseProvider):
    """Provider for video generation services."""

    @abstractmethod
    async def generate_video(
        self,
        prompt: str,
        duration: float,
        output_path: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate video from text prompt.

        Args:
            prompt: Description of desired video
            duration: Duration in seconds
            output_path: Where to save the video file
            options: Additional provider-specific options

        Returns:
            Dictionary with:
                - path: Path to generated video
                - duration: Actual duration
                - resolution: Video resolution
                - fps: Frames per second
        """
        pass

    @abstractmethod
    async def image_to_video(
        self,
        image_path: Path,
        prompt: Optional[str],
        duration: float,
        output_path: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate video from image with optional prompt.

        Args:
            image_path: Path to input image
            prompt: Optional motion/style description
            duration: Duration in seconds
            output_path: Where to save the video file
            options: Additional provider-specific options

        Returns:
            Dictionary with generation results
        """
        pass


class ImageProvider(BaseProvider):
    """Provider for image generation services."""

    @abstractmethod
    async def generate_image(
        self,
        prompt: str,
        output_path: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate image from text prompt.

        Args:
            prompt: Description of desired image
            output_path: Where to save the image file
            options: Additional options (size, style, etc.)

        Returns:
            Dictionary with:
                - path: Path to generated image
                - size: Image dimensions (width, height)
                - format: Image format
        """
        pass

    @abstractmethod
    async def edit_image(
        self,
        image_path: Path,
        prompt: str,
        output_path: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Edit an existing image based on prompt.

        Args:
            image_path: Path to input image
            prompt: Description of desired edits
            output_path: Where to save the edited image
            options: Additional provider-specific options

        Returns:
            Dictionary with edit results
        """
        pass
