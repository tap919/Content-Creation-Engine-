"""
Python AI Services Layer

Modular services for the polyglot architecture:
- video_service: Handles FLUX.1, Sora, Veo, Runway integrations
- audio_service: Handles MusicGen, ElevenLabs, Azure Speech, Amazon Polly
- avatar_service (planned): Will handle D-ID, Tavus avatar generation

These services are intended to expose gRPC interfaces for communication with
the Go API Gateway. The currently available VideoServicer and AudioServicer
implementations are placeholders and are not yet fully functional gRPC
servicers (they do not inherit from the generated protobuf servicer base
classes and do not return protobuf messages). They should not be used as
production gRPC servicers until they are completed.

To generate the gRPC bindings from the proto file, run:
    python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. protos/content_factory.proto
"""

from .video_service import VideoServicer
from .audio_service import AudioServicer

# Note: These servicers are placeholders. They are exported for development
# and testing purposes but are not yet fully functional gRPC servicers.
__all__ = ["VideoServicer", "AudioServicer"]
