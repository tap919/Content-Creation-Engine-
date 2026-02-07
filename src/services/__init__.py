"""
Python AI Services Layer

Modular services for the polyglot architecture:
- video_service: Handles FLUX.1, Sora, Veo, Runway integrations
- audio_service: Handles MusicGen, ElevenLabs, Azure Speech, Amazon Polly
- avatar_service: Handles HeyGen, D-ID, Synthesia, Elai avatar generation
- social_media_service: Handles Postiz, ImPosting, InstaPy integrations
- brand_dna_service: Manages consistent branding across all content
- repurposing_service: Handles multi-platform content adaptation
- creative_spark_service: Provides AI-powered idea generation

These services are intended to expose gRPC interfaces for communication with
the Go API Gateway. The currently available servicers are placeholders and 
are not yet fully functional gRPC servicers (they do not inherit from the 
generated protobuf servicer base classes and do not return protobuf messages). 
They should not be used as production gRPC servicers until they are completed.

To generate the gRPC bindings from the proto file, run:
    python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. protos/content_factory.proto
"""

from .video_service import VideoServicer
from .audio_service import AudioServicer
from .avatar_service import AvatarServicer
from .social_media_service import SocialMediaServicer
from .brand_dna_service import BrandDNAService
from .repurposing_service import ContentRepurposingService
from .creative_spark_service import CreativeSparkService

# Note: These servicers are placeholders. They are exported for development
# and testing purposes but are not yet fully functional gRPC servicers.
__all__ = [
    "VideoServicer", 
    "AudioServicer", 
    "AvatarServicer", 
    "SocialMediaServicer",
    "BrandDNAService",
    "ContentRepurposingService",
    "CreativeSparkService",
]
