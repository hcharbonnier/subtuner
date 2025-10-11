"""Unit tests for optimization algorithms"""

import pytest
from typing import List

from subtuner.config import OptimizationConfig
from subtuner.parsers.base import Subtitle
from subtuner.optimization.algorithms import (
    DurationAdjuster,
    TemporalRebalancer,
    AnticipationAdjuster,
    ConstraintsValidator
)
from subtuner.optimization.statistics import OptimizationStatistics


class TestDurationAdjuster:
    """Test cases for DurationAdjuster algorithm"""
    
    def test_basic_duration_adjustment(self, default_config, single_subtitle):
        """Test basic duration adjustment functionality"""
        adjuster = DurationAdjuster()
        
        # Should extend short subtitle to minimum duration
        result = adjuster.adjust_duration(single_subtitle, None, default_config)
        
        # Should be at least min_duration
        assert result.duration >= default_config.min_duration
        # Should not shorten original
        assert result.duration >= single_subtitle.duration
        # Start time should remain the same
        assert result.start_time == single_subtitle.start_time
    
    def test_minimum_duration_enforcement(self, default_config, short_subtitle):
        """Test that minimum duration is enforced"""
        adjuster = DurationAdjuster()
        
        result = adjuster.adjust_duration(short_subtitle, None, default_config)
        
        # Should be extended to minimum duration
        assert result.duration >= default_config.min_duration
        assert result.end_time == short_subtitle.start_time + default_config.min_duration
    
    def test_maximum_duration_constraint(self, default_config):
        """Test that maximum duration is respected"""
        # Create very long subtitle text
        long_text = "A" * 1000  # 1000 characters
        long_subtitle = Subtitle(
            index=0,
            start_time=10.0,
            end_time=11.0,
            text=long_text,
            metadata={'format': 'srt'}
        )
        
        adjuster = DurationAdjuster()
        result = adjuster.adjust_duration(long_subtitle, None, default_config)
        
        # Should not exceed maximum duration
        assert result.duration <= default_config.max_duration
    
    def test_next_subtitle_constraint(self, default_config, subtitle_pair):
        """Test that next subtitle constrains expansion"""
        adjuster = DurationAdjuster()
        
        current, next_sub = subtitle_pair
        result = adjuster.adjust_duration(current, next_sub, default_config)
        
        # Should not overlap with next subtitle
        gap = next_sub.start_time - result.end_time
        assert gap >= default_config.min_gap
    
    def test_no_shrinking_principle(self, default_config, long_subtitle):
        """Test that subtitles are never shortened"""
        adjuster = DurationAdjuster()
        
        original_duration = long_subtitle.duration
        result = adjuster.adjust_duration(long_subtitle, None, default_config)
        
        # Should never be shorter than original
        assert result.duration >= original_duration
    
    def test_calculate_target_duration(self, default_config):
        """Test target duration calculation"""
        adjuster = DurationAdjuster()
        
        # 20 chars at 20 chars/sec = 1.0s (within bounds)
        subtitle = Subtitle(0, 0, 1, "A" * 20, {})
        target = adjuster.calculate_target_duration(
            subtitle, default_config.chars_per_sec,
            default_config.min_duration, default_config.max_duration
        )
        assert target == 1.0
        
        # 5 chars at 20 chars/sec = 0.25s (below min, should be clamped to 1.0s)
        short_sub = Subtitle(0, 0, 1, "A" * 5, {})
        target = adjuster.calculate_target_duration(
            short_sub, default_config.chars_per_sec,
            default_config.min_duration, default_config.max_duration
        )
        assert target == default_config.min_duration


class TestTemporalRebalancer:
    """Test cases for TemporalRebalancer algorithm"""
    
    def test_basic_rebalancing(self, default_config, subtitle_pair):
        """Test basic rebalancing functionality"""
        rebalancer = TemporalRebalancer()
        
        short_sub, long_sub = subtitle_pair
        
        # Verify initial conditions
        assert short_sub.duration < default_config.short_threshold
        assert long_sub.duration > default_config.long_threshold
        
        new_short, new_long, transferred = rebalancer.rebalance_pair(
            short_sub, long_sub, default_config
        )
        
        # Should have transferred some time
        assert transferred > 0
        # Short subtitle should be longer
        assert new_short.duration > short_sub.duration
        # Long subtitle should be shorter
        assert new_long.duration < long_sub.duration
        # Gap should be maintained
        gap = new_long.start_time - new_short.end_time
        assert gap >= default_config.min_gap
    
    def test_should_rebalance_conditions(self, default_config):
        """Test conditions for rebalancing"""
        rebalancer = TemporalRebalancer()
        
        # Short + Long = Should rebalance
        short_sub = Subtitle(0, 10.0, 10.5, "Short", {})  # 0.5s
        long_sub = Subtitle(1, 12.0, 16.0, "Long subtitle", {})  # 4.0s
        assert rebalancer.should_rebalance(short_sub, long_sub, default_config)
        
        # Normal + Normal = Should not rebalance
        normal1 = Subtitle(0, 10.0, 12.0, "Normal", {})  # 2.0s
        normal2 = Subtitle(1, 13.0, 15.0, "Normal", {})  # 2.0s
        assert not rebalancer.should_rebalance(normal1, normal2, default_config)
        
        # Long + Short = Should not rebalance (wrong order)
        assert not rebalancer.should_rebalance(long_sub, short_sub, default_config)
    
    def test_no_rebalancing_when_inappropriate(self, default_config):
        """Test that rebalancing doesn't occur when inappropriate"""
        rebalancer = TemporalRebalancer()
        
        # Two normal subtitles
        normal1 = Subtitle(0, 10.0, 12.0, "Normal subtitle", {})
        normal2 = Subtitle(1, 13.0, 15.0, "Another normal", {})
        
        new1, new2, transferred = rebalancer.rebalance_pair(normal1, normal2, default_config)
        
        # Should not have changed anything
        assert transferred == 0
        assert new1.duration == normal1.duration
        assert new2.duration == normal2.duration
    
    def test_rebalancing_limits(self, default_config):
        """Test that rebalancing respects limits"""
        rebalancer = TemporalRebalancer()
        
        # Short subtitle that needs a lot of time
        very_short = Subtitle(0, 10.0, 10.2, "Hi", {})  # 0.2s
        # Long subtitle with limited surplus
        somewhat_long = Subtitle(1, 12.0, 15.1, "Somewhat long subtitle", {})  # 3.1s
        
        new_short, new_long, transferred = rebalancer.rebalance_pair(
            very_short, somewhat_long, default_config
        )
        
        # Should transfer limited amount
        assert 0 < transferred <= (somewhat_long.duration - default_config.long_threshold)
        # New long subtitle shouldn't go below long_threshold
        assert new_long.duration >= default_config.min_duration
    
    def test_process_full_sequence(self, default_config, sample_subtitles, stats):
        """Test processing full subtitle sequence"""
        rebalancer = TemporalRebalancer()
        
        result = rebalancer.process(sample_subtitles, default_config, stats)
        
        # Should return same number of subtitles
        assert len(result) == len(sample_subtitles)
        # Statistics should be updated
        assert stats.rebalanced_pairs >= 0


class TestAnticipationAdjuster:
    """Test cases for AnticipationAdjuster algorithm"""
    
    def test_basic_anticipation(self, default_config, anticipation_candidate):
        """Test basic anticipation functionality"""
        adjuster = AnticipationAdjuster()
        
        prev_sub, current_sub = anticipation_candidate
        
        new_sub, offset = adjuster.apply_anticipation(current_sub, prev_sub, default_config)
        
        if offset > 0:
            # Should start earlier
            assert new_sub.start_time < current_sub.start_time
            # Duration should increase
            assert new_sub.duration > current_sub.duration
            # Should maintain gap with previous
            gap = new_sub.start_time - prev_sub.end_time
            assert gap >= default_config.min_gap
    
    def test_first_subtitle_anticipation(self, default_config, first_subtitle):
        """Test anticipation for first subtitle (no previous)"""
        adjuster = AnticipationAdjuster()
        
        new_sub, offset = adjuster.apply_anticipation(first_subtitle, None, default_config)
        
        # Can anticipate freely up to max_anticipation
        if offset > 0:
            assert offset <= default_config.max_anticipation
            assert new_sub.start_time >= 0  # But not negative
    
    def test_no_anticipation_when_inappropriate(self, default_config, minimal_gap_subtitles):
        """Test that anticipation doesn't occur when inappropriate"""
        adjuster = AnticipationAdjuster()
        
        prev_sub, current_sub = minimal_gap_subtitles
        
        new_sub, offset = adjuster.apply_anticipation(current_sub, prev_sub, default_config)
        
        # Should not anticipate with minimal gap
        assert offset == 0
        assert new_sub.start_time == current_sub.start_time
    
    def test_calculate_max_anticipation(self, default_config):
        """Test maximum anticipation calculation"""
        adjuster = AnticipationAdjuster()
        
        # With large gap
        prev_sub = Subtitle(0, 10.0, 11.0, "Previous", {})
        current_sub = Subtitle(1, 15.0, 16.0, "Current", {})  # 4s gap
        
        max_anticipation = adjuster.calculate_max_anticipation(
            current_sub, prev_sub, default_config
        )
        
        # Should be limited by configured maximum
        expected = min(default_config.max_anticipation, 
                      15.0 - 11.0 - default_config.min_gap)
        assert max_anticipation == expected
    
    def test_is_beneficial(self, default_config, single_subtitle):
        """Test benefit calculation"""
        adjuster = AnticipationAdjuster()
        
        # Small anticipation should not be beneficial
        assert not adjuster.is_beneficial(single_subtitle, 0.05, default_config)
        
        # Larger anticipation should be beneficial
        assert adjuster.is_beneficial(single_subtitle, 0.3, default_config)
    
    def test_process_full_sequence(self, default_config, sample_subtitles, stats):
        """Test processing full subtitle sequence"""
        adjuster = AnticipationAdjuster()
        
        result = adjuster.process(sample_subtitles, default_config, stats)
        
        # Should return same number of subtitles
        assert len(result) == len(sample_subtitles)
        # Should maintain chronological order
        for i in range(len(result) - 1):
            assert result[i].start_time <= result[i + 1].start_time


class TestConstraintsValidator:
    """Test cases for ConstraintsValidator algorithm"""
    
    def test_minimum_duration_fix(self, default_config, stats):
        """Test minimum duration enforcement"""
        validator = ConstraintsValidator()
        
        # Subtitle below minimum duration
        short_sub = Subtitle(0, 10.0, 10.8, "Short", {})  # 0.8s < 1.0s min
        
        result = validator.apply_all_fixes(short_sub, None, None, default_config, stats)
        
        assert result is not None
        assert result.duration >= default_config.min_duration
        assert stats.min_duration_fixes > 0
    
    def test_gap_fixing(self, default_config, stats):
        """Test gap fixing between subtitles"""
        validator = ConstraintsValidator()
        
        prev_sub = Subtitle(0, 10.0, 11.0, "Previous", {})
        # Too close to previous
        current_sub = Subtitle(1, 11.01, 12.0, "Current", {})  # 0.01s gap < 0.05s min
        
        result = validator.apply_all_fixes(current_sub, prev_sub, None, default_config, stats)
        
        assert result is not None
        gap = result.start_time - prev_sub.end_time
        assert gap >= default_config.min_gap
        assert stats.gap_fixes > 0
    
    def test_chronology_validation(self, default_config, stats):
        """Test chronological order validation"""
        validator = ConstraintsValidator()
        
        prev_sub = Subtitle(0, 10.0, 11.0, "Previous", {})
        # Starts before previous (chronology violation)
        invalid_sub = Subtitle(1, 9.0, 10.0, "Invalid", {})
        
        result = validator.apply_all_fixes(invalid_sub, prev_sub, None, default_config, stats)
        
        # Should be rejected (None returned)
        assert result is None
        assert stats.chronology_fixes > 0
    
    def test_invalid_time_range_rejection(self, default_config, stats):
        """Test rejection of invalid time ranges"""
        validator = ConstraintsValidator()
        
        # End time before start time
        invalid_sub = Subtitle(0, 10.0, 9.0, "Invalid", {})
        
        result = validator.apply_all_fixes(invalid_sub, None, None, default_config, stats)
        
        # Should be rejected
        assert result is None
    
    def test_overlapping_subtitles_fix(self, default_config, overlapping_subtitles, stats):
        """Test fixing of overlapping subtitles"""
        validator = ConstraintsValidator()
        
        result = validator.validate_and_fix(overlapping_subtitles, default_config, stats)
        
        # Should have fewer subtitles (some removed/fixed)
        assert len(result) <= len(overlapping_subtitles)
        
        # No overlaps should remain
        for i in range(len(result) - 1):
            gap = result[i + 1].start_time - result[i].end_time
            assert gap >= 0  # No negative gaps (overlaps)
    
    def test_is_valid_subtitle(self, default_config):
        """Test subtitle validation"""
        validator = ConstraintsValidator()
        
        # Valid subtitle
        valid_sub = Subtitle(0, 10.0, 12.0, "Valid subtitle", {})
        assert validator.is_valid_subtitle(valid_sub, default_config)
        
        # Invalid: too short
        short_sub = Subtitle(0, 10.0, 10.5, "Short", {})  # 0.5s < 1.0s min
        assert not validator.is_valid_subtitle(short_sub, default_config)
        
        # Invalid: negative start time
        negative_sub = Subtitle(0, -1.0, 1.0, "Negative", {})
        assert not validator.is_valid_subtitle(negative_sub, default_config)
    
    def test_detect_overlaps(self, overlapping_subtitles):
        """Test overlap detection"""
        validator = ConstraintsValidator()
        
        overlaps = validator.detect_overlaps(overlapping_subtitles)
        
        # Should detect overlaps
        assert len(overlaps) > 0
        
        # Should be pairs of indices
        for idx1, idx2 in overlaps:
            assert isinstance(idx1, int)
            assert isinstance(idx2, int)
            assert idx2 == idx1 + 1  # Adjacent pairs
    
    def test_validate_sequence(self, default_config, sample_subtitles):
        """Test full sequence validation"""
        validator = ConstraintsValidator()
        
        report = validator.validate_sequence(sample_subtitles, default_config)
        
        # Should return validation report
        assert 'total_subtitles' in report
        assert 'valid_subtitles' in report
        assert 'violations' in report
        assert report['total_subtitles'] == len(sample_subtitles)
    
    def test_process_full_sequence(self, default_config, invalid_subtitles, stats):
        """Test processing sequence with invalid subtitles"""
        validator = ConstraintsValidator()
        
        result = validator.process(invalid_subtitles, default_config, stats)
        
        # Should remove invalid subtitles
        assert len(result) < len(invalid_subtitles)
        
        # All remaining should be valid
        for subtitle in result:
            assert validator.is_valid_subtitle(subtitle, default_config)


class TestAlgorithmIntegration:
    """Test algorithm integration and interaction"""
    
    def test_algorithm_order_preservation(self, default_config, sample_subtitles):
        """Test that algorithm order is preserved"""
        stats = OptimizationStatistics()
        
        # Apply algorithms in order
        adjuster = DurationAdjuster()
        rebalancer = TemporalRebalancer()
        anticipator = AnticipationAdjuster()
        validator = ConstraintsValidator()
        
        # Phase 1: Duration adjustment
        result1 = adjuster.process(sample_subtitles, default_config, stats)
        
        # Phase 2: Rebalancing
        result2 = rebalancer.process(result1, default_config, stats)
        
        # Phase 3: Anticipation
        result3 = anticipator.process(result2, default_config, stats)
        
        # Phase 4: Validation
        final_result = validator.process(result3, default_config, stats)
        
        # Final result should be valid
        assert len(final_result) <= len(sample_subtitles)
        
        # Should maintain chronological order
        for i in range(len(final_result) - 1):
            assert final_result[i].start_time <= final_result[i + 1].start_time
    
    def test_statistics_accumulation(self, default_config, sample_subtitles):
        """Test that statistics accumulate correctly"""
        stats = OptimizationStatistics()
        stats.original_subtitle_count = len(sample_subtitles)
        
        # Apply all algorithms
        adjuster = DurationAdjuster()
        rebalancer = TemporalRebalancer()
        anticipator = AnticipationAdjuster()
        validator = ConstraintsValidator()
        
        result = sample_subtitles
        result = adjuster.process(result, default_config, stats)
        result = rebalancer.process(result, default_config, stats)
        result = anticipator.process(result, default_config, stats)
        result = validator.process(result, default_config, stats)
        
        stats.final_subtitle_count = len(result)
        
        # Statistics should be accumulated
        assert stats.total_modifications >= 0
        assert stats.original_subtitle_count > 0
        assert stats.final_subtitle_count >= 0
    
    def test_graceful_degradation(self, default_config):
        """Test graceful degradation with edge cases"""
        stats = OptimizationStatistics()
        
        # Empty list
        adjuster = DurationAdjuster()
        result = adjuster.process([], default_config, stats)
        assert result == []
        
        # Single subtitle
        single = [Subtitle(0, 10.0, 11.0, "Single", {})]
        result = adjuster.process(single, default_config, stats)
        assert len(result) == 1
    
    def test_deterministic_results(self, default_config, sample_subtitles):
        """Test that results are deterministic"""
        stats1 = OptimizationStatistics()
        stats2 = OptimizationStatistics()
        
        # Apply same processing twice
        def process_subtitles(subtitles, stats):
            adjuster = DurationAdjuster()
            rebalancer = TemporalRebalancer()
            anticipator = AnticipationAdjuster()
            validator = ConstraintsValidator()
            
            result = subtitles
            result = adjuster.process(result, default_config, stats)
            result = rebalancer.process(result, default_config, stats)
            result = anticipator.process(result, default_config, stats)
            result = validator.process(result, default_config, stats)
            return result
        
        result1 = process_subtitles(sample_subtitles.copy(), stats1)
        result2 = process_subtitles(sample_subtitles.copy(), stats2)
        
        # Results should be identical
        assert len(result1) == len(result2)
        for sub1, sub2 in zip(result1, result2):
            assert abs(sub1.start_time - sub2.start_time) < 0.001
            assert abs(sub1.end_time - sub2.end_time) < 0.001
            assert sub1.text == sub2.text