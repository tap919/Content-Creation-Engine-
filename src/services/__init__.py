"""
Python AI Services Layer

Modular services for the polyglot architecture:
- video_service: Handles FLUX.1, Sora, Veo, Runway integrations
- audio_service: Handles MusicGen, ElevenLabs, Azure Speech, Amazon Polly
- avatar_service: Handles D-ID, Tavus avatar generation

These services expose gRPC interfaces for communication with the Go API Gateway.
"""

from .video_service import VideoServicer
from .audio_service import AudioServicer

__all__ = ["VideoServicer", "AudioServicer"]
