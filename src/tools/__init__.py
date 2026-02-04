"""
Open Source Tools Module for Content Creation Engine

This module provides wrappers for various open source tools used in
content creation:

Video Processing:
- FFmpeg: Video encoding, conversion, streaming, and manipulation
- MoviePy: Python library for programmatic video editing

Audio Processing:
- Pydub: Audio manipulation (trim, adjust volume, convert formats)
- Librosa: Audio analysis and feature extraction
- Whisper: Automatic speech recognition for captions

Image Processing:
- Pillow: Image manipulation
- OpenCV: Computer vision and image processing
- rembg: Background removal

AI & Machine Learning:
- DeepFace: Face recognition and analysis
- spaCy: NLP for text processing and hashtag extraction

Social Media:
- Platform-specific posting handlers (YouTube, Instagram, TikTok, etc.)
"""

from .video import FFmpegTool, MoviePyTool
from .audio import PydubTool, LibrosaTool, WhisperTool
from .image import PillowTool, OpenCVTool, RembgTool
from .nlp import SpacyTool
from .face import DeepFaceTool
from .social_media import (
    YouTubePlatform,
    InstagramPlatform,
    TikTokPlatform,
    TwitterPlatform,
    FacebookPlatform,
    LinkedInPlatform,
    get_platform,
)

__all__ = [
    # Video tools
    "FFmpegTool",
    "MoviePyTool",
    # Audio tools
    "PydubTool",
    "LibrosaTool",
    "WhisperTool",
    # Image tools
    "PillowTool",
    "OpenCVTool",
    "RembgTool",
    # NLP tools
    "SpacyTool",
    # Face analysis tools
    "DeepFaceTool",
    # Social media platforms
    "YouTubePlatform",
    "InstagramPlatform",
    "TikTokPlatform",
    "TwitterPlatform",
    "FacebookPlatform",
    "LinkedInPlatform",
    "get_platform",
]
