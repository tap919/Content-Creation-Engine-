"""Tests for Avatar Service."""

import pytest
from src.services.avatar_service import (
    AvatarServicer,
    HeyGenProvider,
    DIDProvider,
    SynthesiaProvider,
    ElaiProvider,
)


@pytest.fixture
def avatar_servicer():
    """Create avatar servicer for testing."""
    return AvatarServicer(output_dir="/tmp/test_output")


@pytest.fixture
def heygen_provider():
    """Create HeyGen provider for testing."""
    return HeyGenProvider(api_key="test_key")


@pytest.fixture
def did_provider():
    """Create D-ID provider for testing."""
    return DIDProvider(api_key="test_key")


@pytest.fixture
def synthesia_provider():
    """Create Synthesia provider for testing."""
    return SynthesiaProvider(api_key="test_key")


@pytest.fixture
def elai_provider():
    """Create Elai provider for testing."""
    return ElaiProvider(api_key="test_key")


class TestHeyGenProvider:
    """Test HeyGen provider."""

    @pytest.mark.asyncio
    async def test_generate_avatar_video(self, heygen_provider):
        """Test avatar video generation."""
        result = await heygen_provider.generate_avatar_video(
            script="Hello, this is a test video!",
            avatar_id="test_avatar",
            language="en",
        )
        
        assert result["status"] == "completed"
        assert "video_url" in result
        assert result["provider"] == "heygen"
        assert result["duration_ms"] > 0

    @pytest.mark.asyncio
    async def test_upload_photo(self, heygen_provider):
        """Test photo upload for avatar creation."""
        result = await heygen_provider.upload_photo("/tmp/test_photo.jpg")
        
        assert result["status"] == "completed"
        assert "avatar_id" in result


class TestDIDProvider:
    """Test D-ID provider."""

    @pytest.mark.asyncio
    async def test_generate_talking_photo(self, did_provider):
        """Test talking photo generation."""
        result = await did_provider.generate_talking_photo(
            photo_url="https://example.com/photo.jpg",
            script="Hello from D-ID!",
            voice="en-US-JennyNeural",
        )
        
        assert result["status"] == "completed"
        assert "video_url" in result
        assert result["provider"] == "d-id"

    @pytest.mark.asyncio
    async def test_list_voices(self, did_provider):
        """Test listing available voices."""
        result = await did_provider.list_voices()
        
        assert "voices" in result
        assert len(result["voices"]) > 0
        assert "id" in result["voices"][0]


class TestSynthesiaProvider:
    """Test Synthesia provider."""

    @pytest.mark.asyncio
    async def test_generate_video(self, synthesia_provider):
        """Test video generation with Synthesia."""
        result = await synthesia_provider.generate_video(
            script="Welcome to Synthesia!",
            avatar_id="anna_costume1_cameraA",
            background="green_screen",
        )
        
        assert result["status"] == "completed"
        assert "video_url" in result
        assert result["provider"] == "synthesia"

    @pytest.mark.asyncio
    async def test_list_avatars(self, synthesia_provider):
        """Test listing available avatars."""
        result = await synthesia_provider.list_avatars()
        
        assert "avatars" in result
        assert len(result["avatars"]) > 0
        assert "id" in result["avatars"][0]


class TestElaiProvider:
    """Test Elai provider."""

    @pytest.mark.asyncio
    async def test_render_video(self, elai_provider):
        """Test video rendering with Elai."""
        result = await elai_provider.render_video(
            script="Testing Elai video!",
            avatar_style="realistic",
        )
        
        assert result["status"] == "completed"
        assert "video_url" in result
        assert result["provider"] == "elai"

    @pytest.mark.asyncio
    async def test_upload_asset(self, elai_provider):
        """Test asset upload."""
        result = await elai_provider.upload_asset(
            "/tmp/test_asset.mp3",
            "mp3",
        )
        
        assert result["status"] == "completed"
        assert "asset_id" in result
        assert "asset_url" in result


class TestAvatarServicer:
    """Test Avatar servicer."""

    @pytest.mark.asyncio
    async def test_create_avatar_video_heygen(self, avatar_servicer):
        """Test avatar video creation with HeyGen."""
        request = {
            "provider": "heygen",
            "script": "This is a test video",
            "avatar_id": "test_avatar",
            "language": "en",
        }
        
        result = await avatar_servicer.create_avatar_video(request)
        
        assert result["status"] == "completed"
        assert "job_id" in result
        assert "video_url" in result
        assert result["provider"] == "heygen"

    @pytest.mark.asyncio
    async def test_create_avatar_video_did(self, avatar_servicer):
        """Test avatar video creation with D-ID."""
        request = {
            "provider": "d-id",
            "script": "Testing D-ID",
            "photo_url": "https://example.com/photo.jpg",
            "voice": "en-US-JennyNeural",
        }
        
        result = await avatar_servicer.create_avatar_video(request)
        
        assert result["status"] == "completed"
        assert "job_id" in result
        assert "video_url" in result

    @pytest.mark.asyncio
    async def test_create_avatar_video_synthesia(self, avatar_servicer):
        """Test avatar video creation with Synthesia."""
        request = {
            "provider": "synthesia",
            "script": "Synthesia test",
            "avatar_id": "anna_costume1_cameraA",
        }
        
        result = await avatar_servicer.create_avatar_video(request)
        
        assert result["status"] == "completed"
        assert "job_id" in result
        assert "video_url" in result

    @pytest.mark.asyncio
    async def test_create_avatar_video_elai(self, avatar_servicer):
        """Test avatar video creation with Elai."""
        request = {
            "provider": "elai",
            "script": "Elai rendering test",
            "avatar_style": "realistic",
        }
        
        result = await avatar_servicer.create_avatar_video(request)
        
        assert result["status"] == "completed"
        assert "job_id" in result
        assert "video_url" in result

    @pytest.mark.asyncio
    async def test_create_avatar_video_unknown_provider(self, avatar_servicer):
        """Test avatar video creation with unknown provider."""
        request = {
            "provider": "unknown",
            "script": "Test",
        }
        
        result = await avatar_servicer.create_avatar_video(request)
        
        assert result["status"] == "failed"
        assert "error_message" in result

    @pytest.mark.asyncio
    async def test_get_job_status_existing(self, avatar_servicer):
        """Test getting status of existing job."""
        # Create a job first
        request = {
            "provider": "heygen",
            "script": "Test",
        }
        create_result = await avatar_servicer.create_avatar_video(request)
        job_id = create_result["job_id"]
        
        # Get status
        status = await avatar_servicer.get_job_status(job_id)
        
        assert status["job_id"] == job_id
        assert status["status"] in ["processing", "completed"]
        assert "progress_percent" in status

    @pytest.mark.asyncio
    async def test_get_job_status_not_found(self, avatar_servicer):
        """Test getting status of non-existent job."""
        status = await avatar_servicer.get_job_status("nonexistent_job_id")
        
        assert status["status"] == "not_found"

    @pytest.mark.asyncio
    async def test_upload_photo_heygen(self, avatar_servicer):
        """Test photo upload for HeyGen."""
        photo_data = b"fake_photo_data"
        
        result = await avatar_servicer.upload_photo("heygen", photo_data)
        
        assert result["status"] == "completed"
        assert "avatar_id" in result

    @pytest.mark.asyncio
    async def test_upload_photo_elai(self, avatar_servicer):
        """Test photo upload for Elai."""
        photo_data = b"fake_photo_data"
        
        result = await avatar_servicer.upload_photo("elai", photo_data)
        
        assert result["status"] == "completed"
        assert "asset_id" in result

    @pytest.mark.asyncio
    async def test_upload_photo_unsupported_provider(self, avatar_servicer):
        """Test photo upload for unsupported provider."""
        photo_data = b"fake_photo_data"
        
        result = await avatar_servicer.upload_photo("synthesia", photo_data)
        
        assert result["status"] == "failed"
        assert "error_message" in result
