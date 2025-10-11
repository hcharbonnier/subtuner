"""Conditional anticipatory offset algorithm"""

import logging
from typing import List, Optional, Tuple

from ...config import OptimizationConfig
from ...parsers.base import Subtitle
from ..statistics import OptimizationStatistics

logger = logging.getLogger(__name__)


class AnticipationAdjuster:
    """Algorithm 3: Conditional Anticipatory Offset"""
    
    def __init__(self):
        self.name = "Anticipation Adjuster"
    
    def process(
        self, 
        subtitles: List[Subtitle], 
        config: OptimizationConfig,
        stats: OptimizationStatistics
    ) -> List[Subtitle]:
        """Apply anticipatory adjustments to subtitles
        
        Args:
            subtitles: List of subtitles to process
            config: Optimization configuration
            stats: Statistics tracker
            
        Returns:
            List of subtitles with anticipatory adjustments
        """
        if not subtitles:
            return subtitles
        
        logger.debug(f"Starting anticipatory adjustment for {len(subtitles)} subtitles")
        
        anticipated = []
        
        for i, subtitle in enumerate(subtitles):
            previous = anticipated[-1] if anticipated else None
            
            adjusted_subtitle, offset = self.apply_anticipation(
                subtitle, previous, config
            )
            
            if offset > 0:
                stats.add_anticipation(offset)
                logger.debug(
                    f"Subtitle {i}: anticipated by {offset:.3f}s "
                    f"(start: {subtitle.start_time:.3f}s → {adjusted_subtitle.start_time:.3f}s, "
                    f"duration: {subtitle.duration:.3f}s → {adjusted_subtitle.duration:.3f}s)"
                )
            
            anticipated.append(adjusted_subtitle)
        
        logger.info(
            f"Anticipatory adjustment complete: {stats.anticipated_subtitles} subtitles adjusted, "
            f"avg anticipation: {stats.avg_anticipation:.3f}s"
        )
        
        return anticipated
    
    def apply_anticipation(
        self, 
        current: Subtitle, 
        previous: Optional[Subtitle],
        config: OptimizationConfig
    ) -> Tuple[Subtitle, float]:
        """Start subtitle earlier to increase display duration
        
        Args:
            current: Current subtitle
            previous: Previous subtitle (if exists)
            config: Optimization configuration
            
        Returns:
            Tuple of (adjusted_subtitle, anticipation_amount)
        """
        # Calculate maximum possible anticipation
        max_offset = self.calculate_max_anticipation(current, previous, config)
        
        if max_offset <= 0:
            return current, 0.0
        
        # Limit to configured maximum
        actual_offset = min(max_offset, config.max_anticipation)
        
        # Check if anticipation provides meaningful benefit
        if not self.is_beneficial(current, actual_offset, config):
            return current, 0.0
        
        # Apply the anticipation
        new_start = current.start_time - actual_offset
        new_subtitle = current.with_start_time(new_start)
        
        # Validate the adjustment
        if not self.validate_anticipation(current, new_subtitle, previous, config):
            return current, 0.0
        
        return new_subtitle, actual_offset
    
    def calculate_max_anticipation(
        self, 
        current: Subtitle, 
        previous: Optional[Subtitle],
        config: OptimizationConfig
    ) -> float:
        """Calculate maximum possible anticipation without violating constraints
        
        Args:
            current: Current subtitle
            previous: Previous subtitle (if exists)
            config: Optimization configuration
            
        Returns:
            Maximum anticipation in seconds
        """
        if previous is None:
            # First subtitle: can anticipate freely up to max
            return config.max_anticipation
        
        # Calculate gap to previous subtitle
        gap_to_previous = current.start_time - previous.end_time
        
        # Available anticipation is gap minus required minimum gap
        available_anticipation = gap_to_previous - config.min_gap
        
        return max(0, available_anticipation)
    
    def is_beneficial(
        self, 
        subtitle: Subtitle, 
        anticipation: float,
        config: OptimizationConfig,
        min_benefit: float = 0.1
    ) -> bool:
        """Check if anticipation provides meaningful benefit
        
        Args:
            subtitle: Subtitle to anticipate
            anticipation: Amount of anticipation
            config: Optimization configuration
            min_benefit: Minimum benefit threshold
            
        Returns:
            True if anticipation is beneficial
        """
        if anticipation <= 0:
            return False
        
        # Benefit is the increase in duration
        duration_increase = anticipation
        
        # Only apply if benefit is meaningful
        if duration_increase < min_benefit:
            return False
        
        # Additional check: don't anticipate if subtitle is already long enough
        ideal_duration = subtitle.char_count / config.chars_per_sec
        if subtitle.duration >= ideal_duration:
            # Only anticipate if it brings us much closer to min_duration
            if subtitle.duration >= config.min_duration:
                return False
        
        return True
    
    def validate_anticipation(
        self, 
        original: Subtitle,
        anticipated: Subtitle,
        previous: Optional[Subtitle],
        config: OptimizationConfig
    ) -> bool:
        """Validate that anticipation is safe and beneficial
        
        Args:
            original: Original subtitle
            anticipated: Anticipated subtitle
            previous: Previous subtitle (if exists)
            config: Optimization configuration
            
        Returns:
            True if anticipation is valid
        """
        # Check that times are valid
        if anticipated.start_time >= anticipated.end_time:
            return False
        
        # Check that anticipation actually increases duration
        if anticipated.duration <= original.duration:
            return False
        
        # Check minimum gap with previous subtitle
        if previous is not None:
            gap = anticipated.start_time - previous.end_time
            if gap < config.min_gap:
                return False
        
        # Check that start time doesn't go negative
        if anticipated.start_time < 0:
            return False
        
        return True
    
    def calculate_optimal_anticipation(
        self, 
        current: Subtitle,
        previous: Optional[Subtitle],
        config: OptimizationConfig
    ) -> float:
        """Calculate optimal anticipation amount
        
        Args:
            current: Current subtitle
            previous: Previous subtitle
            config: Optimization configuration
            
        Returns:
            Optimal anticipation amount
        """
        # Get maximum possible anticipation
        max_anticipation = self.calculate_max_anticipation(current, previous, config)
        
        if max_anticipation <= 0:
            return 0.0
        
        # Calculate ideal duration based on reading speed
        ideal_duration = current.char_count / config.chars_per_sec
        ideal_duration = max(config.min_duration, min(config.max_duration, ideal_duration))
        
        # How much additional duration do we need?
        needed_duration = max(0, ideal_duration - current.duration)
        
        # Use the minimum of what we need and what's available
        optimal = min(needed_duration, max_anticipation, config.max_anticipation)
        
        return max(0, optimal)
    
    def estimate_benefit(
        self, 
        subtitle: Subtitle, 
        anticipation: float,
        config: OptimizationConfig
    ) -> float:
        """Estimate the benefit of applying anticipation
        
        Args:
            subtitle: Subtitle to anticipate
            anticipation: Amount of anticipation
            config: Optimization configuration
            
        Returns:
            Benefit score (higher is better)
        """
        if anticipation <= 0:
            return 0.0
        
        # Calculate current duration deficit
        ideal_duration = subtitle.char_count / config.chars_per_sec
        ideal_duration = max(config.min_duration, min(config.max_duration, ideal_duration))
        
        deficit_before = max(0, ideal_duration - subtitle.duration)
        deficit_after = max(0, ideal_duration - (subtitle.duration + anticipation))
        
        # Benefit is the reduction in deficit
        benefit = deficit_before - deficit_after
        
        return benefit
    
    def get_anticipation_candidates(
        self, 
        subtitles: List[Subtitle],
        config: OptimizationConfig
    ) -> List[Tuple[int, float]]:
        """Get list of subtitle indices and their potential anticipation amounts
        
        Args:
            subtitles: List of all subtitles
            config: Optimization configuration
            
        Returns:
            List of (index, anticipation_amount) tuples, sorted by benefit
        """
        candidates = []
        
        for i, subtitle in enumerate(subtitles):
            previous = subtitles[i - 1] if i > 0 else None
            
            max_anticipation = self.calculate_max_anticipation(subtitle, previous, config)
            optimal_anticipation = self.calculate_optimal_anticipation(subtitle, previous, config)
            
            if optimal_anticipation > 0.1:  # Only consider significant anticipations
                benefit = self.estimate_benefit(subtitle, optimal_anticipation, config)
                candidates.append((i, optimal_anticipation, benefit))
        
        # Sort by benefit (descending)
        candidates.sort(key=lambda x: x[2], reverse=True)
        
        return [(idx, anticipation) for idx, anticipation, _ in candidates]
    
    def analyze_anticipation_potential(
        self, 
        subtitles: List[Subtitle],
        config: OptimizationConfig
    ) -> dict:
        """Analyze anticipation potential for all subtitles
        
        Args:
            subtitles: List of subtitles
            config: Optimization configuration
            
        Returns:
            Analysis results
        """
        total_subtitles = len(subtitles)
        anticipatable = 0
        total_potential = 0.0
        
        for i, subtitle in enumerate(subtitles):
            previous = subtitles[i - 1] if i > 0 else None
            potential = self.calculate_max_anticipation(subtitle, previous, config)
            
            if potential > 0.1:
                anticipatable += 1
                total_potential += potential
        
        return {
            'total_subtitles': total_subtitles,
            'anticipatable_count': anticipatable,
            'anticipatable_percentage': (anticipatable / total_subtitles * 100) if total_subtitles > 0 else 0,
            'total_potential': total_potential,
            'avg_potential': total_potential / anticipatable if anticipatable > 0 else 0,
        }