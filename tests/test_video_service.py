"""Tests for the Video Service module."""

import pytest
from pathlib import Path

from src.services.video_service import (
    VideoServicer,
    VideoProvider,
    FLUX1Provider,
    SoraProvider,
    VeoProvider,
    RunwayProvider,
)


class TestVideoProvider:
    """Tests for the base VideoProvider class."""

    def test_provider_initialization(self):
        """Test that provider can be initialized with optional API key."""
        provider = VideoProvider()
        assert provider.api_key is None

        provider_with_key = VideoProvider(api_key="test-key")
        assert provider_with_key.api_key == "test-key"

    @pytest.mark.asyncio
    async def test_base_generate_raises_not_implemented(self):
        """Test that base generate method raises NotImplementedError."""
        provider = VideoProvider()
        with pytest.raises(NotImplementedError):
            await provider.generate("test prompt")


class TestFLUX1Provider:
    """Tests for the FLUX1Provider class."""

    @pytest.mark.asyncio
    async def test_generate_returns_expected_structure(self):
        """Test that generate returns dict with expected keys."""
        provider = FLUX1Provider()
        result = await provider.generate(prompt="test prompt")

        assert "job_id" in result
        assert "status" in result
        assert "output_url" in result
        assert "provider" in result
        assert result["status"] == "completed"
        assert result["provider"] == "flux1"
        assert "/output/images/flux1_" in result["output_url"]


class TestSoraProvider:
    """Tests for the SoraProvider class."""

    @pytest.mark.asyncio
    async def test_generate_returns_expected_structure(self):
        """Test that generate returns dict with expected keys."""
        provider = SoraProvider()
        result = await provider.generate(prompt="test prompt")

        assert "job_id" in result
        assert "status" in result
        assert "output_url" in result
        assert "provider" in result
        assert result["status"] == "completed"
        assert result["provider"] == "sora"
        assert "/output/videos/sora_" in result["output_url"]


class TestVeoProvider:
    """Tests for the VeoProvider class."""

    @pytest.mark.asyncio
    async def test_generate_returns_expected_structure(self):
        """Test that generate returns dict with expected keys."""
        provider = VeoProvider()
        result = await provider.generate(prompt="test prompt")

        assert "job_id" in result
        assert "status" in result
        assert "output_url" in result
        assert "provider" in result
        assert result["status"] == "completed"
        assert result["provider"] == "veo"


class TestRunwayProvider:
    """Tests for the RunwayProvider class."""

    @pytest.mark.asyncio
    async def test_generate_returns_expected_structure(self):
        """Test that generate returns dict with expected keys."""
        provider = RunwayProvider()
        result = await provider.generate(prompt="test prompt")

        assert "job_id" in result
        assert "status" in result
        assert "output_url" in result
        assert "provider" in result
        assert result["status"] == "completed"
        assert result["provider"] == "runway"


class TestVideoServicer:
    """Tests for the VideoServicer class."""

    def test_initialization(self, tmp_path):
        """Test that servicer initializes correctly."""
        servicer = VideoServicer(output_dir=str(tmp_path))

        assert servicer.output_dir == tmp_path
        assert "flux1" in servicer.providers
        assert "sora" in servicer.providers
        assert "veo" in servicer.providers
        assert "runway" in servicer.providers

    @pytest.mark.asyncio
    async def test_render_success(self, tmp_path):
        """Test successful render request."""
        servicer = VideoServicer(output_dir=str(tmp_path))

        request = {
            "prompt": "A beautiful sunset over mountains",
            "provider": "flux1",
            "duration_seconds": 15,
        }

        result = await servicer.render(request)

        assert "job_id" in result
        assert result["status"] == "completed"
        assert "video_url" in result
        assert "thumbnail_url" in result
        assert "quality_score" in result

    @pytest.mark.asyncio
    async def test_render_with_default_provider(self, tmp_path):
        """Test render uses flux1 as default provider."""
        servicer = VideoServicer(output_dir=str(tmp_path))

        request = {"prompt": "Test prompt"}
        result = await servicer.render(request)

        assert result["status"] == "completed"
        # Default is flux1 which generates images
        assert "_thumb.jpg" in result["thumbnail_url"]

    @pytest.mark.asyncio
    async def test_get_job_status_not_found(self, tmp_path):
        """Test get_job_status for non-existent job."""
        servicer = VideoServicer(output_dir=str(tmp_path))

        result = await servicer.get_job_status("non-existent-job")
        assert result["status"] == "not_found"

    @pytest.mark.asyncio
    async def test_get_job_status_after_render(self, tmp_path):
        """Test get_job_status for existing job."""
        servicer = VideoServicer(output_dir=str(tmp_path))

        render_result = await servicer.render({"prompt": "test"})
        job_id = render_result["job_id"]

        status_result = await servicer.get_job_status(job_id)
        assert status_result["status"] == "completed"
        assert status_result["progress_percent"] == 100.0

    @pytest.mark.asyncio
    async def test_cancel_job_not_found(self, tmp_path):
        """Test cancel_job for non-existent job."""
        servicer = VideoServicer(output_dir=str(tmp_path))

        result = await servicer.cancel_job("non-existent-job")
        assert result["success"] is False
        assert "not found" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_cancel_completed_job(self, tmp_path):
        """Test cancel_job for already completed job."""
        servicer = VideoServicer(output_dir=str(tmp_path))

        render_result = await servicer.render({"prompt": "test"})
        job_id = render_result["job_id"]

        cancel_result = await servicer.cancel_job(job_id)
        assert cancel_result["success"] is False
        assert "already completed" in cancel_result["message"].lower()

    @pytest.mark.asyncio
    async def test_thumbnail_url_for_png_output(self, tmp_path):
        """Test thumbnail URL generation for PNG files (FLUX1)."""
        servicer = VideoServicer(output_dir=str(tmp_path))

        # FLUX1 generates PNG files
        request = {"prompt": "test", "provider": "flux1"}
        result = await servicer.render(request)

        # Should convert .png to _thumb.jpg
        assert result["thumbnail_url"].endswith("_thumb.jpg")

    @pytest.mark.asyncio
    async def test_thumbnail_url_for_mp4_output(self, tmp_path):
        """Test thumbnail URL generation for MP4 files (Sora)."""
        servicer = VideoServicer(output_dir=str(tmp_path))

        # Sora generates MP4 files
        request = {"prompt": "test", "provider": "sora"}
        result = await servicer.render(request)

        # Should convert .mp4 to _thumb.jpg
        assert result["thumbnail_url"].endswith("_thumb.jpg")
