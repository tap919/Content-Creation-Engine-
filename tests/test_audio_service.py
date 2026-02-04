"""Tests for the Audio Service module."""

import pytest
from pathlib import Path

from src.services.audio_service import (
    AudioServicer,
    AudioProvider,
    MusicGenProvider,
    ElevenLabsProvider,
    AzureSpeechProvider,
    AmazonPollyProvider,
    ESTIMATED_MS_PER_CHAR,
)


class TestEstimatedMsPerChar:
    """Tests for the ESTIMATED_MS_PER_CHAR constant."""

    def test_constant_value(self):
        """Test that constant is set correctly based on speaking rate calculation."""
        # Based on 150 words/min with ~5 chars/word = 750 chars/min = 12.5 chars/sec = 80ms/char
        assert ESTIMATED_MS_PER_CHAR == 80


class TestAudioProvider:
    """Tests for the base AudioProvider class."""

    def test_provider_initialization(self):
        """Test that provider can be initialized with optional API key."""
        provider = AudioProvider()
        assert provider.api_key is None

        provider_with_key = AudioProvider(api_key="test-key")
        assert provider_with_key.api_key == "test-key"

    @pytest.mark.asyncio
    async def test_base_generate_raises_not_implemented(self):
        """Test that base generate method raises NotImplementedError."""
        provider = AudioProvider()
        with pytest.raises(NotImplementedError):
            await provider.generate()


class TestMusicGenProvider:
    """Tests for the MusicGenProvider class."""

    @pytest.mark.asyncio
    async def test_generate_music_returns_expected_structure(self):
        """Test that generate_music returns dict with expected keys."""
        provider = MusicGenProvider()
        result = await provider.generate_music(
            prompt="lo-fi chill beats",
            duration_seconds=15,
            tempo=90.0,
            mood="relaxing",
        )

        assert "job_id" in result
        assert "status" in result
        assert "audio_url" in result
        assert "duration_ms" in result
        assert "provider" in result
        assert result["status"] == "completed"
        assert result["provider"] == "musicgen"
        assert result["duration_ms"] == 15000


class TestElevenLabsProvider:
    """Tests for the ElevenLabsProvider class."""

    @pytest.mark.asyncio
    async def test_generate_voiceover_returns_expected_structure(self):
        """Test that generate_voiceover returns dict with expected keys."""
        provider = ElevenLabsProvider()
        result = await provider.generate_voiceover(
            text="Hello, this is a test.",
            voice="Adam",
        )

        assert "job_id" in result
        assert "status" in result
        assert "audio_url" in result
        assert "duration_ms" in result
        assert "provider" in result
        assert result["status"] == "completed"
        assert result["provider"] == "elevenlabs"
        assert "/output/audio/elevenlabs_" in result["audio_url"]

    @pytest.mark.asyncio
    async def test_duration_estimation(self):
        """Test that duration is estimated based on text length."""
        provider = ElevenLabsProvider()
        text = "A" * 100  # 100 characters
        result = await provider.generate_voiceover(text=text)

        # 100 chars * 80ms = 8000ms
        assert result["duration_ms"] == 100 * ESTIMATED_MS_PER_CHAR


class TestAzureSpeechProvider:
    """Tests for the AzureSpeechProvider class."""

    @pytest.mark.asyncio
    async def test_generate_voiceover_returns_expected_structure(self):
        """Test that generate_voiceover returns dict with expected keys."""
        provider = AzureSpeechProvider()
        result = await provider.generate_voiceover(
            text="Hello, this is a test.",
            voice="en-US-JennyNeural",
        )

        assert "job_id" in result
        assert "status" in result
        assert "audio_url" in result
        assert "duration_ms" in result
        assert "provider" in result
        assert result["status"] == "completed"
        assert result["provider"] == "azure_speech"


class TestAmazonPollyProvider:
    """Tests for the AmazonPollyProvider class."""

    @pytest.mark.asyncio
    async def test_generate_voiceover_returns_expected_structure(self):
        """Test that generate_voiceover returns dict with expected keys."""
        provider = AmazonPollyProvider()
        result = await provider.generate_voiceover(
            text="Hello, this is a test.",
            voice="Matthew",
        )

        assert "job_id" in result
        assert "status" in result
        assert "audio_url" in result
        assert "duration_ms" in result
        assert "provider" in result
        assert result["status"] == "completed"
        assert result["provider"] == "amazon_polly"


class TestAudioServicer:
    """Tests for the AudioServicer class."""

    def test_initialization(self, tmp_path):
        """Test that servicer initializes correctly."""
        servicer = AudioServicer(output_dir=str(tmp_path))

        assert servicer.output_dir == tmp_path
        assert servicer.music_provider is not None
        assert "elevenlabs" in servicer.tts_providers
        assert "azure_speech" in servicer.tts_providers
        assert "amazon_polly" in servicer.tts_providers

    @pytest.mark.asyncio
    async def test_generate_music_success(self, tmp_path):
        """Test successful music generation request."""
        servicer = AudioServicer(output_dir=str(tmp_path))

        request = {
            "params": {
                "mood": "lo-fi chill",
                "tempo": 90,
                "key": "C minor",
                "energy": 0.4,
            },
            "duration_seconds": 15,
        }

        result = await servicer.generate_music(request)

        assert "job_id" in result
        assert result["status"] == "completed"
        assert "audio_url" in result
        assert "quality_score" in result
        assert "duration_ms" in result

    @pytest.mark.asyncio
    async def test_generate_voiceover_success(self, tmp_path):
        """Test successful voiceover generation request."""
        servicer = AudioServicer(output_dir=str(tmp_path))

        request = {
            "text": "Hello, this is a test voiceover.",
            "voice": "Adam",
            "provider": "elevenlabs",
        }

        result = await servicer.generate_voiceover(request)

        assert "job_id" in result
        assert result["status"] == "completed"
        assert "audio_url" in result
        assert "duration_ms" in result

    @pytest.mark.asyncio
    async def test_generate_voiceover_default_provider(self, tmp_path):
        """Test voiceover uses elevenlabs as default provider."""
        servicer = AudioServicer(output_dir=str(tmp_path))

        request = {"text": "Test text"}
        result = await servicer.generate_voiceover(request)

        assert result["status"] == "completed"
        # Default is elevenlabs
        assert "elevenlabs" in result["audio_url"]

    @pytest.mark.asyncio
    async def test_generate_voiceover_azure_provider(self, tmp_path):
        """Test voiceover with Azure Speech provider."""
        servicer = AudioServicer(output_dir=str(tmp_path))

        request = {
            "text": "Test text",
            "provider": "azure_speech",
        }
        result = await servicer.generate_voiceover(request)

        assert result["status"] == "completed"
        assert "azure" in result["audio_url"]

    @pytest.mark.asyncio
    async def test_get_job_status_not_found(self, tmp_path):
        """Test get_job_status for non-existent job."""
        servicer = AudioServicer(output_dir=str(tmp_path))

        result = await servicer.get_job_status("non-existent-job")
        assert result["status"] == "not_found"

    @pytest.mark.asyncio
    async def test_get_job_status_after_music_generation(self, tmp_path):
        """Test get_job_status for existing music job."""
        servicer = AudioServicer(output_dir=str(tmp_path))

        gen_result = await servicer.generate_music({"duration_seconds": 15})
        job_id = gen_result["job_id"]

        status_result = await servicer.get_job_status(job_id)
        assert status_result["status"] == "completed"
        assert status_result["progress_percent"] == 100.0

    @pytest.mark.asyncio
    async def test_get_job_status_after_voiceover_generation(self, tmp_path):
        """Test get_job_status for existing voiceover job."""
        servicer = AudioServicer(output_dir=str(tmp_path))

        gen_result = await servicer.generate_voiceover({"text": "test"})
        job_id = gen_result["job_id"]

        status_result = await servicer.get_job_status(job_id)
        assert status_result["status"] == "completed"
