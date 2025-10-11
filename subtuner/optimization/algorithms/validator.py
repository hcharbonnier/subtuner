"""Temporal constraints validation algorithm"""

import logging
from typing import List, Optional

from ...config import OptimizationConfig
from ...parsers.base import Subtitle
from ..statistics import OptimizationStatistics

logger = logging.getLogger(__name__)


class ConstraintsValidator:
    """Algorithm 4: Temporal Constraints Validation"""
    
    def __init__(self):
        self.name = "Constraints Validator"
    
    def process(
        self, 
        subtitles: List[Subtitle], 
        config: OptimizationConfig,
        stats: OptimizationStatistics
    ) -> List[Subtitle]:
        """Enforce hard constraints across all subtitles
        
        Args:
            subtitles: List of subtitles to validate and fix
            config: Optimization configuration
            stats: Statistics tracker
            
        Returns:
            List of validated subtitles with constraints enforced
        """
        if not subtitles:
            return subtitles
        
        logger.debug(f"Starting constraints validation for {len(subtitles)} subtitles")
        
        validated = self.validate_and_fix(subtitles, config, stats)
        
        logger.info(
            f"Constraints validation complete: "
            f"{stats.min_duration_fixes} min duration fixes, "
            f"{stats.gap_fixes} gap fixes, "
            f"{stats.chronology_fixes} chronology fixes, "
            f"{stats.invalid_removed} invalid removed"
        )
        
        return validated
    
    def validate_and_fix(
        self, 
        subtitles: List[Subtitle],
        config: OptimizationConfig,
        stats: OptimizationStatistics
    ) -> List[Subtitle]:
        """Enforce hard constraints on subtitles
        
        Args:
            subtitles: List of subtitles to validate
            config: Optimization configuration
            stats: Statistics tracker
            
        Returns:
            List of validated subtitles
        """
        validated = []
        
        for i, current in enumerate(subtitles):
            previous = validated[-1] if validated else None
            next_subtitle = subtitles[i + 1] if i + 1 < len(subtitles) else None
            
            # Apply all constraint fixes
            fixed_subtitle = self.apply_all_fixes(
                current, previous, next_subtitle, config, stats
            )
            
            # Only add if subtitle is still valid
            if fixed_subtitle and self.is_valid_subtitle(fixed_subtitle, config):
                validated.append(fixed_subtitle)
            else:
                stats.invalid_removed += 1
                logger.debug(f"Removed invalid subtitle at index {i}")
        
        return validated
    
    def apply_all_fixes(
        self, 
        current: Subtitle,
        previous: Optional[Subtitle],
        next_subtitle: Optional[Subtitle],
        config: OptimizationConfig,
        stats: OptimizationStatistics
    ) -> Optional[Subtitle]:
        """Apply all necessary fixes to a subtitle
        
        Args:
            current: Current subtitle to fix
            previous: Previous valid subtitle
            next_subtitle: Next subtitle (for reference)
            config: Optimization configuration
            stats: Statistics tracker
            
        Returns:
            Fixed subtitle or None if unfixable
        """
        fixed = current
        
        # Fix 1: Enforce minimum duration
        fixed = self.fix_minimum_duration(fixed, config, stats)
        if not fixed:
            return None
        
        # Fix 2: Enforce minimum gap with previous
        fixed = self.fix_minimum_gap(fixed, previous, config, stats)
        if not fixed:
            return None
        
        # Fix 3: Ensure chronological order
        if not self.is_chronologically_valid(fixed, previous):
            stats.chronology_fixes += 1
            logger.debug(f"Chronological order violation detected, skipping subtitle")
            return None
        
        # Fix 4: Ensure valid time range
        if not self.has_valid_time_range(fixed):
            logger.debug(f"Invalid time range detected, skipping subtitle")
            return None
        
        return fixed
    
    def fix_minimum_duration(
        self, 
        subtitle: Subtitle,
        config: OptimizationConfig,
        stats: OptimizationStatistics
    ) -> Optional[Subtitle]:
        """Fix subtitle that's shorter than minimum duration
        
        Args:
            subtitle: Subtitle to fix
            config: Optimization configuration
            stats: Statistics tracker
            
        Returns:
            Fixed subtitle or None if unfixable
        """
        if subtitle.duration >= config.min_duration:
            return subtitle  # No fix needed
        
        # Try to extend end_time to meet minimum duration
        target_end = subtitle.start_time + config.min_duration
        fixed = subtitle.with_end_time(target_end)
        
        stats.min_duration_fixes += 1
        logger.debug(
            f"Fixed minimum duration: {subtitle.duration:.3f}s → {fixed.duration:.3f}s"
        )
        
        return fixed
    
    def fix_minimum_gap(
        self, 
        current: Subtitle,
        previous: Optional[Subtitle],
        config: OptimizationConfig,
        stats: OptimizationStatistics
    ) -> Optional[Subtitle]:
        """Fix gap between current and previous subtitle
        
        Args:
            current: Current subtitle
            previous: Previous subtitle
            config: Optimization configuration
            stats: Statistics tracker
            
        Returns:
            Fixed subtitle or None if unfixable
        """
        if previous is None:
            return current  # No previous subtitle to check against
        
        current_gap = current.start_time - previous.end_time
        
        if current_gap >= config.min_gap:
            return current  # Gap is sufficient
        
        # Shift current subtitle forward to maintain minimum gap
        required_start = previous.end_time + config.min_gap
        duration = current.duration
        
        fixed = current.with_times(required_start, required_start + duration)
        
        stats.gap_fixes += 1
        logger.debug(
            f"Fixed gap: shifted start {current.start_time:.3f}s → {required_start:.3f}s "
            f"(gap: {current_gap:.3f}s → {config.min_gap:.3f}s)"
        )
        
        return fixed
    
    def is_chronologically_valid(
        self, 
        current: Subtitle,
        previous: Optional[Subtitle]
    ) -> bool:
        """Check if subtitle is in chronological order
        
        Args:
            current: Current subtitle
            previous: Previous subtitle
            
        Returns:
            True if chronologically valid
        """
        if previous is None:
            return True
        
        # Current must start after or at the same time as previous
        return current.start_time >= previous.start_time
    
    def has_valid_time_range(self, subtitle: Subtitle) -> bool:
        """Check if subtitle has valid time range
        
        Args:
            subtitle: Subtitle to check
            
        Returns:
            True if time range is valid
        """
        return (
            subtitle.start_time >= 0 and
            subtitle.end_time > subtitle.start_time and
            subtitle.duration > 0
        )
    
    def is_valid_subtitle(
        self, 
        subtitle: Subtitle,
        config: OptimizationConfig
    ) -> bool:
        """Check if subtitle meets all basic validity requirements
        
        Args:
            subtitle: Subtitle to validate
            config: Optimization configuration
            
        Returns:
            True if subtitle is valid
        """
        # Check basic validity
        if not subtitle.validate():
            return False
        
        # Check minimum duration
        if subtitle.duration < config.min_duration:
            return False
        
        # Check reasonable bounds
        if subtitle.start_time < 0:
            return False
        
        if subtitle.duration > config.max_duration * 2:  # Allow some flexibility
            return False
        
        return True
    
    def detect_overlaps(self, subtitles: List[Subtitle]) -> List[tuple[int, int]]:
        """Detect overlapping subtitle pairs
        
        Args:
            subtitles: List of subtitles to check
            
        Returns:
            List of (index1, index2) tuples for overlapping pairs
        """
        overlaps = []
        
        for i in range(len(subtitles) - 1):
            current = subtitles[i]
            next_subtitle = subtitles[i + 1]
            
            if current.end_time > next_subtitle.start_time:
                overlaps.append((i, i + 1))
        
        return overlaps
    
    def fix_overlaps(
        self, 
        subtitles: List[Subtitle],
        config: OptimizationConfig,
        stats: OptimizationStatistics
    ) -> List[Subtitle]:
        """Fix overlapping subtitles
        
        Args:
            subtitles: List of subtitles with potential overlaps
            config: Optimization configuration
            stats: Statistics tracker
            
        Returns:
            List of subtitles with overlaps fixed
        """
        fixed = subtitles.copy()
        overlaps = self.detect_overlaps(fixed)
        
        for i, j in overlaps:
            if i < len(fixed) and j < len(fixed):
                current = fixed[i]
                next_subtitle = fixed[j]
                
                # Fix by adjusting current subtitle's end time
                new_end = next_subtitle.start_time - config.min_gap
                
                if new_end > current.start_time + config.min_duration:
                    fixed[i] = current.with_end_time(new_end)
                    stats.gap_fixes += 1
                    logger.debug(f"Fixed overlap between subtitles {i} and {j}")
                else:
                    # Can't fix without violating minimum duration, remove current
                    fixed.pop(i)
                    stats.invalid_removed += 1
                    logger.debug(f"Removed overlapping subtitle {i}")
        
        return fixed
    
    def validate_sequence(
        self, 
        subtitles: List[Subtitle],
        config: OptimizationConfig
    ) -> dict:
        """Validate entire subtitle sequence
        
        Args:
            subtitles: List of subtitles to validate
            config: Optimization configuration
            
        Returns:
            Validation report
        """
        report = {
            'total_subtitles': len(subtitles),
            'valid_subtitles': 0,
            'violations': {
                'min_duration': 0,
                'min_gap': 0,
                'overlaps': 0,
                'chronology': 0,
                'invalid_times': 0,
            }
        }
        
        for i, subtitle in enumerate(subtitles):
            is_valid = True
            
            # Check individual subtitle validity
            if not subtitle.validate():
                report['violations']['invalid_times'] += 1
                is_valid = False
            
            # Check minimum duration
            if subtitle.duration < config.min_duration:
                report['violations']['min_duration'] += 1
                is_valid = False
            
            # Check gaps and chronology
            if i > 0:
                prev_subtitle = subtitles[i - 1]
                
                # Check chronological order
                if subtitle.start_time < prev_subtitle.start_time:
                    report['violations']['chronology'] += 1
                    is_valid = False
                
                # Check gap
                gap = subtitle.start_time - prev_subtitle.end_time
                if gap < config.min_gap:
                    if gap < 0:
                        report['violations']['overlaps'] += 1
                    else:
                        report['violations']['min_gap'] += 1
                    is_valid = False
            
            if is_valid:
                report['valid_subtitles'] += 1
        
        return report