"""Subtitle extraction using FFmpeg"""

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from ..errors import FFmpegError, SubtitleExtractionError
from ..video.analyzer import SubtitleTrackInfo

logger = logging.getLogger(__name__)


class TempFileManager:
    """Context manager for temporary files"""
    
    def __init__(self, suffix: str = "", prefix: str = "subtuner_", dir: Optional[str] = None):
        """Initialize temporary file manager
        
        Args:
            suffix: File suffix (e.g., '.srt')
            prefix: File prefix
            dir: Directory for temporary files
        """
        self.suffix = suffix
        self.prefix = prefix
        self.dir = dir
        self.temp_file = None
        self.temp_path = None
    
    def __enter__(self) -> str:
        """Create temporary file and return path"""
        try:
            self.temp_file = tempfile.NamedTemporaryFile(
                suffix=self.suffix,
                prefix=self.prefix,
                dir=self.dir,
                delete=False
            )
            self.temp_path = self.temp_file.name
            self.temp_file.close()  # Close file handle but keep file
            logger.debug(f"Created temporary file: {self.temp_path}")
            return self.temp_path
        except Exception as e:
            raise SubtitleExtractionError(f"Failed to create temporary file: {e}")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up temporary file"""
        if self.temp_path and os.path.exists(self.temp_path):
            try:
                os.unlink(self.temp_path)
                logger.debug(f"Cleaned up temporary file: {self.temp_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file {self.temp_path}: {e}")


class SubtitleExtractor:
    """Extracts subtitle tracks from video files using FFmpeg"""
    
    def __init__(self, ffmpeg_path: Optional[str] = None, temp_dir: Optional[str] = None):
        """Initialize the subtitle extractor
        
        Args:
            ffmpeg_path: Custom path to ffmpeg binary
            temp_dir: Directory for temporary files
        """
        self.ffmpeg_path = self._find_ffmpeg(ffmpeg_path)
        self.temp_dir = temp_dir
        logger.debug(f"Using FFmpeg at: {self.ffmpeg_path}")
        if temp_dir:
            logger.debug(f"Using temp directory: {temp_dir}")
    
    def _find_ffmpeg(self, custom_path: Optional[str]) -> str:
        """Find ffmpeg binary"""
        if custom_path:
            if os.path.isfile(custom_path):
                return custom_path
            raise FFmpegError(f"Custom ffmpeg path not found: {custom_path}")
        
        # Try to find ffmpeg in PATH
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            return ffmpeg_path
        
        # Try common locations
        common_paths = [
            "/usr/bin/ffmpeg",
            "/usr/local/bin/ffmpeg",
            "C:\\Program Files\\FFmpeg\\bin\\ffmpeg.exe",
            "C:\\ffmpeg\\bin\\ffmpeg.exe",
        ]
        
        for path in common_paths:
            if os.path.isfile(path):
                return path
        
        raise FFmpegError(
            "FFmpeg not found. Please install FFmpeg or specify custom path."
        )
    
    def extract_track(
        self, 
        video_path: str, 
        track_info: SubtitleTrackInfo
    ) -> str:
        """Extract a subtitle track to a temporary file
        
        Args:
            video_path: Path to the video file
            track_info: Information about the subtitle track
            
        Returns:
            Path to the extracted subtitle file
            
        Raises:
            SubtitleExtractionError: If extraction fails
        """
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise SubtitleExtractionError(f"Video file not found: {video_path}")
        
        logger.info(
            f"Extracting subtitle track {track_info.index} "
            f"({track_info.codec}) from {video_path.name}"
        )
        
        # Determine output format
        output_format = self._get_output_format(track_info.codec)
        suffix = f".{track_info.format_extension}"
        # Create temporary file (without auto-cleanup)
        try:
            temp_file = tempfile.NamedTemporaryFile(
                suffix=suffix,
                prefix="subtuner_",
                dir=self.temp_dir,
                delete=False  # Don't auto-delete
            )
            temp_path = temp_file.name
            temp_file.close()  # Close file handle but keep file
            logger.debug(f"Created temporary file: {temp_path}")
            
            # Build FFmpeg command
            cmd = self._build_extraction_command(
                str(video_path),
                track_info.index,
                temp_path,
                output_format
            )
            
            logger.debug(f"Running extraction command: {' '.join(cmd)}")
            
            # Execute FFmpeg
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=300  # 5 minute timeout
            )
            
            # Verify extraction was successful
            if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                # Clean up failed file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise SubtitleExtractionError(
                    f"Extraction produced no output for track {track_info.index}"
                )
            
            logger.info(
                f"Successfully extracted track {track_info.index} "
                f"to {temp_path} ({os.path.getsize(temp_path)} bytes)"
            )
            
            # Return path to extracted file (caller is responsible for cleanup)
            return temp_path
            
        except subprocess.TimeoutExpired:
            # Clean up temp file on error
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.unlink(temp_path)
            raise SubtitleExtractionError(
                f"FFmpeg timed out while extracting track {track_info.index}"
            )
        except subprocess.CalledProcessError as e:
            # Clean up temp file on error
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.unlink(temp_path)
            error_msg = e.stderr.strip() if e.stderr else "Unknown error"
            raise SubtitleExtractionError(
                f"FFmpeg failed to extract track {track_info.index}: {error_msg}"
            )
        except Exception as e:
            # Clean up temp file on error
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.unlink(temp_path)
            raise SubtitleExtractionError(
                f"Unexpected error extracting track {track_info.index}: {e}"
            )
    
    def _build_extraction_command(
        self, 
        video_path: str, 
        track_index: int, 
        output_path: str,
        output_format: Optional[str] = None
    ) -> list[str]:
        """Build FFmpeg command for subtitle extraction"""
        cmd = [
            self.ffmpeg_path,
            "-y",  # Overwrite output files
            "-v", "error",  # Only show errors
            "-i", video_path,
            "-map", f"0:{track_index}",  # Map specific stream by absolute index
        ]
        
        # Add codec specification if needed
        if output_format:
            cmd.extend(["-c:s", output_format])
        else:
            cmd.extend(["-c:s", "copy"])  # Copy without re-encoding
        
        cmd.append(output_path)
        
        return cmd
    
    def _get_output_format(self, input_codec: str) -> Optional[str]:
        """Get appropriate output format for subtitle codec
        
        Args:
            input_codec: Input subtitle codec name
            
        Returns:
            Output codec name for FFmpeg, or None to copy
        """
        # Map codecs that need conversion
        codec_mapping = {
            'mov_text': 'srt',  # Convert QuickTime text to SRT
            'text': 'srt',      # Convert generic text to SRT
        }
        
        return codec_mapping.get(input_codec.lower())
    
    def extract_all_tracks(
        self, 
        video_path: str, 
        tracks: list[SubtitleTrackInfo]
    ) -> list[tuple[SubtitleTrackInfo, str]]:
        """Extract all subtitle tracks from a video
        
        Args:
            video_path: Path to the video file
            tracks: List of subtitle track information
            
        Returns:
            List of (track_info, temp_file_path) tuples
            
        Raises:
            SubtitleExtractionError: If any extraction fails
        """
        if not tracks:
            logger.info("No subtitle tracks to extract")
            return []
        
        logger.info(f"Extracting {len(tracks)} subtitle tracks from {Path(video_path).name}")
        
        extracted_tracks = []
        failed_tracks = []
        
        for track_info in tracks:
            try:
                temp_path = self.extract_track(video_path, track_info)
                extracted_tracks.append((track_info, temp_path))
            except SubtitleExtractionError as e:
                logger.error(f"Failed to extract track {track_info.index}: {e}")
                failed_tracks.append((track_info.index, str(e)))
                # Continue with other tracks rather than failing completely
        
        if failed_tracks and not extracted_tracks:
            # All tracks failed
            error_details = "; ".join([f"Track {idx}: {err}" for idx, err in failed_tracks])
            raise SubtitleExtractionError(f"Failed to extract any tracks: {error_details}")
        
        if failed_tracks:
            logger.warning(f"Successfully extracted {len(extracted_tracks)} tracks, "
                         f"{len(failed_tracks)} failed")
        else:
            logger.info(f"Successfully extracted all {len(extracted_tracks)} tracks")
        
        return extracted_tracks
    
    def cleanup_temp_files(self, temp_paths: list[str]) -> None:
        """Clean up temporary files
        
        Args:
            temp_paths: List of temporary file paths to clean up
        """
        for temp_path in temp_paths:
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                    logger.debug(f"Cleaned up temporary file: {temp_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up {temp_path}: {e}")