"""Statistics tracking for optimization algorithms"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class OptimizationStatistics:
    """Statistics collected during subtitle optimization"""
    
    # Track metadata
    track_index: int = 0
    original_subtitle_count: int = 0
    final_subtitle_count: int = 0
    
    # Merging
    merged_subtitles: int = 0
    
    # Duration adjustments
    duration_adjustments: int = 0
    total_duration_change: float = 0.0
    duration_changes: List[float] = field(default_factory=list)
    
    # Rebalancing
    rebalanced_pairs: int = 0
    total_time_transferred: float = 0.0
    rebalancing_transfers: List[float] = field(default_factory=list)
    
    # Anticipation
    anticipated_subtitles: int = 0
    total_anticipation: float = 0.0
    anticipation_amounts: List[float] = field(default_factory=list)
    
    # Validation fixes
    min_duration_fixes: int = 0
    gap_fixes: int = 0
    chronology_fixes: int = 0
    invalid_removed: int = 0
    
    # Performance metrics
    processing_time: float = 0.0
    start_time: Optional[float] = None
    
    def start_timing(self) -> None:
        """Start timing the optimization process"""
        self.start_time = time.time()
    
    def stop_timing(self) -> None:
        """Stop timing and calculate processing time"""
        if self.start_time is not None:
            self.processing_time = time.time() - self.start_time
    
    def add_duration_change(self, change: float) -> None:
        """Record a duration adjustment"""
        if abs(change) > 0.01:  # Only count significant changes
            self.duration_adjustments += 1
            self.total_duration_change += change
            self.duration_changes.append(change)
    
    def add_rebalancing_transfer(self, transfer: float) -> None:
        """Record a rebalancing transfer"""
        if transfer > 0.01:  # Only count significant transfers
            self.rebalanced_pairs += 1
            self.total_time_transferred += transfer
            self.rebalancing_transfers.append(transfer)
    
    def add_anticipation(self, anticipation: float) -> None:
        """Record an anticipatory adjustment"""
        if anticipation > 0.01:  # Only count significant anticipation
            self.anticipated_subtitles += 1
            self.total_anticipation += anticipation
            self.anticipation_amounts.append(anticipation)
    
    @property
    def avg_duration_change(self) -> float:
        """Calculate average duration change"""
        if self.duration_adjustments == 0:
            return 0.0
        return self.total_duration_change / self.duration_adjustments
    
    @property
    def avg_anticipation(self) -> float:
        """Calculate average anticipation amount"""
        if self.anticipated_subtitles == 0:
            return 0.0
        return self.total_anticipation / self.anticipated_subtitles
    
    @property
    def total_modifications(self) -> int:
        """Calculate total number of modifications made"""
        return (
            self.merged_subtitles +
            self.duration_adjustments +
            self.rebalanced_pairs +
            self.anticipated_subtitles +
            self.min_duration_fixes +
            self.gap_fixes +
            self.chronology_fixes
        )
    
    @property
    def modification_percentage(self) -> float:
        """Calculate percentage of subtitles that were modified"""
        if self.original_subtitle_count == 0:
            return 0.0
        return (self.total_modifications / self.original_subtitle_count) * 100
    
    def get_summary(self) -> Dict[str, any]:
        """Get summary statistics as dictionary"""
        return {
            'original_count': self.original_subtitle_count,
            'final_count': self.final_subtitle_count,
            'processing_time': round(self.processing_time, 3),
            'total_modifications': self.total_modifications,
            'modification_percentage': round(self.modification_percentage, 1),
            'merged_subtitles': self.merged_subtitles,
            'duration_adjustments': self.duration_adjustments,
            'avg_duration_change': round(self.avg_duration_change, 3),
            'rebalanced_pairs': self.rebalanced_pairs,
            'total_time_transferred': round(self.total_time_transferred, 3),
            'anticipated_subtitles': self.anticipated_subtitles,
            'avg_anticipation': round(self.avg_anticipation, 3),
            'validation_fixes': {
                'min_duration': self.min_duration_fixes,
                'gaps': self.gap_fixes,
                'chronology': self.chronology_fixes,
                'invalid_removed': self.invalid_removed,
            }
        }
    
    def __str__(self) -> str:
        """Human-readable string representation"""
        lines = [
            f"Optimization Statistics:",
            f"  Original Subtitles: {self.original_subtitle_count:,}",
            f"  Final Subtitles: {self.final_subtitle_count:,}",
            f"  Processing Time: {self.processing_time:.2f}s",
            f"",
            f"  Merged Subtitles: {self.merged_subtitles:,}",
            f"",
            f"  Duration Adjustments: {self.duration_adjustments:,} ({self.duration_adjustments/self.original_subtitle_count*100:.1f}%)" if self.original_subtitle_count > 0 else f"  Duration Adjustments: {self.duration_adjustments:,}",
            f"    Average Change: {self.avg_duration_change:+.3f}s",
            f"",
            f"  Rebalanced Pairs: {self.rebalanced_pairs:,}",
            f"    Total Time Transferred: {self.total_time_transferred:.3f}s",
            f"",
            f"  Anticipated Subtitles: {self.anticipated_subtitles:,} ({self.anticipated_subtitles/self.original_subtitle_count*100:.1f}%)" if self.original_subtitle_count > 0 else f"  Anticipated Subtitles: {self.anticipated_subtitles:,}",
            f"    Average Anticipation: {self.avg_anticipation:.3f}s",
            f"",
            f"  Validation Fixes:",
            f"    Min Duration: {self.min_duration_fixes:,}",
            f"    Gap Fixes: {self.gap_fixes:,}",
            f"    Chronology: {self.chronology_fixes:,}",
            f"    Invalid Removed: {self.invalid_removed:,}",
            f"",
            f"  Total Modifications: {self.total_modifications:,} ({self.modification_percentage:.1f}%)",
        ]
        return '\n'.join(lines)