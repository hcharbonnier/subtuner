"""Optimization engine that coordinates all algorithms"""

import logging
from dataclasses import dataclass
from typing import List

from ..config import OptimizationConfig
from ..errors import OptimizationError
from ..parsers.base import Subtitle
from .algorithms.duration_adjuster import DurationAdjuster
from .algorithms.rebalancer import TemporalRebalancer
from .algorithms.anticipator import AnticipationAdjuster
from .algorithms.validator import ConstraintsValidator
from .statistics import OptimizationStatistics

logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    """Result of subtitle optimization"""
    
    subtitles: List[Subtitle]
    statistics: OptimizationStatistics
    original_count: int
    final_count: int
    
    @property
    def success(self) -> bool:
        """Check if optimization was successful"""
        return len(self.subtitles) > 0
    
    @property
    def improvement_summary(self) -> dict:
        """Get improvement summary"""
        return {
            'total_modifications': self.statistics.total_modifications,
            'modification_percentage': self.statistics.modification_percentage,
            'processing_time': self.statistics.processing_time,
            'subtitles_retained': self.final_count,
            'subtitles_removed': self.original_count - self.final_count,
        }


class OptimizationEngine:
    """Main optimization engine that coordinates all algorithms"""
    
    def __init__(self):
        """Initialize the optimization engine"""
        self.duration_adjuster = DurationAdjuster()
        self.rebalancer = TemporalRebalancer()
        self.anticipator = AnticipationAdjuster()
        self.validator = ConstraintsValidator()
        
        logger.debug("OptimizationEngine initialized with all algorithms")
    
    def optimize(
        self, 
        subtitles: List[Subtitle], 
        config: OptimizationConfig,
        track_index: int = 0
    ) -> OptimizationResult:
        """Apply all optimization algorithms in sequence
        
        Args:
            subtitles: List of subtitles to optimize
            config: Optimization configuration
            track_index: Track index for statistics
            
        Returns:
            OptimizationResult with optimized subtitles and statistics
            
        Raises:
            OptimizationError: If optimization fails
        """
        if not subtitles:
            logger.warning("No subtitles provided for optimization")
            return OptimizationResult(
                subtitles=[],
                statistics=OptimizationStatistics(track_index=track_index),
                original_count=0,
                final_count=0
            )
        
        logger.info(f"Starting optimization of {len(subtitles)} subtitles")
        
        # Initialize statistics
        stats = OptimizationStatistics(track_index=track_index)
        stats.original_subtitle_count = len(subtitles)
        stats.start_timing()
        
        try:
            # Apply optimization pipeline
            optimized = self._apply_optimization_pipeline(subtitles, config, stats)
            
            # Finalize statistics
            stats.final_subtitle_count = len(optimized)
            stats.stop_timing()
            
            result = OptimizationResult(
                subtitles=optimized,
                statistics=stats,
                original_count=len(subtitles),
                final_count=len(optimized)
            )
            
            logger.info(
                f"Optimization complete: {stats.total_modifications} modifications in {stats.processing_time:.2f}s"
            )
            
            return result
            
        except Exception as e:
            stats.stop_timing()
            logger.error(f"Optimization failed: {e}")
            raise OptimizationError(f"Optimization failed: {e}") from e
    
    def _apply_optimization_pipeline(
        self,
        subtitles: List[Subtitle],
        config: OptimizationConfig,
        stats: OptimizationStatistics
    ) -> List[Subtitle]:
        """Apply the complete optimization pipeline
        
        Args:
            subtitles: Input subtitles
            config: Optimization configuration
            stats: Statistics tracker
            
        Returns:
            Optimized subtitles
        """
        # Detect original overlaps to preserve them
        original_overlaps = self._detect_original_overlaps(subtitles)
        logger.debug(f"Detected {len(original_overlaps)} original overlaps to preserve")
        
        current = subtitles.copy()
        
        # Phase 1: Duration Adjustment
        logger.debug("Phase 1: Duration adjustment")
        current = self.duration_adjuster.process(current, config, stats)
        logger.debug(f"After duration adjustment: {len(current)} subtitles")
        
        # Phase 2: Temporal Rebalancing
        logger.debug("Phase 2: Temporal rebalancing")
        current = self.rebalancer.process(current, config, stats)
        logger.debug(f"After rebalancing: {len(current)} subtitles")
        
        # Phase 3: Anticipatory Offset
        logger.debug("Phase 3: Anticipatory offset")
        current = self.anticipator.process(current, config, stats)
        logger.debug(f"After anticipation: {len(current)} subtitles")
        
        # Phase 4: Constraints Validation (with overlap preservation)
        logger.debug("Phase 4: Constraints validation")
        current = self.validator.process(current, config, stats, allowed_overlaps=original_overlaps)
        logger.debug(f"After validation: {len(current)} subtitles")
        
        return current
    
    def _detect_original_overlaps(self, subtitles: List[Subtitle]) -> set:
        """Detect pairs of subtitles that overlap in original timing
        
        Args:
            subtitles: Original subtitles
            
        Returns:
            Set of (index1, index2) tuples for overlapping pairs
        """
        overlaps = set()
        
        for i in range(len(subtitles) - 1):
            current = subtitles[i]
            next_sub = subtitles[i + 1]
            
            # Check if they overlap
            if current.end_time > next_sub.start_time:
                overlaps.add((i, i + 1))
                logger.debug(f"Original overlap detected between subtitle {i} and {i+1}")
        
        return overlaps
    
    def analyze_subtitles(
        self, 
        subtitles: List[Subtitle], 
        config: OptimizationConfig
    ) -> dict:
        """Analyze subtitles without optimization to understand potential improvements
        
        Args:
            subtitles: List of subtitles to analyze
            config: Optimization configuration
            
        Returns:
            Analysis results
        """
        if not subtitles:
            return {'error': 'No subtitles to analyze'}
        
        logger.info(f"Analyzing {len(subtitles)} subtitles")
        
        analysis = {
            'total_subtitles': len(subtitles),
            'duration_stats': self._analyze_durations(subtitles, config),
            'gap_stats': self._analyze_gaps(subtitles, config),
            'reading_speed_stats': self._analyze_reading_speeds(subtitles, config),
            'optimization_potential': {},
        }
        
        # Get potential improvements from each algorithm
        analysis['optimization_potential'].update({
            'anticipation': self.anticipator.analyze_anticipation_potential(subtitles, config),
            'validation': self.validator.validate_sequence(subtitles, config),
        })
        
        return analysis
    
    def _analyze_durations(
        self, 
        subtitles: List[Subtitle], 
        config: OptimizationConfig
    ) -> dict:
        """Analyze subtitle durations"""
        durations = [sub.duration for sub in subtitles]
        
        return {
            'min': min(durations),
            'max': max(durations),
            'avg': sum(durations) / len(durations),
            'below_min': sum(1 for d in durations if d < config.min_duration),
            'above_max': sum(1 for d in durations if d > config.max_duration),
            'total_duration': sum(durations),
        }
    
    def _analyze_gaps(
        self, 
        subtitles: List[Subtitle], 
        config: OptimizationConfig
    ) -> dict:
        """Analyze gaps between subtitles"""
        if len(subtitles) < 2:
            return {'error': 'Need at least 2 subtitles to analyze gaps'}
        
        gaps = []
        overlaps = 0
        
        for i in range(len(subtitles) - 1):
            gap = subtitles[i + 1].start_time - subtitles[i].end_time
            gaps.append(gap)
            if gap < 0:
                overlaps += 1
        
        return {
            'min_gap': min(gaps),
            'max_gap': max(gaps),
            'avg_gap': sum(gaps) / len(gaps),
            'overlaps': overlaps,
            'below_min_gap': sum(1 for g in gaps if 0 <= g < config.min_gap),
            'negative_gaps': sum(1 for g in gaps if g < 0),
        }
    
    def _analyze_reading_speeds(
        self, 
        subtitles: List[Subtitle], 
        config: OptimizationConfig
    ) -> dict:
        """Analyze reading speeds"""
        speeds = []
        
        for subtitle in subtitles:
            if subtitle.duration > 0:
                speed = subtitle.char_count / subtitle.duration
                speeds.append(speed)
        
        if not speeds:
            return {'error': 'No valid subtitles for reading speed analysis'}
        
        return {
            'min_speed': min(speeds),
            'max_speed': max(speeds),
            'avg_speed': sum(speeds) / len(speeds),
            'target_speed': config.chars_per_sec,
            'above_target': sum(1 for s in speeds if s > config.chars_per_sec),
            'below_target': sum(1 for s in speeds if s < config.chars_per_sec),
        }
    
    def preview_optimization(
        self, 
        subtitles: List[Subtitle], 
        config: OptimizationConfig,
        sample_size: int = 10
    ) -> dict:
        """Preview optimization changes on a sample of subtitles
        
        Args:
            subtitles: List of subtitles
            config: Optimization configuration
            sample_size: Number of subtitles to sample
            
        Returns:
            Preview results
        """
        if not subtitles:
            return {'error': 'No subtitles to preview'}
        
        # Take a representative sample
        step = max(1, len(subtitles) // sample_size)
        sample_indices = list(range(0, len(subtitles), step))[:sample_size]
        
        preview_results = []
        
        for i in sample_indices:
            original = subtitles[i]
            
            # Create mini-context (previous and next if available)
            context_start = max(0, i - 1)
            context_end = min(len(subtitles), i + 2)
            context = subtitles[context_start:context_end]
            context_i = i - context_start
            
            # Apply optimization to context
            stats = OptimizationStatistics()
            optimized_context = self._apply_optimization_pipeline(context, config, stats)
            
            if context_i < len(optimized_context):
                optimized = optimized_context[context_i]
                
                preview_results.append({
                    'index': i,
                    'original': {
                        'start': original.start_time,
                        'end': original.end_time,
                        'duration': original.duration,
                        'text': original.text[:50] + ('...' if len(original.text) > 50 else ''),
                        'char_count': original.char_count,
                    },
                    'optimized': {
                        'start': optimized.start_time,
                        'end': optimized.end_time,
                        'duration': optimized.duration,
                        'text': optimized.text[:50] + ('...' if len(optimized.text) > 50 else ''),
                        'char_count': optimized.char_count,
                    },
                    'changes': {
                        'start_change': optimized.start_time - original.start_time,
                        'end_change': optimized.end_time - original.end_time,
                        'duration_change': optimized.duration - original.duration,
                    }
                })
        
        return {
            'sample_size': len(preview_results),
            'total_subtitles': len(subtitles),
            'previews': preview_results,
        }
    
    def get_algorithm_info(self) -> dict:
        """Get information about available algorithms
        
        Returns:
            Algorithm information
        """
        return {
            'algorithms': [
                {
                    'name': self.duration_adjuster.name,
                    'phase': 1,
                    'description': 'Adjusts subtitle duration based on reading speed'
                },
                {
                    'name': self.rebalancer.name,
                    'phase': 2,
                    'description': 'Transfers time from long subtitles to short ones'
                },
                {
                    'name': self.anticipator.name,
                    'phase': 3,
                    'description': 'Starts subtitles earlier when beneficial'
                },
                {
                    'name': self.validator.name,
                    'phase': 4,
                    'description': 'Enforces timing constraints and fixes violations'
                }
            ],
            'execution_order': 'Sequential pipeline in phase order',
            'principles': [
                'Readability first',
                'Semantic preservation', 
                'Graceful degradation',
                'Deterministic results'
            ]
        }