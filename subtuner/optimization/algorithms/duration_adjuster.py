"""Duration adjustment algorithm"""

import logging
from typing import List, Optional

from ...config import OptimizationConfig
from ...parsers.base import Subtitle
from ..statistics import OptimizationStatistics

logger = logging.getLogger(__name__)


class DurationAdjuster:
    """Algorithm 1: Duration Adjustment based on reading speed"""
    
    def __init__(self):
        self.name = "Duration Adjuster"
    
    def process(
        self,
        subtitles: List[Subtitle],
        config: OptimizationConfig,
        stats: OptimizationStatistics,
        allowed_overlaps: set = None
    ) -> List[Subtitle]:
        """Apply duration adjustment to all subtitles
        
        Args:
            subtitles: List of subtitles to process
            config: Optimization configuration
            stats: Statistics tracker
            allowed_overlaps: Set of (index1, index2) tuples for allowed overlaps
            
        Returns:
            List of subtitles with adjusted durations
        """
        if not subtitles:
            return subtitles
        
        if allowed_overlaps is None:
            allowed_overlaps = set()
        
        logger.debug(f"Starting duration adjustment for {len(subtitles)} subtitles")
        logger.debug(f"Preserving {len(allowed_overlaps)} original overlaps")
        
        adjusted = []
        
        for i, subtitle in enumerate(subtitles):
            next_subtitle = subtitles[i + 1] if i + 1 < len(subtitles) else None
            is_overlap_allowed = (i, i + 1) in allowed_overlaps if next_subtitle else False
            adjusted_subtitle = self.adjust_duration(subtitle, next_subtitle, config, is_overlap_allowed)
            
            # Track changes
            duration_change = adjusted_subtitle.duration - subtitle.duration
            if abs(duration_change) > 0.01:  # Only count significant changes
                stats.add_duration_change(duration_change)
                logger.debug(
                    f"Subtitle {i}: duration {subtitle.duration:.3f}s → "
                    f"{adjusted_subtitle.duration:.3f}s ({duration_change:+.3f}s)"
                )
            
            adjusted.append(adjusted_subtitle)
        
        logger.info(
            f"Duration adjustment complete: {stats.duration_adjustments} adjustments, "
            f"avg change: {stats.avg_duration_change:+.3f}s"
        )
        
        return adjusted
    
    def adjust_duration(
        self,
        current: Subtitle,
        next_subtitle: Optional[Subtitle],
        config: OptimizationConfig,
        is_overlap_allowed: bool = False
    ) -> Subtitle:
        """Adjust subtitle duration based on character count and reading speed
        
        Args:
            current: Current subtitle to adjust
            next_subtitle: Next subtitle (if exists)
            config: Optimization configuration
            is_overlap_allowed: Whether overlap with next subtitle is allowed
            
        Returns:
            Subtitle with adjusted duration
        """
        # Calculate ideal duration based on reading speed
        char_count = current.char_count
        ideal_duration = char_count / config.chars_per_sec
        
        # Apply duration constraints
        target_duration = max(
            config.min_duration,
            min(config.max_duration, ideal_duration)
        )
        
        # Calculate available time window
        if next_subtitle is not None:
            if is_overlap_allowed:
                # Preserve existing overlap: can extend up to original next.end_time
                # This allows the overlap to remain as it was
                max_possible_duration = next_subtitle.end_time - current.start_time
                logger.debug(f"Allowing overlap with next subtitle (preserving original overlap)")
            else:
                # Normal case: respect min_gap
                available_end_time = next_subtitle.start_time - config.min_gap
                max_possible_duration = available_end_time - current.start_time
        else:
            # Last subtitle: no constraint from next
            max_possible_duration = float('inf')
        
        # Use minimum of target and available duration
        new_duration = min(target_duration, max_possible_duration)
        
        # Only extend, never shorten (semantic preservation)
        final_duration = max(new_duration, current.duration)
        
        # Ensure we don't create invalid durations
        if final_duration <= 0:
            final_duration = current.duration
        
        # Return subtitle with new end time
        new_end_time = current.start_time + final_duration
        
        return current.with_end_time(new_end_time)
    
    def calculate_target_duration(
        self, 
        subtitle: Subtitle, 
        chars_per_sec: float, 
        min_dur: float, 
        max_dur: float
    ) -> float:
        """Calculate target duration for a subtitle
        
        Args:
            subtitle: Subtitle to calculate duration for
            chars_per_sec: Reading speed in characters per second
            min_dur: Minimum duration
            max_dur: Maximum duration
            
        Returns:
            Target duration in seconds
        """
        char_count = subtitle.char_count
        ideal_duration = char_count / chars_per_sec
        
        return max(min_dur, min(max_dur, ideal_duration))
    
    def get_available_duration(
        self, 
        current: Subtitle, 
        next_subtitle: Optional[Subtitle], 
        min_gap: float
    ) -> float:
        """Calculate available duration for subtitle expansion
        
        Args:
            current: Current subtitle
            next_subtitle: Next subtitle (if exists)
            min_gap: Minimum gap required between subtitles
            
        Returns:
            Available duration in seconds
        """
        if next_subtitle is None:
            return float('inf')  # No constraint from next subtitle
        
        # Calculate maximum possible end time
        max_end_time = next_subtitle.start_time - min_gap
        
        # Calculate available duration
        available_duration = max_end_time - current.start_time
        
        # Ensure it's not negative
        return max(0, available_duration)
    
    def should_adjust(
        self, 
        current: Subtitle, 
        target_duration: float, 
        tolerance: float = 0.1
    ) -> bool:
        """Check if subtitle duration should be adjusted
        
        Args:
            current: Current subtitle
            target_duration: Target duration
            tolerance: Tolerance for considering adjustment worthwhile
            
        Returns:
            True if adjustment is beneficial
        """
        duration_difference = target_duration - current.duration
        
        # Only adjust if the improvement is significant
        return duration_difference > tolerance
    
    def validate_adjustment(
        self, 
        original: Subtitle, 
        adjusted: Subtitle, 
        next_subtitle: Optional[Subtitle], 
        min_gap: float
    ) -> bool:
        """Validate that the adjustment is safe and beneficial
        
        Args:
            original: Original subtitle
            adjusted: Adjusted subtitle
            next_subtitle: Next subtitle (if exists)
            min_gap: Minimum gap required
            
        Returns:
            True if adjustment is valid
        """
        # Check that duration didn't decrease
        if adjusted.duration < original.duration:
            return False
        
        # Check that we don't overlap with next subtitle
        if next_subtitle is not None:
            gap = next_subtitle.start_time - adjusted.end_time
            if gap < min_gap:
                return False
        
        # Check that times are valid
        if adjusted.start_time >= adjusted.end_time:
            return False
        
        return True