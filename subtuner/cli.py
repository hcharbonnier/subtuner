"""Command-line interface for SubTuner"""

import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

import click

from .config import GlobalConfig, OptimizationConfig, ProcessingConfig
from .errors import SubTunerError
from .extraction.extractor import SubtitleExtractor
from .optimization.engine import OptimizationEngine
from .parsers.base import get_parser_for_file
from .statistics.reporter import StatisticsReporter, ReportFormat
from .video.analyzer import VideoAnalyzer
from .writers.base import get_writer_for_format


# Configure logging
def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """Set up logging configuration"""
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Reduce verbosity of third-party libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)


@click.command()
@click.argument('video_paths', nargs=-1, required=True, type=click.Path(exists=True, file_okay=True, dir_okay=True))
@click.option(
    '--chars-per-sec', 
    default=20.0, 
    type=click.FloatRange(10.0, 40.0),
    help='Reading speed in characters per second (10-40)'
)
@click.option(
    '--max-duration', 
    default=8.0, 
    type=click.FloatRange(3.0, 15.0),
    help='Maximum subtitle duration in seconds (3-15)'
)
@click.option(
    '--min-duration', 
    default=1.0, 
    type=click.FloatRange(0.5, 2.0),
    help='Minimum subtitle duration in seconds (0.5-2)'
)
@click.option(
    '--min-gap', 
    default=0.05, 
    type=click.FloatRange(0.01, 0.2),
    help='Minimum gap between subtitles in seconds (0.01-0.2)'
)
@click.option(
    '--max-anticipation', 
    default=0.5, 
    type=click.FloatRange(0.0, 1.0),
    help='Maximum anticipatory offset in seconds (0-1)'
)
@click.option(
    '--short-threshold', 
    default=0.8, 
    type=click.FloatRange(0.5, 1.5),
    help='Threshold for "short" subtitle in seconds (0.5-1.5)'
)
@click.option(
    '--long-threshold', 
    default=3.0, 
    type=click.FloatRange(2.0, 6.0),
    help='Threshold for "long" subtitle in seconds (2-6)'
)
@click.option(
    '--output-dir',
    type=click.Path(),
    help='Output directory for optimized subtitles (default: same as input)'
)
@click.option(
    '--output-label',
    default='fixed',
    type=str,
    help='Label to add to optimized subtitle filenames (default: "fixed")'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Preview changes without writing files'
)
@click.option(
    '--verbose', 
    is_flag=True,
    help='Enable verbose output'
)
@click.option(
    '--quiet', 
    is_flag=True,
    help='Suppress all output except errors'
)
@click.option(
    '--report-format',
    type=click.Choice(['console', 'json', 'markdown', 'csv']),
    default='console',
    help='Report output format'
)
@click.option(
    '--save-report',
    type=click.Path(),
    help='Save detailed report to file'
)
@click.version_option(version="0.1.0", prog_name="SubTuner")
def main(
    video_paths: tuple,
    chars_per_sec: float,
    max_duration: float,
    min_duration: float,
    min_gap: float,
    max_anticipation: float,
    short_threshold: float,
    long_threshold: float,
    output_dir: Optional[str],
    output_label: str,
    dry_run: bool,
    verbose: bool,
    quiet: bool,
    report_format: str,
    save_report: Optional[str]
) -> None:
    """SubTuner - Optimize embedded video subtitles for better readability.
    
    SubTuner extracts subtitle tracks from video files and applies intelligent
    optimization algorithms to improve reading experience while preserving
    semantic structure.
    
    Examples:
    
        # Optimize a single video
        subtuner movie.mkv
        
        # Batch process multiple videos
        subtuner movie1.mkv movie2.mp4 series/*.mkv
        
        # Custom reading speed for slower readers
        subtuner movie.mkv --chars-per-sec 15
        
        # Preview changes without writing files
        subtuner movie.mkv --dry-run
        
        # Save detailed report
        subtuner movie.mkv --save-report report.json --report-format json
    """
    try:
        # Set up logging
        setup_logging(verbose, quiet)
        logger = logging.getLogger(__name__)
        
        if not quiet:
            click.echo("🎬 SubTuner - Subtitle Optimization Tool")
            click.echo("=" * 50)
        
        # Create configuration
        config = GlobalConfig.from_args(
            chars_per_sec=chars_per_sec,
            max_duration=max_duration,
            min_duration=min_duration,
            min_gap=min_gap,
            max_anticipation=max_anticipation,
            short_threshold=short_threshold,
            long_threshold=long_threshold,
            output_dir=output_dir,
            output_label=output_label,
            dry_run=dry_run,
            verbose=verbose,
            quiet=quiet
        )
        
        # Initialize CLI processor
        cli = SubTunerCLI(config)
        
        # Convert tuple to list and expand directories
        video_list = cli.expand_video_paths(list(video_paths))
        
        if not video_list:
            if not quiet:
                click.echo("❌ No video files found to process")
            sys.exit(1)
        
        # Process videos
        if len(video_list) == 1:
            # Single video processing
            results = cli.process_single_video(video_list[0])
        else:
            # Batch processing
            results = cli.process_batch_videos(video_list)
        
        # Generate and display reports
        report_fmt = ReportFormat(report_format)
        cli.generate_reports(results, report_fmt, save_report)
        
        if not quiet:
            click.echo("\n✅ SubTuner processing complete!")
        
    except SubTunerError as e:
        if not quiet:
            click.echo(f"\n❌ SubTuner error: {e}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        if not quiet:
            click.echo("\n⚠️  Processing interrupted by user", err=True)
        sys.exit(130)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.exception("Unexpected error occurred")
        if not quiet:
            click.echo(f"\n💥 Unexpected error: {e}", err=True)
        sys.exit(1)


class SubTunerCLI:
    """Main CLI processor that coordinates all SubTuner operations"""
    
    def __init__(self, config: GlobalConfig):
        """Initialize CLI processor
        
        Args:
            config: Global configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.video_analyzer = VideoAnalyzer()
        self.extractor = SubtitleExtractor(temp_dir=config.processing.temp_dir)
        self.optimizer = OptimizationEngine()
        self.reporter = StatisticsReporter()
        
        self.logger.debug("SubTuner CLI initialized")
    
    def expand_video_paths(self, paths: List[str]) -> List[str]:
        """Expand directory paths to video files with confirmation
        
        Args:
            paths: List of file or directory paths
            
        Returns:
            Expanded list of video file paths
        """
        video_extensions = {'.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
        expanded = []
        
        for path in paths:
            path_obj = Path(path)
            
            if path_obj.is_file():
                # Add file directly
                expanded.append(str(path_obj))
                
            elif path_obj.is_dir():
                # Find all video files in directory
                video_files = []
                for ext in video_extensions:
                    video_files.extend(path_obj.glob(f'*{ext}'))
                    video_files.extend(path_obj.glob(f'*{ext.upper()}'))
                
                if video_files:
                    # Sort files for consistent ordering
                    video_files = sorted(set(str(f) for f in video_files))
                    
                    if not self.config.processing.quiet:
                        click.echo(f"\n📁 Found {len(video_files)} video file(s) in {path}:")
                        for i, vf in enumerate(video_files[:10], 1):  # Show first 10
                            click.echo(f"  {i}. {Path(vf).name}")
                        if len(video_files) > 10:
                            click.echo(f"  ... and {len(video_files) - 10} more")
                        
                        # Ask for confirmation
                        if click.confirm(f"\n⚠️  Process all {len(video_files)} video(s)?", default=True):
                            expanded.extend(video_files)
                        else:
                            click.echo("Skipping directory")
                    else:
                        # In quiet mode, process without confirmation
                        expanded.extend(video_files)
                else:
                    if not self.config.processing.quiet:
                        click.echo(f"⚠️  No video files found in {path}")
            else:
                self.logger.warning(f"Path not found: {path}")
        
        return expanded
    
    def process_single_video(self, video_path: str) -> dict:
        """Process a single video file
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with processing results
        """
        self.logger.info(f"Processing single video: {Path(video_path).name}")
        
        if not self.config.processing.quiet:
            click.echo(f"\n📹 Processing: {Path(video_path).name}")
        
        try:
            # Analyze video for subtitle tracks
            if not self.config.processing.quiet:
                click.echo("🔍 Analyzing video for subtitle tracks...")
            
            tracks = self.video_analyzer.analyze_video(video_path)
            
            if not tracks:
                if not self.config.processing.quiet:
                    click.echo("⚠️  No text-based subtitle tracks found")
                return {'video_path': video_path, 'tracks': [], 'status': 'no_tracks'}
            
            if not self.config.processing.quiet:
                click.echo(f"📝 Found {len(tracks)} subtitle track(s)")
            
            # Process each track
            track_results = []
            
            for i, track_info in enumerate(tracks):
                if not self.config.processing.quiet:
                    lang_info = f" ({track_info.language})" if track_info.language else ""
                    click.echo(f"⚙️  Processing track {track_info.index} [{track_info.codec}{lang_info}]...")
                
                result = self._process_single_track(video_path, track_info)
                track_results.append(result)
            
            return {
                'video_path': video_path,
                'tracks': track_results,
                'status': 'success'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to process {video_path}: {e}")
            return {
                'video_path': video_path,
                'tracks': [],
                'status': 'error',
                'error': str(e)
            }
    
    def process_batch_videos(self, video_paths: List[str]) -> dict:
        """Process multiple video files
        
        Args:
            video_paths: List of video file paths
            
        Returns:
            Dictionary with batch processing results
        """
        self.logger.info(f"Processing batch of {len(video_paths)} videos")
        
        if not self.config.processing.quiet:
            click.echo(f"\n📦 Batch processing {len(video_paths)} videos")
        
        self.reporter.start_session()
        
        batch_results = {}
        successful = 0
        failed = 0
        
        for i, video_path in enumerate(video_paths, 1):
            if not self.config.processing.quiet:
                click.echo(f"\n[{i}/{len(video_paths)}] {Path(video_path).name}")
            
            try:
                result = self.process_single_video(video_path)
                batch_results[video_path] = result.get('tracks', [])
                
                if result['status'] == 'success':
                    successful += 1
                else:
                    failed += 1
                    
            except Exception as e:
                self.logger.error(f"Failed to process {video_path}: {e}")
                batch_results[video_path] = []
                failed += 1
        
        self.reporter.end_session()
        
        if not self.config.processing.quiet:
            click.echo(f"\n📊 Batch complete: {successful} successful, {failed} failed")
        
        return {
            'type': 'batch',
            'results': batch_results,
            'summary': {
                'total': len(video_paths),
                'successful': successful,
                'failed': failed
            }
        }
    
    def _process_single_track(self, video_path: str, track_info) -> dict:
        """Process a single subtitle track
        
        Args:
            video_path: Path to video file
            track_info: Subtitle track information
            
        Returns:
            Dictionary with track processing results
        """
        try:
            # Extract subtitle track
            temp_file = self.extractor.extract_track(video_path, track_info)
            
            try:
                # Parse subtitles
                parser = get_parser_for_file(temp_file)
                if not parser:
                    raise SubTunerError(f"No parser available for track {track_info.index}")
                
                subtitles = parser.parse(temp_file)
                
                if not subtitles:
                    return {
                        'track_index': track_info.index,
                        'status': 'empty',
                        'original_count': 0,
                        'optimized_count': 0
                    }
                
                # Optimize subtitles
                optimization_result = self.optimizer.optimize(
                    subtitles, 
                    self.config.optimization,
                    track_info.index
                )
                
                # Write optimized subtitles (unless dry run)
                output_path = None
                if not self.config.processing.dry_run:
                    writer = get_writer_for_format(track_info.codec)
                    if not writer:
                        raise SubTunerError(f"No writer available for format {track_info.codec}")
                    
                    output_path = writer.get_output_path(
                        video_path,
                        track_info.index,
                        self.config.processing.output_dir,
                        language=track_info.language,
                        label=self.config.processing.output_label
                    )
                    
                    writer.write_safely(optimization_result.subtitles, output_path)
                    
                    if not self.config.processing.quiet:
                        click.echo(f"💾 Saved: {Path(output_path).name}")
                
                return {
                    'track_index': track_info.index,
                    'track_info': track_info,
                    'statistics': optimization_result.statistics,
                    'output_path': output_path,
                    'status': 'success',
                    'original_count': len(subtitles),
                    'optimized_count': len(optimization_result.subtitles)
                }
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file):
                    try:
                        os.unlink(temp_file)
                    except Exception as e:
                        self.logger.warning(f"Failed to clean up temp file {temp_file}: {e}")
                
        except Exception as e:
            self.logger.error(f"Failed to process track {track_info.index}: {e}")
            return {
                'track_index': track_info.index,
                'status': 'error',
                'error': str(e)
            }
    
    def generate_reports(
        self, 
        results: dict,
        report_format: ReportFormat,
        save_path: Optional[str] = None
    ) -> None:
        """Generate and display processing reports
        
        Args:
            results: Processing results
            report_format: Report format to generate
            save_path: Optional path to save report
        """
        try:
            if results.get('type') == 'batch':
                # Batch report
                # Convert results format for reporter
                batch_stats = {}
                for video_path, track_results in results['results'].items():
                    track_stats = []
                    for track_result in track_results:
                        if 'statistics' in track_result:
                            track_stats.append(track_result['statistics'])
                    if track_stats:
                        batch_stats[video_path] = track_stats
                
                if batch_stats:
                    report_content = self.reporter.generate_batch_report(
                        batch_stats, report_format
                    )
                    
                    if not self.config.processing.quiet and report_format == ReportFormat.CONSOLE:
                        click.echo("\n" + report_content)
                    
                    if save_path:
                        self.reporter.save_report(report_content, save_path, report_format)
                        if not self.config.processing.quiet:
                            click.echo(f"📄 Report saved: {save_path}")
            
            else:
                # Single video report
                video_path = results['video_path']
                track_results = results.get('tracks', [])
                
                # Extract statistics
                track_stats = []
                for track_result in track_results:
                    if 'statistics' in track_result and track_result.get('status') == 'success':
                        track_stats.append(track_result['statistics'])
                
                if track_stats:
                    if len(track_stats) == 1:
                        report_content = self.reporter.generate_single_track_report(
                            video_path, track_stats[0], report_format
                        )
                    else:
                        report_content = self.reporter.generate_multi_track_report(
                            video_path, track_stats, report_format
                        )
                    
                    if not self.config.processing.quiet and report_format == ReportFormat.CONSOLE:
                        click.echo("\n" + report_content)
                    
                    if save_path:
                        self.reporter.save_report(report_content, save_path, report_format)
                        if not self.config.processing.quiet:
                            click.echo(f"📄 Report saved: {save_path}")
        
        except Exception as e:
            self.logger.error(f"Failed to generate report: {e}")
            if not self.config.processing.quiet:
                click.echo(f"⚠️  Failed to generate report: {e}", err=True)


if __name__ == "__main__":
    main()