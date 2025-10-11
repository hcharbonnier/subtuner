"""Unit tests for the OptimizationEngine"""

import pytest

from subtuner.config import OptimizationConfig
from subtuner.optimization.engine import OptimizationEngine, OptimizationResult
from subtuner.parsers.base import Subtitle


class TestOptimizationEngine:
    """Test cases for OptimizationEngine"""
    
    def test_engine_initialization(self):
        """Test that engine initializes correctly"""
        engine = OptimizationEngine()
        
        assert engine.duration_adjuster is not None
        assert engine.rebalancer is not None
        assert engine.anticipator is not None
        assert engine.validator is not None
    
    def test_optimize_empty_list(self, default_config):
        """Test optimization with empty subtitle list"""
        engine = OptimizationEngine()
        
        result = engine.optimize([], default_config)
        
        assert isinstance(result, OptimizationResult)
        assert result.subtitles == []
        assert result.original_count == 0
        assert result.final_count == 0
        assert not result.success  # Empty result is not success
    
    def test_optimize_single_subtitle(self, default_config, single_subtitle):
        """Test optimization with single subtitle"""
        engine = OptimizationEngine()
        
        result = engine.optimize([single_subtitle], default_config)
        
        assert isinstance(result, OptimizationResult)
        assert len(result.subtitles) == 1
        assert result.original_count == 1
        assert result.final_count == 1
        assert result.success
    
    def test_optimize_full_sequence(self, default_config, sample_subtitles):
        """Test optimization with full subtitle sequence"""
        engine = OptimizationEngine()
        
        result = engine.optimize(sample_subtitles, default_config)
        
        assert isinstance(result, OptimizationResult)
        assert len(result.subtitles) <= len(sample_subtitles)  # May remove invalid ones
        assert result.original_count == len(sample_subtitles)
        assert result.final_count == len(result.subtitles)
        assert result.success
        
        # Statistics should be populated
        assert result.statistics.original_subtitle_count == len(sample_subtitles)
        assert result.statistics.processing_time > 0
    
    def test_statistics_tracking(self, default_config, sample_subtitles):
        """Test that statistics are properly tracked"""
        engine = OptimizationEngine()
        
        result = engine.optimize(sample_subtitles, default_config, track_index=5)
        
        stats = result.statistics
        assert stats.track_index == 5
        assert stats.original_subtitle_count == len(sample_subtitles)
        assert stats.final_subtitle_count == len(result.subtitles)
        assert stats.processing_time > 0
        assert stats.total_modifications >= 0
    
    def test_optimization_maintains_order(self, default_config, sample_subtitles):
        """Test that optimization maintains chronological order"""
        engine = OptimizationEngine()
        
        result = engine.optimize(sample_subtitles, default_config)
        
        # Check chronological order
        for i in range(len(result.subtitles) - 1):
            assert result.subtitles[i].start_time <= result.subtitles[i + 1].start_time
    
    def test_optimization_preserves_text(self, default_config, sample_subtitles):
        """Test that optimization preserves subtitle text"""
        engine = OptimizationEngine()
        
        original_texts = [sub.text for sub in sample_subtitles]
        result = engine.optimize(sample_subtitles, default_config)
        
        # Text should be preserved (though order might change due to removal)
        result_texts = [sub.text for sub in result.subtitles]
        for text in result_texts:
            assert text in original_texts
    
    def test_analyze_subtitles(self, default_config, sample_subtitles):
        """Test subtitle analysis functionality"""
        engine = OptimizationEngine()
        
        analysis = engine.analyze_subtitles(sample_subtitles, default_config)
        
        assert 'total_subtitles' in analysis
        assert 'duration_stats' in analysis
        assert 'gap_stats' in analysis
        assert 'reading_speed_stats' in analysis
        assert 'optimization_potential' in analysis
        
        assert analysis['total_subtitles'] == len(sample_subtitles)
    
    def test_analyze_empty_subtitles(self, default_config):
        """Test analysis with empty subtitle list"""
        engine = OptimizationEngine()
        
        analysis = engine.analyze_subtitles([], default_config)
        
        assert 'error' in analysis
    
    def test_preview_optimization(self, default_config, sample_subtitles):
        """Test optimization preview functionality"""
        engine = OptimizationEngine()
        
        preview = engine.preview_optimization(sample_subtitles, default_config, sample_size=2)
        
        assert 'sample_size' in preview
        assert 'total_subtitles' in preview
        assert 'previews' in preview
        assert preview['total_subtitles'] == len(sample_subtitles)
        assert len(preview['previews']) <= 2
    
    def test_preview_empty_subtitles(self, default_config):
        """Test preview with empty subtitle list"""
        engine = OptimizationEngine()
        
        preview = engine.preview_optimization([], default_config)
        
        assert 'error' in preview
    
    def test_get_algorithm_info(self):
        """Test algorithm information retrieval"""
        engine = OptimizationEngine()
        
        info = engine.get_algorithm_info()
        
        assert 'algorithms' in info
        assert 'execution_order' in info
        assert 'principles' in info
        assert len(info['algorithms']) == 4  # Four algorithms
        
        # Check algorithm phases
        phases = [alg['phase'] for alg in info['algorithms']]
        assert phases == [1, 2, 3, 4]  # Sequential phases
    
    def test_optimization_result_properties(self, default_config, sample_subtitles):
        """Test OptimizationResult properties"""
        engine = OptimizationEngine()
        
        result = engine.optimize(sample_subtitles, default_config)
        
        # Test success property
        assert result.success == (len(result.subtitles) > 0)
        
        # Test improvement summary
        summary = result.improvement_summary
        assert 'total_modifications' in summary
        assert 'modification_percentage' in summary
        assert 'processing_time' in summary
        assert 'subtitles_retained' in summary
        assert 'subtitles_removed' in summary
        
        assert summary['subtitles_retained'] == result.final_count
        assert summary['subtitles_removed'] == result.original_count - result.final_count


class TestOptimizationPipeline:
    """Test the complete optimization pipeline"""
    
    def test_pipeline_with_various_configs(self, sample_subtitles):
        """Test pipeline with different configurations"""
        engine = OptimizationEngine()
        
        configs = [
            OptimizationConfig(),  # Default
            OptimizationConfig(chars_per_sec=15.0),  # Slow reading
            OptimizationConfig(chars_per_sec=25.0),  # Fast reading
            OptimizationConfig(min_duration=1.5, max_duration=6.0),  # Strict durations
            OptimizationConfig(max_anticipation=0.0),  # No anticipation
        ]
        
        for config in configs:
            result = engine.optimize(sample_subtitles, config)
            assert result.success
            assert len(result.subtitles) <= len(sample_subtitles)
    
    def test_pipeline_edge_cases(self, default_config):
        """Test pipeline with edge cases"""
        engine = OptimizationEngine()
        
        # Very short subtitle
        very_short = [Subtitle(0, 10.0, 10.1, "Hi", {})]
        result = engine.optimize(very_short, default_config)
        assert result.success
        
        # Very long subtitle
        very_long_text = "A" * 500
        very_long = [Subtitle(0, 10.0, 11.0, very_long_text, {})]
        result = engine.optimize(very_long, default_config)
        assert result.success
        
        # Overlapping subtitles
        overlapping = [
            Subtitle(0, 10.0, 12.0, "First", {}),
            Subtitle(1, 11.0, 13.0, "Overlapping", {}),
        ]
        result = engine.optimize(overlapping, default_config)
        assert result.success
    
    def test_pipeline_preserves_metadata(self, default_config):
        """Test that pipeline preserves subtitle metadata"""
        engine = OptimizationEngine()
        
        subtitles = [
            Subtitle(0, 10.0, 11.0, "Test", {'format': 'srt', 'custom': 'data'}),
            Subtitle(1, 12.0, 13.0, "Test2", {'format': 'vtt', 'style': 'bold'}),
        ]
        
        result = engine.optimize(subtitles, default_config)
        
        # Metadata should be preserved
        for subtitle in result.subtitles:
            assert 'format' in subtitle.metadata
    
    def test_pipeline_performance(self, default_config):
        """Test pipeline performance with large subtitle set"""
        engine = OptimizationEngine()
        
        # Create large subtitle set
        large_set = []
        for i in range(100):
            large_set.append(Subtitle(
                index=i,
                start_time=i * 2.0,
                end_time=i * 2.0 + 1.0,
                text=f"Subtitle {i}",
                metadata={'format': 'srt'}
            ))
        
        result = engine.optimize(large_set, default_config)
        
        assert result.success
        assert result.statistics.processing_time < 10.0  # Should be fast
        assert len(result.subtitles) == len(large_set)  # All should be valid


class TestAnalysisFeatures:
    """Test analysis and preview features"""
    
    def test_duration_analysis(self, default_config, sample_subtitles):
        """Test duration statistics analysis"""
        engine = OptimizationEngine()
        
        analysis = engine.analyze_subtitles(sample_subtitles, default_config)
        duration_stats = analysis['duration_stats']
        
        assert 'min' in duration_stats
        assert 'max' in duration_stats
        assert 'avg' in duration_stats
        assert 'below_min' in duration_stats
        assert 'above_max' in duration_stats
        assert 'total_duration' in duration_stats
        
        # Values should be reasonable
        assert duration_stats['min'] >= 0
        assert duration_stats['max'] >= duration_stats['min']
        assert duration_stats['avg'] > 0
    
    def test_gap_analysis(self, default_config, sample_subtitles):
        """Test gap statistics analysis"""
        engine = OptimizationEngine()
        
        analysis = engine.analyze_subtitles(sample_subtitles, default_config)
        gap_stats = analysis['gap_stats']
        
        assert 'min_gap' in gap_stats
        assert 'max_gap' in gap_stats
        assert 'avg_gap' in gap_stats
        assert 'overlaps' in gap_stats
        assert 'below_min_gap' in gap_stats
        assert 'negative_gaps' in gap_stats
        
        # Values should be consistent
        assert gap_stats['overlaps'] == gap_stats['negative_gaps']
    
    def test_reading_speed_analysis(self, default_config, sample_subtitles):
        """Test reading speed analysis"""
        engine = OptimizationEngine()
        
        analysis = engine.analyze_subtitles(sample_subtitles, default_config)
        speed_stats = analysis['reading_speed_stats']
        
        assert 'min_speed' in speed_stats
        assert 'max_speed' in speed_stats
        assert 'avg_speed' in speed_stats
        assert 'target_speed' in speed_stats
        assert 'above_target' in speed_stats
        assert 'below_target' in speed_stats
        
        # Target speed should match config
        assert speed_stats['target_speed'] == default_config.chars_per_sec
    
    def test_optimization_potential_analysis(self, default_config, sample_subtitles):
        """Test optimization potential analysis"""
        engine = OptimizationEngine()
        
        analysis = engine.analyze_subtitles(sample_subtitles, default_config)
        potential = analysis['optimization_potential']
        
        assert 'anticipation' in potential
        assert 'validation' in potential
        
        # Anticipation potential should have expected fields
        anticipation = potential['anticipation']
        assert 'total_subtitles' in anticipation
        assert 'anticipatable_count' in anticipation
        
        # Validation should have violations breakdown
        validation = potential['validation']
        assert 'total_subtitles' in validation
        assert 'valid_subtitles' in validation
        assert 'violations' in validation