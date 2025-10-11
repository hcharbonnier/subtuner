"""Statistics reporting for SubTuner optimization results"""

import json
import logging
import time
from dataclasses import asdict
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union

from ..optimization.statistics import OptimizationStatistics

logger = logging.getLogger(__name__)


class ReportFormat(Enum):
    """Supported report output formats"""
    CONSOLE = "console"
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"


class StatisticsReporter:
    """Generates reports from optimization statistics"""
    
    def __init__(self):
        """Initialize the statistics reporter"""
        self.total_processing_time = 0.0
        self.session_start_time = None
    
    def start_session(self) -> None:
        """Start a reporting session"""
        self.session_start_time = time.time()
        logger.debug("Statistics session started")
    
    def end_session(self) -> None:
        """End a reporting session"""
        if self.session_start_time:
            self.total_processing_time = time.time() - self.session_start_time
            logger.debug(f"Statistics session ended: {self.total_processing_time:.2f}s")
    
    def generate_single_track_report(
        self, 
        video_path: str,
        track_stats: OptimizationStatistics,
        format: ReportFormat = ReportFormat.CONSOLE
    ) -> str:
        """Generate report for a single subtitle track
        
        Args:
            video_path: Path to the video file
            track_stats: Statistics for the track
            format: Output format
            
        Returns:
            Formatted report string
        """
        if format == ReportFormat.CONSOLE:
            return self._generate_console_single_report(video_path, track_stats)
        elif format == ReportFormat.JSON:
            return self._generate_json_single_report(video_path, track_stats)
        elif format == ReportFormat.MARKDOWN:
            return self._generate_markdown_single_report(video_path, track_stats)
        elif format == ReportFormat.CSV:
            return self._generate_csv_single_report(video_path, track_stats)
        else:
            raise ValueError(f"Unsupported report format: {format}")
    
    def generate_multi_track_report(
        self,
        video_path: str,
        all_tracks_stats: List[OptimizationStatistics],
        format: ReportFormat = ReportFormat.CONSOLE
    ) -> str:
        """Generate report for multiple subtitle tracks
        
        Args:
            video_path: Path to the video file
            all_tracks_stats: Statistics for all tracks
            format: Output format
            
        Returns:
            Formatted report string
        """
        if format == ReportFormat.CONSOLE:
            return self._generate_console_multi_report(video_path, all_tracks_stats)
        elif format == ReportFormat.JSON:
            return self._generate_json_multi_report(video_path, all_tracks_stats)
        elif format == ReportFormat.MARKDOWN:
            return self._generate_markdown_multi_report(video_path, all_tracks_stats)
        elif format == ReportFormat.CSV:
            return self._generate_csv_multi_report(video_path, all_tracks_stats)
        else:
            raise ValueError(f"Unsupported report format: {format}")
    
    def generate_batch_report(
        self,
        batch_results: Dict[str, List[OptimizationStatistics]],
        format: ReportFormat = ReportFormat.CONSOLE
    ) -> str:
        """Generate report for batch processing results
        
        Args:
            batch_results: Dictionary mapping video paths to track statistics
            format: Output format
            
        Returns:
            Formatted report string
        """
        if format == ReportFormat.CONSOLE:
            return self._generate_console_batch_report(batch_results)
        elif format == ReportFormat.JSON:
            return self._generate_json_batch_report(batch_results)
        elif format == ReportFormat.MARKDOWN:
            return self._generate_markdown_batch_report(batch_results)
        elif format == ReportFormat.CSV:
            return self._generate_csv_batch_report(batch_results)
        else:
            raise ValueError(f"Unsupported report format: {format}")
    
    # Console format implementations
    
    def _generate_console_single_report(
        self, 
        video_path: str,
        stats: OptimizationStatistics
    ) -> str:
        """Generate console report for single track"""
        lines = []
        video_name = Path(video_path).name
        
        lines.extend([
            "=" * 60,
            "SubTuner Optimization Report",
            "=" * 60,
            "",
            f"Video: {video_name}",
            f"Processing Time: {stats.processing_time:.2f} seconds",
            "",
            f"Track {stats.track_index} Results:",
            f"  Original Subtitles: {stats.original_subtitle_count:,}",
            f"  Final Subtitles: {stats.final_subtitle_count:,}",
        ])
        
        if stats.final_subtitle_count != stats.original_subtitle_count:
            removed = stats.original_subtitle_count - stats.final_subtitle_count
            lines.append(f"  Removed: {removed:,} ({removed/stats.original_subtitle_count*100:.1f}%)")
        
        lines.extend([
            "",
            "Optimization Results:",
            f"  Duration Adjustments: {stats.duration_adjustments:,} ({stats.duration_adjustments/stats.original_subtitle_count*100:.1f}%)" if stats.original_subtitle_count > 0 else f"  Duration Adjustments: {stats.duration_adjustments:,}",
            f"    Average Change: {stats.avg_duration_change:+.3f}s",
            f"    Total Change: {stats.total_duration_change:+.3f}s",
            "",
            f"  Rebalanced Pairs: {stats.rebalanced_pairs:,}",
            f"    Total Time Transferred: {stats.total_time_transferred:.3f}s",
        ])
        
        if stats.rebalanced_pairs > 0:
            avg_transfer = stats.total_time_transferred / stats.rebalanced_pairs
            lines.append(f"    Average Transfer: {avg_transfer:.3f}s")
        
        lines.extend([
            "",
            f"  Anticipated Subtitles: {stats.anticipated_subtitles:,} ({stats.anticipated_subtitles/stats.original_subtitle_count*100:.1f}%)" if stats.original_subtitle_count > 0 else f"  Anticipated Subtitles: {stats.anticipated_subtitles:,}",
            f"    Average Anticipation: {stats.avg_anticipation:.3f}s",
            f"    Total Anticipation: {stats.total_anticipation:.3f}s",
            "",
            "Validation Fixes:",
            f"  Minimum Duration: {stats.min_duration_fixes:,}",
            f"  Gap Fixes: {stats.gap_fixes:,}",
            f"  Chronology Fixes: {stats.chronology_fixes:,}",
            f"  Invalid Removed: {stats.invalid_removed:,}",
            "",
            f"Total Modifications: {stats.total_modifications:,} ({stats.modification_percentage:.1f}%)",
            "",
            "=" * 60,
        ])
        
        return '\n'.join(lines)
    
    def _generate_console_multi_report(
        self,
        video_path: str,
        all_stats: List[OptimizationStatistics]
    ) -> str:
        """Generate console report for multiple tracks"""
        lines = []
        video_name = Path(video_path).name
        total_processing_time = sum(s.processing_time for s in all_stats)
        
        lines.extend([
            "=" * 60,
            "SubTuner Multi-Track Optimization Report",
            "=" * 60,
            "",
            f"Video: {video_name}",
            f"Tracks Processed: {len(all_stats)}",
            f"Total Processing Time: {total_processing_time:.2f} seconds",
            "",
        ])
        
        # Individual track summaries
        for stats in all_stats:
            lines.extend([
                f"Track {stats.track_index}:",
                f"  Subtitles: {stats.original_subtitle_count:,} → {stats.final_subtitle_count:,}",
                f"  Modifications: {stats.total_modifications:,} ({stats.modification_percentage:.1f}%)",
                f"  Processing: {stats.processing_time:.2f}s",
                "",
            ])
        
        # Aggregate statistics
        total_original = sum(s.original_subtitle_count for s in all_stats)
        total_final = sum(s.final_subtitle_count for s in all_stats)
        total_modifications = sum(s.total_modifications for s in all_stats)
        total_duration_adjustments = sum(s.duration_adjustments for s in all_stats)
        total_rebalanced = sum(s.rebalanced_pairs for s in all_stats)
        total_anticipated = sum(s.anticipated_subtitles for s in all_stats)
        
        lines.extend([
            "Aggregate Results:",
            f"  Total Original Subtitles: {total_original:,}",
            f"  Total Final Subtitles: {total_final:,}",
            f"  Total Modifications: {total_modifications:,}",
            f"  Duration Adjustments: {total_duration_adjustments:,}",
            f"  Rebalanced Pairs: {total_rebalanced:,}",
            f"  Anticipated Subtitles: {total_anticipated:,}",
            "",
            "=" * 60,
        ])
        
        return '\n'.join(lines)
    
    def _generate_console_batch_report(
        self,
        batch_results: Dict[str, List[OptimizationStatistics]]
    ) -> str:
        """Generate console report for batch processing"""
        lines = []
        total_videos = len(batch_results)
        total_tracks = sum(len(tracks) for tracks in batch_results.values())
        
        lines.extend([
            "=" * 60,
            "SubTuner Batch Processing Report",
            "=" * 60,
            "",
            f"Videos Processed: {total_videos:,}",
            f"Tracks Processed: {total_tracks:,}",
            f"Session Time: {self.total_processing_time:.2f} seconds",
            "",
            "Per-Video Results:",
            "",
        ])
        
        # Per-video summaries
        for video_path, track_stats in batch_results.items():
            video_name = Path(video_path).name
            video_processing_time = sum(s.processing_time for s in track_stats)
            total_subtitles = sum(s.original_subtitle_count for s in track_stats)
            total_mods = sum(s.total_modifications for s in track_stats)
            
            lines.extend([
                f"{video_name}:",
                f"  Tracks: {len(track_stats)}",
                f"  Subtitles: {total_subtitles:,}",
                f"  Modifications: {total_mods:,}",
                f"  Time: {video_processing_time:.2f}s",
                "",
            ])
        
        # Global aggregates
        all_stats = [stat for tracks in batch_results.values() for stat in tracks]
        global_original = sum(s.original_subtitle_count for s in all_stats)
        global_final = sum(s.final_subtitle_count for s in all_stats)
        global_modifications = sum(s.total_modifications for s in all_stats)
        global_processing_time = sum(s.processing_time for s in all_stats)
        
        lines.extend([
            "Global Statistics:",
            f"  Total Original Subtitles: {global_original:,}",
            f"  Total Final Subtitles: {global_final:,}",
            f"  Total Modifications: {global_modifications:,}",
            f"  Total Processing Time: {global_processing_time:.2f}s",
            f"  Average Speed: {global_original/global_processing_time:.0f} subtitles/sec" if global_processing_time > 0 else "  Average Speed: N/A",
            "",
            "=" * 60,
        ])
        
        return '\n'.join(lines)
    
    # JSON format implementations
    
    def _generate_json_single_report(
        self,
        video_path: str,
        stats: OptimizationStatistics
    ) -> str:
        """Generate JSON report for single track"""
        report = {
            "video_path": video_path,
            "video_name": Path(video_path).name,
            "track_statistics": self._stats_to_dict(stats),
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        }
        return json.dumps(report, indent=2)
    
    def _generate_json_multi_report(
        self,
        video_path: str,
        all_stats: List[OptimizationStatistics]
    ) -> str:
        """Generate JSON report for multiple tracks"""
        report = {
            "video_path": video_path,
            "video_name": Path(video_path).name,
            "total_tracks": len(all_stats),
            "total_processing_time": sum(s.processing_time for s in all_stats),
            "tracks": [self._stats_to_dict(stats) for stats in all_stats],
            "aggregates": self._calculate_aggregates(all_stats),
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        }
        return json.dumps(report, indent=2)
    
    def _generate_json_batch_report(
        self,
        batch_results: Dict[str, List[OptimizationStatistics]]
    ) -> str:
        """Generate JSON report for batch processing"""
        videos = []
        for video_path, track_stats in batch_results.items():
            videos.append({
                "video_path": video_path,
                "video_name": Path(video_path).name,
                "tracks": [self._stats_to_dict(stats) for stats in track_stats],
                "aggregates": self._calculate_aggregates(track_stats),
            })
        
        all_stats = [stat for tracks in batch_results.values() for stat in tracks]
        
        report = {
            "batch_summary": {
                "total_videos": len(batch_results),
                "total_tracks": len(all_stats),
                "session_time": self.total_processing_time,
            },
            "videos": videos,
            "global_aggregates": self._calculate_aggregates(all_stats),
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        }
        return json.dumps(report, indent=2)
    
    # Markdown format implementations
    
    def _generate_markdown_single_report(
        self,
        video_path: str,
        stats: OptimizationStatistics
    ) -> str:
        """Generate Markdown report for single track"""
        video_name = Path(video_path).name
        
        lines = [
            f"# SubTuner Optimization Report",
            f"",
            f"**Video:** `{video_name}`  ",
            f"**Processing Time:** {stats.processing_time:.2f} seconds  ",
            f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}",
            f"",
            f"## Track {stats.track_index} Results",
            f"",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Original Subtitles | {stats.original_subtitle_count:,} |",
            f"| Final Subtitles | {stats.final_subtitle_count:,} |",
            f"| Duration Adjustments | {stats.duration_adjustments:,} ({stats.duration_adjustments/stats.original_subtitle_count*100:.1f}%) |" if stats.original_subtitle_count > 0 else f"| Duration Adjustments | {stats.duration_adjustments:,} |",
            f"| Average Duration Change | {stats.avg_duration_change:+.3f}s |",
            f"| Rebalanced Pairs | {stats.rebalanced_pairs:,} |",
            f"| Time Transferred | {stats.total_time_transferred:.3f}s |",
            f"| Anticipated Subtitles | {stats.anticipated_subtitles:,} ({stats.anticipated_subtitles/stats.original_subtitle_count*100:.1f}%) |" if stats.original_subtitle_count > 0 else f"| Anticipated Subtitles | {stats.anticipated_subtitles:,} |",
            f"| Average Anticipation | {stats.avg_anticipation:.3f}s |",
            f"| **Total Modifications** | **{stats.total_modifications:,} ({stats.modification_percentage:.1f}%)** |",
            f"",
            f"## Validation Fixes",
            f"",
            f"- Minimum Duration: {stats.min_duration_fixes:,}",
            f"- Gap Fixes: {stats.gap_fixes:,}",
            f"- Chronology Fixes: {stats.chronology_fixes:,}",
            f"- Invalid Removed: {stats.invalid_removed:,}",
        ]
        
        return '\n'.join(lines)
    
    def _generate_markdown_multi_report(
        self,
        video_path: str,
        all_stats: List[OptimizationStatistics]
    ) -> str:
        """Generate Markdown report for multiple tracks"""
        video_name = Path(video_path).name
        total_processing_time = sum(s.processing_time for s in all_stats)
        
        lines = [
            f"# SubTuner Multi-Track Report",
            f"",
            f"**Video:** `{video_name}`  ",
            f"**Tracks:** {len(all_stats)}  ",
            f"**Total Processing Time:** {total_processing_time:.2f} seconds",
            f"",
            f"## Track Summary",
            f"",
            f"| Track | Subtitles | Modifications | Time |",
            f"|-------|-----------|---------------|------|",
        ]
        
        for stats in all_stats:
            lines.append(
                f"| {stats.track_index} | {stats.original_subtitle_count:,} → {stats.final_subtitle_count:,} | "
                f"{stats.total_modifications:,} ({stats.modification_percentage:.1f}%) | {stats.processing_time:.2f}s |"
            )
        
        aggregates = self._calculate_aggregates(all_stats)
        lines.extend([
            f"",
            f"## Aggregate Results",
            f"",
            f"| Metric | Total |",
            f"|--------|-------|",
            f"| Original Subtitles | {aggregates['total_original']:,} |",
            f"| Final Subtitles | {aggregates['total_final']:,} |",
            f"| Modifications | {aggregates['total_modifications']:,} |",
            f"| Duration Adjustments | {aggregates['total_duration_adjustments']:,} |",
            f"| Rebalanced Pairs | {aggregates['total_rebalanced']:,} |",
            f"| Anticipated Subtitles | {aggregates['total_anticipated']:,} |",
        ])
        
        return '\n'.join(lines)
    
    def _generate_markdown_batch_report(
        self,
        batch_results: Dict[str, List[OptimizationStatistics]]
    ) -> str:
        """Generate Markdown report for batch processing"""
        lines = [
            f"# SubTuner Batch Processing Report",
            f"",
            f"**Videos Processed:** {len(batch_results):,}  ",
            f"**Total Tracks:** {sum(len(tracks) for tracks in batch_results.values()):,}  ",
            f"**Session Time:** {self.total_processing_time:.2f} seconds",
            f"",
            f"## Video Results",
            f"",
            f"| Video | Tracks | Subtitles | Modifications | Time |",
            f"|-------|--------|-----------|---------------|------|",
        ]
        
        for video_path, track_stats in batch_results.items():
            video_name = Path(video_path).name
            video_processing_time = sum(s.processing_time for s in track_stats)
            total_subtitles = sum(s.original_subtitle_count for s in track_stats)
            total_mods = sum(s.total_modifications for s in track_stats)
            
            lines.append(
                f"| `{video_name}` | {len(track_stats)} | {total_subtitles:,} | "
                f"{total_mods:,} | {video_processing_time:.2f}s |"
            )
        
        all_stats = [stat for tracks in batch_results.values() for stat in tracks]
        global_aggregates = self._calculate_aggregates(all_stats)
        
        lines.extend([
            f"",
            f"## Global Statistics",
            f"",
            f"| Metric | Total |",
            f"|--------|-------|",
            f"| Original Subtitles | {global_aggregates['total_original']:,} |",
            f"| Final Subtitles | {global_aggregates['total_final']:,} |",
            f"| Modifications | {global_aggregates['total_modifications']:,} |",
            f"| Processing Time | {global_aggregates['total_processing_time']:.2f}s |",
            f"| Average Speed | {global_aggregates['total_original']/global_aggregates['total_processing_time']:.0f} subtitles/sec |" if global_aggregates['total_processing_time'] > 0 else f"| Average Speed | N/A |",
        ])
        
        return '\n'.join(lines)
    
    # CSV format implementations
    
    def _generate_csv_single_report(
        self,
        video_path: str,
        stats: OptimizationStatistics
    ) -> str:
        """Generate CSV report for single track"""
        lines = [
            "metric,value",
            f"video_path,{video_path}",
            f"track_index,{stats.track_index}",
            f"original_subtitles,{stats.original_subtitle_count}",
            f"final_subtitles,{stats.final_subtitle_count}",
            f"duration_adjustments,{stats.duration_adjustments}",
            f"avg_duration_change,{stats.avg_duration_change:.3f}",
            f"rebalanced_pairs,{stats.rebalanced_pairs}",
            f"time_transferred,{stats.total_time_transferred:.3f}",
            f"anticipated_subtitles,{stats.anticipated_subtitles}",
            f"avg_anticipation,{stats.avg_anticipation:.3f}",
            f"total_modifications,{stats.total_modifications}",
            f"modification_percentage,{stats.modification_percentage:.1f}",
            f"processing_time,{stats.processing_time:.3f}",
        ]
        return '\n'.join(lines)
    
    def _generate_csv_multi_report(
        self,
        video_path: str,
        all_stats: List[OptimizationStatistics]
    ) -> str:
        """Generate CSV report for multiple tracks"""
        lines = [
            "video_path,track_index,original_subtitles,final_subtitles,duration_adjustments,"
            "rebalanced_pairs,anticipated_subtitles,total_modifications,processing_time"
        ]
        
        for stats in all_stats:
            lines.append(
                f"{video_path},{stats.track_index},{stats.original_subtitle_count},"
                f"{stats.final_subtitle_count},{stats.duration_adjustments},"
                f"{stats.rebalanced_pairs},{stats.anticipated_subtitles},"
                f"{stats.total_modifications},{stats.processing_time:.3f}"
            )
        
        return '\n'.join(lines)
    
    def _generate_csv_batch_report(
        self,
        batch_results: Dict[str, List[OptimizationStatistics]]
    ) -> str:
        """Generate CSV report for batch processing"""
        lines = [
            "video_path,track_index,original_subtitles,final_subtitles,duration_adjustments,"
            "rebalanced_pairs,anticipated_subtitles,total_modifications,processing_time"
        ]
        
        for video_path, track_stats in batch_results.items():
            for stats in track_stats:
                lines.append(
                    f"{video_path},{stats.track_index},{stats.original_subtitle_count},"
                    f"{stats.final_subtitle_count},{stats.duration_adjustments},"
                    f"{stats.rebalanced_pairs},{stats.anticipated_subtitles},"
                    f"{stats.total_modifications},{stats.processing_time:.3f}"
                )
        
        return '\n'.join(lines)
    
    # Helper methods
    
    def _stats_to_dict(self, stats: OptimizationStatistics) -> dict:
        """Convert OptimizationStatistics to dictionary"""
        stats_dict = asdict(stats)
        # Remove non-serializable fields
        stats_dict.pop('start_time', None)
        return stats_dict
    
    def _calculate_aggregates(self, stats_list: List[OptimizationStatistics]) -> dict:
        """Calculate aggregate statistics"""
        if not stats_list:
            return {}
        
        return {
            "total_original": sum(s.original_subtitle_count for s in stats_list),
            "total_final": sum(s.final_subtitle_count for s in stats_list),
            "total_modifications": sum(s.total_modifications for s in stats_list),
            "total_duration_adjustments": sum(s.duration_adjustments for s in stats_list),
            "total_rebalanced": sum(s.rebalanced_pairs for s in stats_list),
            "total_anticipated": sum(s.anticipated_subtitles for s in stats_list),
            "total_processing_time": sum(s.processing_time for s in stats_list),
        }
    
    def save_report(
        self,
        report_content: str,
        output_path: str,
        format: ReportFormat
    ) -> None:
        """Save report to file
        
        Args:
            report_content: Report content to save
            output_path: Path to save report
            format: Report format (determines file extension if not specified)
        """
        try:
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Write report
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            logger.info(f"Report saved to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to save report to {output_path}: {e}")
            raise
    
    def get_default_filename(
        self,
        video_path: str,
        format: ReportFormat,
        is_batch: bool = False
    ) -> str:
        """Generate default filename for report
        
        Args:
            video_path: Path to video (or first video for batch)
            format: Report format
            is_batch: Whether this is a batch report
            
        Returns:
            Default filename for the report
        """
        video_name = Path(video_path).stem
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        if is_batch:
            base_name = f"subtuner_batch_report_{timestamp}"
        else:
            base_name = f"{video_name}_subtuner_report_{timestamp}"
        
        extensions = {
            ReportFormat.CONSOLE: ".txt",
            ReportFormat.JSON: ".json",
            ReportFormat.CSV: ".csv",
            ReportFormat.MARKDOWN: ".md",
        }
        
        return base_name + extensions.get(format, ".txt")