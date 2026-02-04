"""
Tests for Baby Tools

These tests verify that baby tools can be imported and instantiated.
"""

import pytest
from pathlib import Path


class TestBabyToolsImport:
    """Test that all baby tools can be imported."""
    
    def test_import_baby_canva(self):
        """Test BabyCanva import."""
        from src.tools.baby_design import BabyCanva
        assert BabyCanva is not None
    
    def test_import_baby_capcut(self):
        """Test BabyCapCut import."""
        from src.tools.baby_video_editor import BabyCapCut
        assert BabyCapCut is not None
    
    def test_import_baby_opusclip(self):
        """Test BabyOpusClip import."""
        from src.tools.baby_clips import BabyOpusClip
        assert BabyOpusClip is not None
    
    def test_import_baby_analytics(self):
        """Test BabyAnalytics import."""
        from src.tools.baby_analytics import BabyAnalytics
        assert BabyAnalytics is not None


class TestBabyCanva:
    """Test BabyCanva functionality."""
    
    def test_instantiate(self):
        """Test BabyCanva instantiation."""
        from src.tools.baby_design import BabyCanva
        canva = BabyCanva(output_dir="./test_output/designs")
        assert canva is not None
        assert canva.output_dir.exists()
    
    def test_platform_dimensions(self):
        """Test that platform dimensions are defined."""
        from src.tools.baby_design import BabyCanva
        canva = BabyCanva()
        assert 'instagram_post' in canva.DIMENSIONS
        assert 'tiktok' in canva.DIMENSIONS
        assert 'youtube_thumbnail' in canva.DIMENSIONS


class TestBabyCapCut:
    """Test BabyCapCut functionality."""
    
    def test_instantiate(self):
        """Test BabyCapCut instantiation."""
        from src.tools.baby_video_editor import BabyCapCut
        editor = BabyCapCut(output_dir="./test_output/videos")
        assert editor is not None
        assert editor.output_dir.exists()
    
    def test_platform_sizes(self):
        """Test that platform sizes are defined."""
        from src.tools.baby_video_editor import BabyCapCut
        editor = BabyCapCut()
        assert 'tiktok' in editor.PLATFORM_SIZES
        assert 'youtube_short' in editor.PLATFORM_SIZES


class TestBabyOpusClip:
    """Test BabyOpusClip functionality."""
    
    def test_instantiate(self):
        """Test BabyOpusClip instantiation."""
        from src.tools.baby_clips import BabyOpusClip
        clipper = BabyOpusClip(output_dir="./test_output/clips")
        assert clipper is not None
        assert clipper.output_dir.exists()


class TestBabyAnalytics:
    """Test BabyAnalytics functionality."""
    
    def test_instantiate(self):
        """Test BabyAnalytics instantiation."""
        from src.tools.baby_analytics import BabyAnalytics
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_analytics.db")
            analytics = BabyAnalytics(db_path=db_path)
            assert analytics is not None
    
    def test_track_event(self):
        """Test event tracking."""
        from src.tools.baby_analytics import BabyAnalytics
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_analytics.db")
            analytics = BabyAnalytics(db_path=db_path)
            
            result = analytics.track_event(
                event_type='pageview',
                page_url='/test',
                session_id='test_session'
            )
            assert result is True
    
    def test_get_summary(self):
        """Test getting summary stats."""
        from src.tools.baby_analytics import BabyAnalytics
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_analytics.db")
            analytics = BabyAnalytics(db_path=db_path)
            
            # Track some events
            analytics.track_pageview('/page1', session_id='session1')
            analytics.track_pageview('/page2', session_id='session1')
            analytics.track_event('click', page_url='/page1', session_id='session1')
            
            summary = analytics.get_summary()
            assert 'total_events' in summary
            assert 'pageviews' in summary
            assert summary['total_events'] >= 3
            assert summary['pageviews'] >= 2


class TestBabyToolsIntegration:
    """Test that baby tools work together."""
    
    def test_import_from_tools_package(self):
        """Test importing from main tools package."""
        from src.tools import BabyCanva, BabyCapCut, BabyOpusClip, BabyAnalytics
        
        assert BabyCanva is not None
        assert BabyCapCut is not None
        assert BabyOpusClip is not None
        assert BabyAnalytics is not None
