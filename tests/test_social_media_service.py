"""Tests for Social Media Service."""

import pytest
from src.services.social_media_service import (
    SocialMediaServicer,
    PostizProvider,
    ImPostingProvider,
    InstaPyProvider,
)


@pytest.fixture
def social_media_servicer():
    """Create social media servicer for testing."""
    return SocialMediaServicer(output_dir="/tmp/test_output")


@pytest.fixture
def postiz_provider():
    """Create Postiz provider for testing."""
    return PostizProvider(api_key="test_key")


@pytest.fixture
def imposting_provider():
    """Create ImPosting provider for testing."""
    return ImPostingProvider(api_key="test_key")


@pytest.fixture
def instapy_provider():
    """Create InstaPy provider for testing."""
    return InstaPyProvider()


class TestPostizProvider:
    """Test Postiz provider."""

    @pytest.mark.asyncio
    async def test_create_post(self, postiz_provider):
        """Test creating a post."""
        result = await postiz_provider.create_post(
            content="Test post content",
            platforms=["instagram", "tiktok"],
            media_urls=["https://example.com/video.mp4"],
        )
        
        assert "post_id" in result
        assert result["status"] in ["scheduled", "published"]
        assert result["provider"] == "postiz"
        assert "platforms" in result

    @pytest.mark.asyncio
    async def test_create_scheduled_post(self, postiz_provider):
        """Test creating a scheduled post."""
        result = await postiz_provider.create_post(
            content="Scheduled post",
            platforms=["instagram"],
            scheduled_at="2026-02-05T10:00:00Z",
        )
        
        assert result["status"] == "scheduled"
        assert result["scheduled_at"] == "2026-02-05T10:00:00Z"

    @pytest.mark.asyncio
    async def test_list_integrations(self, postiz_provider):
        """Test listing integrations."""
        result = await postiz_provider.list_integrations()
        
        assert "integrations" in result
        assert len(result["integrations"]) > 0
        assert "platform" in result["integrations"][0]

    @pytest.mark.asyncio
    async def test_get_post_analytics(self, postiz_provider):
        """Test getting post analytics."""
        result = await postiz_provider.get_post_analytics("test_post_id")
        
        assert "post_id" in result
        assert "views" in result
        assert "likes" in result
        assert "engagement_rate" in result


class TestImPostingProvider:
    """Test ImPosting provider."""

    @pytest.mark.asyncio
    async def test_upload_media(self, imposting_provider):
        """Test media upload."""
        result = await imposting_provider.upload_media("/tmp/test_video.mp4")
        
        assert "media_id" in result
        assert "media_url" in result
        assert result["status"] == "uploaded"

    @pytest.mark.asyncio
    async def test_schedule_post(self, imposting_provider):
        """Test scheduling a post."""
        result = await imposting_provider.schedule_post(
            platform="instagram",
            post_data={"caption": "Test post", "media_id": "123"},
            scheduled_at="2026-02-05T10:00:00Z",
        )
        
        assert "schedule_id" in result
        assert result["status"] == "scheduled"
        assert result["platform"] == "instagram"
        assert result["provider"] == "imposting"

    @pytest.mark.asyncio
    async def test_get_oauth_url(self, imposting_provider):
        """Test getting OAuth URL."""
        result = await imposting_provider.get_oauth_url(
            platform="instagram",
            callback_url="https://example.com/callback",
        )
        
        assert "oauth_url" in result
        assert "state" in result
        assert "instagram" in result["oauth_url"]


class TestInstaPyProvider:
    """Test InstaPy provider."""

    @pytest.mark.asyncio
    async def test_post_photo(self, instapy_provider):
        """Test posting a photo."""
        result = await instapy_provider.post_photo(
            photo_path="/tmp/test_photo.jpg",
            caption="Test photo caption",
            hashtags=["test", "automation"],
        )
        
        assert "post_id" in result
        assert result["status"] == "published"
        assert "url" in result
        assert result["provider"] == "instapy"

    @pytest.mark.asyncio
    async def test_post_video(self, instapy_provider):
        """Test posting a video."""
        result = await instapy_provider.post_video(
            video_path="/tmp/test_video.mp4",
            caption="Test video caption",
            hashtags=["reel", "content"],
        )
        
        assert "post_id" in result
        assert result["status"] == "published"
        assert "reel" in result["url"]

    @pytest.mark.asyncio
    async def test_auto_engage(self, instapy_provider):
        """Test auto-engagement."""
        result = await instapy_provider.auto_engage(
            target_hashtags=["ai", "content"],
            like_count=20,
            comment_templates=["Great post!", "Love this!"],
        )
        
        assert result["status"] == "completed"
        assert result["likes"] == 20
        assert result["comments"] > 0
        assert result["follows"] > 0


class TestSocialMediaServicer:
    """Test Social Media servicer."""

    @pytest.mark.asyncio
    async def test_post_content_postiz(self, social_media_servicer):
        """Test posting content via Postiz."""
        request = {
            "provider": "postiz",
            "content": "Test post content",
            "platforms": ["instagram", "tiktok"],
            "media_urls": ["https://example.com/video.mp4"],
        }
        
        result = await social_media_servicer.post_content(request)
        
        assert result["status"] in ["scheduled", "published", "completed"]
        assert "job_id" in result
        assert "post_id" in result

    @pytest.mark.asyncio
    async def test_post_content_imposting(self, social_media_servicer):
        """Test posting content via ImPosting."""
        request = {
            "provider": "imposting",
            "content": "Test caption",
            "platforms": ["instagram"],
            "media_path": "/tmp/test_video.mp4",
            "scheduled_at": "2026-02-05T10:00:00Z",
        }
        
        result = await social_media_servicer.post_content(request)
        
        assert result["status"] in ["scheduled", "completed"]
        assert "job_id" in result

    @pytest.mark.asyncio
    async def test_post_content_instapy_photo(self, social_media_servicer):
        """Test posting photo via InstaPy."""
        request = {
            "provider": "instapy",
            "content": "Photo caption",
            "platforms": ["instagram"],
            "media_path": "/tmp/test_photo.jpg",
            "hashtags": ["test", "photo"],
        }
        
        result = await social_media_servicer.post_content(request)
        
        assert result["status"] in ["published", "completed"]
        assert "job_id" in result

    @pytest.mark.asyncio
    async def test_post_content_instapy_video(self, social_media_servicer):
        """Test posting video via InstaPy."""
        request = {
            "provider": "instapy",
            "content": "Video caption",
            "platforms": ["instagram"],
            "media_path": "/tmp/test_video.mp4",
            "hashtags": ["test", "video"],
        }
        
        result = await social_media_servicer.post_content(request)
        
        assert result["status"] in ["published", "completed"]
        assert "job_id" in result

    @pytest.mark.asyncio
    async def test_post_content_unknown_provider(self, social_media_servicer):
        """Test posting with unknown provider."""
        request = {
            "provider": "unknown",
            "content": "Test",
            "platforms": ["instagram"],
        }
        
        result = await social_media_servicer.post_content(request)
        
        assert result["status"] == "failed"
        assert "error_message" in result

    @pytest.mark.asyncio
    async def test_get_analytics(self, social_media_servicer):
        """Test getting analytics."""
        request = {
            "post_id": "test_post_123",
            "provider": "postiz",
        }
        
        result = await social_media_servicer.get_analytics(request)
        
        assert "post_id" in result
        # Analytics are available for Postiz
        assert "views" in result or "error" in result

    @pytest.mark.asyncio
    async def test_auto_engage(self, social_media_servicer):
        """Test auto-engagement."""
        request = {
            "hashtags": ["ai", "automation"],
            "like_count": 15,
            "comment_templates": ["Great!"],
        }
        
        result = await social_media_servicer.auto_engage(request)
        
        assert result["status"] == "completed"
        assert "job_id" in result
        assert result["likes"] == 15

    @pytest.mark.asyncio
    async def test_get_job_status_existing(self, social_media_servicer):
        """Test getting status of existing job."""
        # Create a job first
        request = {
            "provider": "postiz",
            "content": "Test",
            "platforms": ["instagram"],
        }
        create_result = await social_media_servicer.post_content(request)
        job_id = create_result["job_id"]
        
        # Get status
        status = await social_media_servicer.get_job_status(job_id)
        
        assert status["job_id"] == job_id
        assert status["status"] in ["processing", "completed"]
        assert "progress_percent" in status

    @pytest.mark.asyncio
    async def test_get_job_status_not_found(self, social_media_servicer):
        """Test getting status of non-existent job."""
        status = await social_media_servicer.get_job_status("nonexistent_job_id")
        
        assert status["status"] == "not_found"
