"""Integration tests for SubTuner end-to-end workflow"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from subtuner.cli import SubTunerCLI
from subtuner.config import GlobalConfig, OptimizationConfig, ProcessingConfig
from subtuner.parsers.base import Subtitle
from subtuner.video.analyzer import SubtitleTrackInfo


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield tmp_dir
    
    @pytest.fixture
    def mock_video_file(self, temp_dir):
        """Create a mock video file for testing"""
        video_path = Path(temp_dir) / "test_video.mkv"
        video_path.write_text("fake video content")  # Just create the file
        return str(video_path)
    
    @pytest.fixture
    def sample_srt_content(self):
        """Sample SRT content for testing"""
        return """1
00:00:10,000 --> 00:00:10,500
Hi!

2
00:00:12,000 --> 00:00:16,000
This is a much longer subtitle with more content to read.

3
00:00:17,000 --> 00:00:17,800
Quick

4
00:00:20,000 --> 00:00:22,500
Normal length subtitle
"""
    
    @pytest.fixture
    def mock_subtitle_tracks(self):
        """Mock subtitle track information"""
        return [
            SubtitleTrackInfo(
                index=0,
                codec='subrip',
                language='eng',
                title='English',
                default=True,
                forced=False
            )
        ]
    
    def test_single_video_processing_success(self, temp_dir, mock_video_file, 
                                           sample_srt_content, mock_subtitle_tracks):
        """Test successful processing of a single video"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False) as srt_file:
            srt_file.write(sample_srt_content)
            srt_file.flush()
            
            try:
                config = GlobalConfig(
                    optimization=OptimizationConfig(),
                    processing=ProcessingConfig(output_dir=temp_dir, quiet=True)
                )
                
                cli = SubTunerCLI(config)
                
                # Mock the video analyzer and extractor
                with patch.object(cli.video_analyzer, 'analyze_video', return_value=mock_subtitle_tracks), \
                     patch.object(cli.extractor, 'extract_track', return_value=srt_file.name):
                    
                    result = cli.process_single_video(mock_video_file)
                    
                    assert result['status'] == 'success'
                    assert len(result['tracks']) == 1
                    
                    track_result = result['tracks'][0]
                    assert track_result['status'] == 'success'
                    assert track_result['original_count'] > 0
                    assert track_result['optimized_count'] > 0
                    assert 'statistics' in track_result
                    
            finally:
                # Clean up
                if os.path.exists(srt_file.name):
                    os.unlink(srt_file.name)
    
    def test_single_video_no_subtitle_tracks(self, mock_video_file):
        """Test processing video with no subtitle tracks"""
        config = GlobalConfig(
            optimization=OptimizationConfig(),
            processing=ProcessingConfig(quiet=True)
        )
        
        cli = SubTunerCLI(config)
        
        # Mock video analyzer to return no tracks
        with patch.object(cli.video_analyzer, 'analyze_video', return_value=[]):
            result = cli.process_single_video(mock_video_file)
            
            assert result['status'] == 'no_tracks'
            assert len(result['tracks']) == 0
    
    def test_batch_processing(self, temp_dir, sample_srt_content, mock_subtitle_tracks):
        """Test batch processing of multiple videos"""
        # Create multiple mock video files
        video_files = []
        srt_files = []
        
        for i in range(3):
            video_path = Path(temp_dir) / f"video_{i}.mkv"
            video_path.write_text(f"fake video content {i}")
            video_files.append(str(video_path))
            
            # Create corresponding SRT file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False) as srt_file:
                srt_file.write(sample_srt_content)
                srt_files.append(srt_file.name)
        
        try:
            config = GlobalConfig(
                optimization=OptimizationConfig(),
                processing=ProcessingConfig(output_dir=temp_dir, quiet=True)
            )
            
            cli = SubTunerCLI(config)
            
            # Mock analyzer and extractor
            with patch.object(cli.video_analyzer, 'analyze_video', return_value=mock_subtitle_tracks), \
                 patch.object(cli.extractor, 'extract_track', side_effect=srt_files):
                
                result = cli.process_batch_videos(video_files)
                
                assert result['type'] == 'batch'
                assert result['summary']['total'] == 3
                assert result['summary']['successful'] >= 0
                assert len(result['results']) == 3
                
        finally:
            # Clean up SRT files
            for srt_file in srt_files:
                if os.path.exists(srt_file):
                    os.unlink(srt_file)
    
    def test_dry_run_mode(self, temp_dir, mock_video_file, sample_srt_content, mock_subtitle_tracks):
        """Test dry run mode (no files written)"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False) as srt_file:
            srt_file.write(sample_srt_content)
            srt_file.flush()
            
            try:
                config = GlobalConfig(
                    optimization=OptimizationConfig(),
                    processing=ProcessingConfig(output_dir=temp_dir, dry_run=True, quiet=True)
                )
                
                cli = SubTunerCLI(config)
                
                with patch.object(cli.video_analyzer, 'analyze_video', return_value=mock_subtitle_tracks), \
                     patch.object(cli.extractor, 'extract_track', return_value=srt_file.name):
                    
                    result = cli.process_single_video(mock_video_file)
                    
                    assert result['status'] == 'success'
                    
                    # In dry run, output_path should be None
                    track_result = result['tracks'][0]
                    assert track_result['output_path'] is None
                    
                    # Should still have statistics
                    assert 'statistics' in track_result
                    
            finally:
                if os.path.exists(srt_file.name):
                    os.unlink(srt_file.name)
    
    def test_error_handling(self, mock_video_file):
        """Test error handling in CLI"""
        config = GlobalConfig(
            optimization=OptimizationConfig(),
            processing=ProcessingConfig(quiet=True)
        )
        
        cli = SubTunerCLI(config)
        
        # Mock video analyzer to raise exception
        with patch.object(cli.video_analyzer, 'analyze_video', 
                         side_effect=Exception("Mock error")):
            
            result = cli.process_single_video(mock_video_file)
            
            assert result['status'] == 'error'
            assert 'error' in result
            assert len(result['tracks']) == 0
    
    def test_configuration_validation(self):
        """Test that invalid configurations are rejected"""
        with pytest.raises(Exception):  # Should raise ConfigurationError
            OptimizationConfig(
                chars_per_sec=100.0,  # Invalid: too high
                min_duration=5.0,
                max_duration=2.0      # Invalid: min > max
            )
    
    def test_report_generation(self, temp_dir, mock_video_file, sample_srt_content, mock_subtitle_tracks):
        """Test report generation and saving"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False) as srt_file:
            srt_file.write(sample_srt_content)
            srt_file.flush()
            
            try:
                config = GlobalConfig(
                    optimization=OptimizationConfig(),
                    processing=ProcessingConfig(output_dir=temp_dir, quiet=True)
                )
                
                cli = SubTunerCLI(config)
                
                with patch.object(cli.video_analyzer, 'analyze_video', return_value=mock_subtitle_tracks), \
                     patch.object(cli.extractor, 'extract_track', return_value=srt_file.name):
                    
                    # Process video
                    result = cli.process_single_video(mock_video_file)
                    
                    # Test report generation
                    from subtuner.statistics.reporter import ReportFormat
                    
                    # Should not raise exception
                    cli.generate_reports(result, ReportFormat.CONSOLE)
                    
                    # Test saving report
                    report_path = Path(temp_dir) / "test_report.json"
                    cli.generate_reports(result, ReportFormat.JSON, str(report_path))
                    
                    # Report file should be created
                    assert report_path.exists()
                    assert report_path.stat().st_size > 0
                    
            finally:
                if os.path.exists(srt_file.name):
                    os.unlink(srt_file.name)


class TestParserWriterIntegration:
    """Test parser and writer integration"""
    
    def test_srt_parse_write_cycle(self, temp_dir, sample_srt_content):
        """Test parsing SRT and writing it back"""
        from subtuner.parsers.srt_parser import SRTParser
        from subtuner.writers.srt_writer import SRTWriter
        from subtuner.optimization.engine import OptimizationEngine
        
        # Create input file
        input_path = Path(temp_dir) / "input.srt"
        input_path.write_text(sample_srt_content, encoding='utf-8')
        
        # Parse
        parser = SRTParser()
        subtitles = parser.parse(str(input_path))
        
        assert len(subtitles) > 0
        
        # Optimize
        engine = OptimizationEngine()
        result = engine.optimize(subtitles, OptimizationConfig())
        
        # Write back
        output_path = Path(temp_dir) / "output.srt"
        writer = SRTWriter()
        writer.write(result.subtitles, str(output_path))
        
        # Verify file was created
        assert output_path.exists()
        assert output_path.stat().st_size > 0
        
        # Parse again to verify integrity
        parsed_again = parser.parse(str(output_path))
        assert len(parsed_again) == len(result.subtitles)
    
    def test_format_detection_and_writing(self, temp_dir):
        """Test format detection and appropriate writer selection"""
        from subtuner.parsers.base import get_parser_for_file
        from subtuner.writers.base import get_writer_for_format
        
        # Create different format files
        srt_path = Path(temp_dir) / "test.srt"
        vtt_path = Path(temp_dir) / "test.vtt"
        ass_path = Path(temp_dir) / "test.ass"
        
        srt_path.write_text("1\n00:00:01,000 --> 00:00:02,000\nTest\n", encoding='utf-8')
        vtt_path.write_text("WEBVTT\n\n00:01.000 --> 00:02.000\nTest\n", encoding='utf-8')
        ass_path.write_text("[V4+ Styles]\nFormat: Name, Fontname\nStyle: Default,Arial\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\nDialogue: 0,0:00:01.00,0:00:02.00,Default,,0,0,0,,Test\n", encoding='utf-8')
        
        # Test parser detection
        srt_parser = get_parser_for_file(str(srt_path))
        vtt_parser = get_parser_for_file(str(vtt_path))
        ass_parser = get_parser_for_file(str(ass_path))
        
        assert srt_parser is not None
        assert vtt_parser is not None
        assert ass_parser is not None
        
        # Test writer detection
        srt_writer = get_writer_for_format('srt')
        vtt_writer = get_writer_for_format('vtt')
        ass_writer = get_writer_for_format('ass')
        
        assert srt_writer is not None
        assert vtt_writer is not None
        assert ass_writer is not None


class TestConfigurationIntegration:
    """Test configuration system integration"""
    
    def test_config_from_cli_args(self):
        """Test configuration creation from CLI arguments"""
        args = {
            'chars_per_sec': 25.0,
            'max_duration': 6.0,
            'min_duration': 1.5,
            'output_dir': '/tmp/test',
            'dry_run': True,
            'verbose': True
        }
        
        config = GlobalConfig.from_args(**args)
        
        assert config.optimization.chars_per_sec == 25.0
        assert config.optimization.max_duration == 6.0
        assert config.optimization.min_duration == 1.5
        assert config.processing.output_dir == '/tmp/test'
        assert config.processing.dry_run == True
        assert config.processing.verbose == True
    
    def test_config_validation_integration(self):
        """Test that configuration validation works in practice"""
        # Valid configuration should work
        valid_config = GlobalConfig(
            optimization=OptimizationConfig(chars_per_sec=20.0),
            processing=ProcessingConfig()
        )
        assert valid_config.optimization.chars_per_sec == 20.0
        
        # Invalid configuration should fail
        with pytest.raises(Exception):
            OptimizationConfig(
                chars_per_sec=5.0,  # Too low
                min_duration=10.0,  # Too high
                max_duration=5.0    # Less than min
            )


class TestErrorHandling:
    """Test error handling across the system"""
    
    def test_missing_ffmpeg_handling(self):
        """Test handling when FFmpeg is not available"""
        from subtuner.video.analyzer import VideoAnalyzer
        from subtuner.errors import FFmpegError
        
        # Try to create analyzer with non-existent path
        with pytest.raises(FFmpegError):
            VideoAnalyzer(ffprobe_path="/nonexistent/path")
    
    def test_invalid_video_file_handling(self, temp_dir):
        """Test handling of invalid video files"""
        from subtuner.video.analyzer import VideoAnalyzer
        from subtuner.errors import VideoAnalysisError
        
        # Create non-video file
        fake_video = Path(temp_dir) / "fake.mkv"
        fake_video.write_text("not a video")
        
        # Mock VideoAnalyzer to avoid requiring real FFmpeg
        analyzer = VideoAnalyzer()
        
        # Should handle gracefully
        with patch.object(analyzer, 'analyze_video', side_effect=VideoAnalysisError("Invalid video")):
            config = GlobalConfig(
                optimization=OptimizationConfig(),
                processing=ProcessingConfig(quiet=True)
            )
            cli = SubTunerCLI(config)
            
            result = cli.process_single_video(str(fake_video))
            assert result['status'] == 'error'
    
    def test_parsing_error_handling(self, temp_dir):
        """Test handling of subtitle parsing errors"""
        from subtuner.parsers.srt_parser import SRTParser
        from subtuner.errors import ParsingError
        
        # Create malformed SRT file
        malformed_srt = Path(temp_dir) / "malformed.srt"
        malformed_srt.write_text("This is not valid SRT content", encoding='utf-8')
        
        parser = SRTParser()
        
        # Should raise ParsingError
        with pytest.raises(ParsingError):
            parser.parse(str(malformed_srt))
    
    def test_writing_permission_error_handling(self, temp_dir):
        """Test handling of writing permission errors"""
        from subtuner.writers.srt_writer import SRTWriter
        from subtuner.errors import WritingError
        
        writer = SRTWriter()
        subtitles = [Subtitle(0, 1.0, 2.0, "Test", {})]
        
        # Try to write to non-existent directory with no permissions
        invalid_path = "/root/nonexistent/test.srt"  # Assuming no write access
        
        with patch('builtins.open', side_effect=PermissionError("No permission")):
            with pytest.raises(WritingError):
                writer.write(subtitles, invalid_path)


class TestPerformanceIntegration:
    """Test performance characteristics"""
    
    def test_large_subtitle_set_performance(self, default_config):
        """Test performance with large subtitle sets"""
        from subtuner.optimization.engine import OptimizationEngine
        
        # Create large subtitle set (simulating 2-hour movie)
        large_subtitles = []
        for i in range(2000):
            start_time = i * 3.6  # Every 3.6 seconds
            end_time = start_time + 2.0
            text = f"Subtitle number {i} with some content to read"
            
            large_subtitles.append(Subtitle(
                index=i,
                start_time=start_time,
                end_time=end_time,
                text=text,
                metadata={'format': 'srt'}
            ))
        
        engine = OptimizationEngine()
        
        # Measure processing time
        import time
        start = time.time()
        result = engine.optimize(large_subtitles, default_config)
        processing_time = time.time() - start
        
        # Should complete in reasonable time
        assert processing_time < 10.0  # Less than 10 seconds
        assert result.success
        assert len(result.subtitles) > 0
        
        # Performance should be logged in statistics
        assert result.statistics.processing_time < processing_time  # Internal timing should be available
    
    def test_memory_efficiency(self, default_config):
        """Test memory usage with large datasets"""
        from subtuner.optimization.engine import OptimizationEngine
        
        # Create very large subtitle set
        huge_subtitles = []
        for i in range(5000):
            huge_subtitles.append(Subtitle(
                index=i,
                start_time=i * 2.0,
                end_time=i * 2.0 + 1.5,
                text=f"Subtitle {i}",
                metadata={'format': 'srt'}
            ))
        
        engine = OptimizationEngine()
        
        # This should complete without memory errors
        result = engine.optimize(huge_subtitles, default_config)
        assert result.success


class TestRealWorldScenarios:
    """Test real-world usage scenarios"""
    
    def test_anime_fast_dialogue_scenario(self, temp_dir):
        """Test optimization for anime with fast dialogue"""
        # Create subtitles simulating anime dialogue
        anime_subtitles = [
            Subtitle(0, 1.0, 1.3, "Ah!", {}),                    # Very short
            Subtitle(1, 2.0, 2.5, "What?!", {}),                 # Short
            Subtitle(2, 3.0, 3.4, "No way!", {}),                # Short
            Subtitle(3, 4.0, 7.0, "This is a longer explanation that takes more time", {}),  # Long
            Subtitle(4, 8.0, 8.2, "Oh!", {}),                    # Very short
        ]
        
        # Use config optimized for fast dialogue
        config = OptimizationConfig(
            chars_per_sec=22.0,      # Faster reading
            min_duration=0.8,        # Shorter minimum
            max_anticipation=0.6     # More anticipation
        )
        
        from subtuner.optimization.engine import OptimizationEngine
        engine = OptimizationEngine()
        
        result = engine.optimize(anime_subtitles, config)
        
        assert result.success
        # Should have optimized short subtitles
        assert result.statistics.duration_adjustments > 0
    
    def test_documentary_slow_reading_scenario(self):
        """Test optimization for documentary with slow reading requirements"""
        # Create subtitles for documentary
        doc_subtitles = [
            Subtitle(0, 1.0, 3.0, "In the beginning...", {}),
            Subtitle(1, 5.0, 8.0, "The documentary explores complex scientific concepts.", {}),
            Subtitle(2, 10.0, 12.0, "Research shows interesting findings.", {}),
        ]
        
        # Use config for slower reading
        config = OptimizationConfig(
            chars_per_sec=15.0,      # Slower reading
            min_duration=2.0,        # Longer minimum
            max_duration=10.0,       # Allow longer subtitles
            max_anticipation=0.2     # Less anticipation
        )
        
        from subtuner.optimization.engine import OptimizationEngine
        engine = OptimizationEngine()
        
        result = engine.optimize(doc_subtitles, config)
        
        assert result.success
        # All subtitles should meet minimum duration
        for subtitle in result.subtitles:
            assert subtitle.duration >= config.min_duration
    
    def test_accessibility_requirements(self):
        """Test optimization for accessibility requirements"""
        # Create subtitles that need accessibility optimization
        subtitles = [
            Subtitle(0, 1.0, 1.8, "Quick dialogue", {}),
            Subtitle(1, 3.0, 4.2, "Normal paced speech", {}),
            Subtitle(2, 5.0, 5.5, "Fast", {}),
        ]
        
        # Use accessibility-friendly config
        config = OptimizationConfig(
            chars_per_sec=12.0,      # Very slow reading
            min_duration=3.0,        # Long minimum display
            max_anticipation=0.0,    # No anticipation (predictable timing)
            min_gap=0.2             # Larger gaps
        )
        
        from subtuner.optimization.engine import OptimizationEngine
        engine = OptimizationEngine()
        
        result = engine.optimize(subtitles, config)
        
        assert result.success
        # All subtitles should meet accessibility requirements
        for subtitle in result.subtitles:
            assert subtitle.duration >= config.min_duration
        
        # Check gaps
        for i in range(len(result.subtitles) - 1):
            gap = result.subtitles[i + 1].start_time - result.subtitles[i].end_time
            assert gap >= config.min_gap


class TestEdgeCasesIntegration:
    """Test edge cases in integrated workflows"""
    
    def test_single_subtitle_file(self):
        """Test processing file with single subtitle"""
        single_subtitle = [Subtitle(0, 10.0, 11.0, "Only subtitle", {})]
        
        from subtuner.optimization.engine import OptimizationEngine
        engine = OptimizationEngine()
        
        result = engine.optimize(single_subtitle, OptimizationConfig())
        
        assert result.success
        assert len(result.subtitles) == 1
    
    def test_very_dense_subtitles(self):
        """Test processing very tightly packed subtitles"""
        # Create subtitles with minimal gaps
        dense_subtitles = []
        for i in range(10):
            start_time = i * 1.1
            end_time = start_time + 1.0
            dense_subtitles.append(Subtitle(i, start_time, end_time, f"Subtitle {i}", {}))
        
        from subtuner.optimization.engine import OptimizationEngine
        engine = OptimizationEngine()
        
        result = engine.optimize(dense_subtitles, OptimizationConfig())
        
        assert result.success
        # Should maintain minimum gaps
        for i in range(len(result.subtitles) - 1):
            gap = result.subtitles[i + 1].start_time - result.subtitles[i].end_time
            assert gap >= 0.05  # Default min_gap
    
    def test_unicode_content_handling(self, temp_dir):
        """Test handling of Unicode content in subtitles"""
        unicode_subtitles = [
            Subtitle(0, 1.0, 3.0, "Hello 世界 🌍", {}),
            Subtitle(1, 5.0, 7.0, "Café résumé naïve", {}),
            Subtitle(2, 10.0, 12.0, "Здравствуй мир", {}),
        ]
        
        from subtuner.optimization.engine import OptimizationEngine
        from subtuner.writers.srt_writer import SRTWriter
        
        engine = OptimizationEngine()
        result = engine.optimize(unicode_subtitles, OptimizationConfig())
        
        # Should handle Unicode correctly
        assert result.success
        
        # Test writing Unicode content
        output_path = Path(temp_dir) / "unicode.srt"
        writer = SRTWriter()
        writer.write(result.subtitles, str(output_path), encoding='utf-8')
        
        # File should be created and readable
        assert output_path.exists()
        content = output_path.read_text(encoding='utf-8')
        assert "世界" in content
        assert "Café" in content
        assert "Здравствуй" in content