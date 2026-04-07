"""
Provider abstraction layer for external services.

This module provides a unified interface for different service providers
(both open-source and paid APIs) to enable easy switching and fallback handling.
"""

from .base import (
    AudioProvider,
    VideoProvider,
    ImageProvider,
    TranscriptionProvider,
    ProviderConfig,
)
from .audio_providers import WhisperTranscriptionProvider, CoquiTTSProvider
from .video_providers import OpenSoraVideoProvider
from .image_providers import ComfyUIImageProvider

__all__ = [
    # Base classes
    "AudioProvider",
    "VideoProvider",
    "ImageProvider",
    "TranscriptionProvider",
    "ProviderConfig",
    # Audio providers
    "WhisperTranscriptionProvider",
    "CoquiTTSProvider",
    # Video providers
    "OpenSoraVideoProvider",
    # Image providers
    "ComfyUIImageProvider",
]
