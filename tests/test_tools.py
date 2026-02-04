"""
Tests for the Open Source Tools module.

Tests the wrappers for:
- Video tools (FFmpeg, MoviePy)
- Audio tools (Pydub, Librosa, Whisper)
- Image tools (Pillow, OpenCV, rembg)
- NLP tools (spaCy)
- Face analysis tools (DeepFace)
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile


class TestFFmpegTool:
    """Tests for FFmpegTool."""

    def test_ffmpeg_tool_init(self):
        """Test FFmpegTool initialization."""
        from src.tools.video import FFmpegTool

        tool = FFmpegTool()
        assert tool.ffmpeg_path == "ffmpeg"

        tool = FFmpegTool(ffmpeg_path="/usr/bin/ffmpeg")
        assert tool.ffmpeg_path == "/usr/bin/ffmpeg"

    @patch("subprocess.run")
    def test_resize_video(self, mock_run):
        """Test video resizing."""
        from src.tools.video import FFmpegTool

        mock_run.return_value = Mock(returncode=0)

        tool = FFmpegTool()
        result = tool.resize_video("input.mp4", "output.mp4", 1080, 1920)

        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "ffmpeg" in call_args
        assert "-vf" in call_args
        assert "scale=1080:1920" in call_args

    @patch("subprocess.run")
    def test_resize_for_instagram(self, mock_run):
        """Test Instagram resizing (9:16 aspect ratio)."""
        from src.tools.video import FFmpegTool

        mock_run.return_value = Mock(returncode=0)

        tool = FFmpegTool()
        result = tool.resize_for_instagram("input.mp4", "output.mp4")

        assert result is True
        call_args = mock_run.call_args[0][0]
        assert "scale=1080:1920" in call_args

    @patch("subprocess.run")
    def test_add_watermark(self, mock_run):
        """Test adding watermark."""
        from src.tools.video import FFmpegTool

        mock_run.return_value = Mock(returncode=0)

        tool = FFmpegTool()
        result = tool.add_watermark("video.mp4", "logo.png", "output.mp4")

        assert result is True
        call_args = mock_run.call_args[0][0]
        assert "-filter_complex" in call_args
        assert "overlay" in str(call_args)

    @patch("subprocess.run")
    def test_extract_audio(self, mock_run):
        """Test audio extraction."""
        from src.tools.video import FFmpegTool

        mock_run.return_value = Mock(returncode=0)

        tool = FFmpegTool()
        result = tool.extract_audio("video.mp4", "audio.mp3")

        assert result is True
        call_args = mock_run.call_args[0][0]
        assert "-vn" in call_args  # No video flag

    @patch("subprocess.run")
    def test_merge_audio_video(self, mock_run):
        """Test merging audio and video."""
        from src.tools.video import FFmpegTool

        mock_run.return_value = Mock(returncode=0)

        tool = FFmpegTool()
        result = tool.merge_audio_video("video.mp4", "audio.mp3", "output.mp4")

        assert result is True


class TestMoviePyTool:
    """Tests for MoviePyTool."""

    def test_moviepy_tool_init(self):
        """Test MoviePyTool initialization."""
        from src.tools.video import MoviePyTool

        with tempfile.TemporaryDirectory() as tmpdir:
            tool = MoviePyTool(output_dir=tmpdir)
            assert tool.output_dir == Path(tmpdir)
            assert tool.output_dir.exists()

    def test_moviepy_available_property(self):
        """Test available property."""
        from src.tools.video import MoviePyTool, MOVIEPY_AVAILABLE

        tool = MoviePyTool()
        assert tool.available == MOVIEPY_AVAILABLE


class TestPydubTool:
    """Tests for PydubTool."""

    def test_pydub_tool_init(self):
        """Test PydubTool initialization."""
        from src.tools.audio import PydubTool

        with tempfile.TemporaryDirectory() as tmpdir:
            tool = PydubTool(output_dir=tmpdir)
            assert tool.output_dir == Path(tmpdir)

    def test_pydub_available_property(self):
        """Test available property."""
        from src.tools.audio import PydubTool, PYDUB_AVAILABLE

        tool = PydubTool()
        assert tool.available == PYDUB_AVAILABLE


class TestLibrosaTool:
    """Tests for LibrosaTool."""

    def test_librosa_tool_init(self):
        """Test LibrosaTool initialization."""
        from src.tools.audio import LibrosaTool

        tool = LibrosaTool()
        assert tool is not None

    def test_librosa_available_property(self):
        """Test available property."""
        from src.tools.audio import LibrosaTool, LIBROSA_AVAILABLE

        tool = LibrosaTool()
        assert tool.available == LIBROSA_AVAILABLE


class TestWhisperTool:
    """Tests for WhisperTool."""

    def test_whisper_tool_init(self):
        """Test WhisperTool initialization."""
        from src.tools.audio import WhisperTool

        with tempfile.TemporaryDirectory() as tmpdir:
            tool = WhisperTool(model_name="tiny", output_dir=tmpdir)
            assert tool.model_name == "tiny"
            assert tool.output_dir == Path(tmpdir)

    def test_whisper_available_property(self):
        """Test available property."""
        from src.tools.audio import WhisperTool, WHISPER_AVAILABLE

        tool = WhisperTool()
        assert tool.available == WHISPER_AVAILABLE

    def test_format_srt_time(self):
        """Test SRT time formatting."""
        from src.tools.audio import WhisperTool

        tool = WhisperTool()

        # Test various time formats
        assert tool._format_srt_time(0) == "00:00:00,000"
        assert tool._format_srt_time(1.5) == "00:00:01,500"
        assert tool._format_srt_time(61.25) == "00:01:01,250"
        # Test hour-range timestamp with exact integer value
        assert tool._format_srt_time(3662.0) == "01:01:02,000"


class TestPillowTool:
    """Tests for PillowTool."""

    def test_pillow_tool_init(self):
        """Test PillowTool initialization."""
        from src.tools.image import PillowTool

        with tempfile.TemporaryDirectory() as tmpdir:
            tool = PillowTool(output_dir=tmpdir)
            assert tool.output_dir == Path(tmpdir)
            assert tool.output_dir.exists()

    def test_pillow_available_property(self):
        """Test available property."""
        from src.tools.image import PillowTool, PILLOW_AVAILABLE

        tool = PillowTool()
        assert tool.available == PILLOW_AVAILABLE


class TestOpenCVTool:
    """Tests for OpenCVTool."""

    def test_opencv_tool_init(self):
        """Test OpenCVTool initialization."""
        from src.tools.image import OpenCVTool

        with tempfile.TemporaryDirectory() as tmpdir:
            tool = OpenCVTool(output_dir=tmpdir)
            assert tool.output_dir == Path(tmpdir)

    def test_opencv_available_property(self):
        """Test available property."""
        from src.tools.image import OpenCVTool, OPENCV_AVAILABLE

        tool = OpenCVTool()
        assert tool.available == OPENCV_AVAILABLE


class TestRembgTool:
    """Tests for RembgTool."""

    def test_rembg_tool_init(self):
        """Test RembgTool initialization."""
        from src.tools.image import RembgTool

        with tempfile.TemporaryDirectory() as tmpdir:
            tool = RembgTool(output_dir=tmpdir)
            assert tool.output_dir == Path(tmpdir)

    def test_rembg_available_property(self):
        """Test available property."""
        from src.tools.image import RembgTool, REMBG_AVAILABLE

        tool = RembgTool()
        assert tool.available == REMBG_AVAILABLE


class TestSpacyTool:
    """Tests for SpacyTool."""

    def test_spacy_tool_init(self):
        """Test SpacyTool initialization."""
        from src.tools.nlp import SpacyTool

        tool = SpacyTool()
        assert tool.model_name == "en_core_web_sm"

        tool = SpacyTool(model_name="en_core_web_md")
        assert tool.model_name == "en_core_web_md"

    def test_spacy_tool_invalid_model_name(self):
        """Test SpacyTool rejects invalid model names."""
        from src.tools.nlp import SpacyTool

        with pytest.raises(ValueError):
            SpacyTool(model_name="invalid_model")

        with pytest.raises(ValueError):
            SpacyTool(model_name="../etc/passwd")

    def test_spacy_available_property(self):
        """Test available property."""
        from src.tools.nlp import SpacyTool, SPACY_AVAILABLE

        tool = SpacyTool()
        assert tool.available == SPACY_AVAILABLE


class TestDeepFaceTool:
    """Tests for DeepFaceTool."""

    def test_deepface_tool_init(self):
        """Test DeepFaceTool initialization."""
        from src.tools.face import DeepFaceTool

        tool = DeepFaceTool()
        assert tool is not None

    def test_deepface_available_property(self):
        """Test available property."""
        from src.tools.face import DeepFaceTool, DEEPFACE_AVAILABLE

        tool = DeepFaceTool()
        assert tool.available == DEEPFACE_AVAILABLE


class TestToolsModuleImport:
    """Tests for tools module imports."""

    def test_all_tools_importable(self):
        """Test that all tools can be imported from the module."""
        from src.tools import (
            FFmpegTool,
            MoviePyTool,
            PydubTool,
            LibrosaTool,
            WhisperTool,
            PillowTool,
            OpenCVTool,
            RembgTool,
            SpacyTool,
            DeepFaceTool,
        )

        # Verify all classes are importable
        assert FFmpegTool is not None
        assert MoviePyTool is not None
        assert PydubTool is not None
        assert LibrosaTool is not None
        assert WhisperTool is not None
        assert PillowTool is not None
        assert OpenCVTool is not None
        assert RembgTool is not None
        assert SpacyTool is not None
        assert DeepFaceTool is not None

    def test_module_all_exports(self):
        """Test that __all__ is properly defined."""
        from src import tools

        expected_exports = [
            "FFmpegTool",
            "MoviePyTool",
            "PydubTool",
            "LibrosaTool",
            "WhisperTool",
            "PillowTool",
            "OpenCVTool",
            "RembgTool",
            "SpacyTool",
            "DeepFaceTool",
        ]

        for export in expected_exports:
            assert export in tools.__all__
