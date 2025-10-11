"""Temporal rebalancing algorithm"""

import logging
from typing import List, Tuple

from ...config import OptimizationConfig
from ...parsers.base import Subtitle
from ..statistics import OptimizationStatistics

logger = logging.getLogger(__name__)


class TemporalRebalancer:
    """Algorithm 2: Temporal Rebalancing between consecutive subtitles"""
    
    def __init__(self):
        self.name = "Temporal Rebalancer"
    
    def process(
        self, 
        subtitles: List[Subtitle], 
        config: OptimizationConfig,
        stats: OptimizationStatistics
    ) -> List[Subtitle]:
        """Apply temporal rebalancing to subtitle pairs
        
        Args:
            subtitles: List of subtitles to process
            config: Optimization configuration
            stats: Statistics tracker
            
        Returns:
            List of subtitles with rebalanced timing
        """
        if len(subtitles) < 2:
            return subtitles
        
        logger.debug(f"Starting temporal rebalancing for {len(subtitles)} subtitles")
        
        rebalanced = subtitles.copy()
        
        i = 0
        while i < len(rebalanced) - 1:
            current = rebalanced[i]
            next_subtitle = rebalanced[i + 1]
            
            new_current, new_next, transferred = self.rebalance_pair(
                current, next_subtitle, config
            )
            
            if transferred > 0:
                stats.add_rebalancing_transfer(transferred)
                logger.debug(
                    f"Rebalanced pair {i}-{i+1}: transferred {transferred:.3f}s "
                    f"(current: {current.duration:.3f}s → {new_current.duration:.3f}s, "
                    f"next: {next_subtitle.duration:.3f}s → {new_next.duration:.3f}s)"
                )
                
                rebalanced[i] = new_current
                rebalanced[i + 1] = new_next
            
            i += 1
        
        logger.info(
            f"Temporal rebalancing complete: {stats.rebalanced_pairs} pairs rebalanced, "
            f"total time transferred: {stats.total_time_transferred:.3f}s"
        )
        
        return rebalanced
    
    def rebalance_pair(
        self, 
        current: Subtitle, 
        next_subtitle: Subtitle,
        config: OptimizationConfig
    ) -> Tuple[Subtitle, Subtitle, float]:
        """Rebalance time between a short subtitle and following long subtitle
        
        Args:
            current: Current (potentially short) subtitle
            next_subtitle: Next (potentially long) subtitle
            config: Optimization configuration
            
        Returns:
            Tuple of (new_current, new_next, transfer_amount)
        """
        # Check if rebalancing conditions are met
        if not self.should_rebalance(current, next_subtitle, config):
            return current, next_subtitle, 0.0
        
        # Calculate how much time we want to add to current
        current_deficit = config.short_threshold - current.duration
        
        # Calculate how much we can take from next
        next_surplus = next_subtitle.duration - config.long_threshold
        
        # Transfer amount is minimum of deficit and surplus
        transfer_amount = min(current_deficit, next_surplus)
        
        if transfer_amount <= 0:
            return current, next_subtitle, 0.0
        
        # Apply the transfer while maintaining min_gap
        new_current_end = current.end_time + transfer_amount
        new_next_start = new_current_end + config.min_gap
        
        # Verify we don't create invalid state
        if new_next_start >= next_subtitle.end_time:
            return current, next_subtitle, 0.0  # Transfer would make next too short
        
        # Create new subtitles
        new_current = current.with_end_time(new_current_end)
        new_next = next_subtitle.with_start_time(new_next_start)
        
        # Validate the rebalancing
        if not self.validate_rebalancing(current, next_subtitle, new_current, new_next, config):
            return current, next_subtitle, 0.0
        
        return new_current, new_next, transfer_amount
    
    def should_rebalance(
        self, 
        current: Subtitle, 
        next_subtitle: Subtitle,
        config: OptimizationConfig
    ) -> bool:
        """Check if rebalancing conditions are met
        
        Args:
            current: Current subtitle
            next_subtitle: Next subtitle
            config: Optimization configuration
            
        Returns:
            True if rebalancing should be applied
        """
        is_current_short = current.duration < config.short_threshold
        is_next_long = next_subtitle.duration > config.long_threshold
        
        return is_current_short and is_next_long
    
    def calculate_transfer_amount(
        self, 
        current: Subtitle, 
        next_subtitle: Subtitle,
        config: OptimizationConfig
    ) -> float:
        """Calculate optimal transfer amount between subtitles
        
        Args:
            current: Current (short) subtitle
            next_subtitle: Next (long) subtitle
            config: Optimization configuration
            
        Returns:
            Amount of time to transfer (seconds)
        """
        # How much does current need?
        current_deficit = max(0, config.short_threshold - current.duration)
        
        # How much can next spare?
        next_surplus = max(0, next_subtitle.duration - config.long_threshold)
        
        # Transfer the minimum of what's needed and what's available
        return min(current_deficit, next_surplus)
    
    def get_available_transfer_space(
        self, 
        current: Subtitle, 
        next_subtitle: Subtitle,
        config: OptimizationConfig
    ) -> float:
        """Calculate how much space is available for rebalancing
        
        Args:
            current: Current subtitle
            next_subtitle: Next subtitle
            config: Optimization configuration
            
        Returns:
            Available space for transfer (seconds)
        """
        # Calculate current gap
        current_gap = next_subtitle.start_time - current.end_time
        
        # Available space is current gap minus required minimum gap
        available_space = current_gap - config.min_gap
        
        return max(0, available_space)
    
    def validate_rebalancing(
        self, 
        original_current: Subtitle,
        original_next: Subtitle,
        new_current: Subtitle,
        new_next: Subtitle,
        config: OptimizationConfig
    ) -> bool:
        """Validate that rebalancing is safe and beneficial
        
        Args:
            original_current: Original current subtitle
            original_next: Original next subtitle
            new_current: New current subtitle
            new_next: New next subtitle
            config: Optimization configuration
            
        Returns:
            True if rebalancing is valid
        """
        # Check that times are valid
        if new_current.start_time >= new_current.end_time:
            return False
        if new_next.start_time >= new_next.end_time:
            return False
        
        # Check that gap is maintained
        gap = new_next.start_time - new_current.end_time
        if gap < config.min_gap:
            return False
        
        # Check that current got longer (benefit)
        if new_current.duration <= original_current.duration:
            return False
        
        # Check that next didn't become too short
        if new_next.duration < config.min_duration:
            return False
        
        # Check that we didn't make next shorter than current was originally
        # (avoid creating new imbalances)
        if new_next.duration < original_current.duration:
            return False
        
        return True
    
    def estimate_benefit(
        self, 
        current: Subtitle, 
        next_subtitle: Subtitle,
        transfer_amount: float,
        config: OptimizationConfig
    ) -> float:
        """Estimate the benefit of rebalancing
        
        Args:
            current: Current subtitle
            next_subtitle: Next subtitle
            transfer_amount: Amount to transfer
            config: Optimization configuration
            
        Returns:
            Benefit score (higher is better)
        """
        if transfer_amount <= 0:
            return 0.0
        
        # Calculate how much closer to ideal we get
        current_deficit_before = max(0, config.short_threshold - current.duration)
        current_deficit_after = max(0, config.short_threshold - (current.duration + transfer_amount))
        current_improvement = current_deficit_before - current_deficit_after
        
        # Calculate cost in terms of next subtitle
        next_surplus_before = max(0, next_subtitle.duration - config.long_threshold)
        next_surplus_after = max(0, (next_subtitle.duration - transfer_amount) - config.long_threshold)
        next_cost = next_surplus_before - next_surplus_after
        
        # Benefit is improvement minus cost
        return current_improvement - (next_cost * 0.5)  # Weight cost less than benefit
    
    def find_optimal_transfer(
        self, 
        current: Subtitle, 
        next_subtitle: Subtitle,
        config: OptimizationConfig,
        max_transfer: float
    ) -> float:
        """Find optimal transfer amount through incremental search
        
        Args:
            current: Current subtitle
            next_subtitle: Next subtitle
            config: Optimization configuration
            max_transfer: Maximum allowed transfer
            
        Returns:
            Optimal transfer amount
        """
        best_transfer = 0.0
        best_benefit = 0.0
        
        # Try different transfer amounts
        step = 0.1  # 100ms steps
        transfer = step
        
        while transfer <= max_transfer:
            benefit = self.estimate_benefit(current, next_subtitle, transfer, config)
            
            if benefit > best_benefit:
                best_benefit = benefit
                best_transfer = transfer
            
            transfer += step
        
        return best_transfer