"""Video analysis using FFprobe"""

import json
import logging
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from ..errors import FFmpegError, VideoAnalysisError

logger = logging.getLogger(__name__)


@dataclass
class SubtitleTrackInfo:
    """Information about a subtitle track in a video file"""
    
    index: int
    codec: str
    language: Optional[str] = None
    title: Optional[str] = None
    default: bool = False
    forced: bool = False
    
    @property
    def is_text_based(self) -> bool:
        """Check if subtitle track contains text-based subtitles"""
        text_codecs = {
            'subrip', 'srt', 'ass', 'ssa', 'webvtt', 'vtt', 
            'mov_text', 'text', 'subviewer', 'microdvd'
        }
        return self.codec.lower() in text_codecs
    
    @property
    def format_extension(self) -> str:
        """Get the appropriate file extension for this subtitle format"""
        codec_mapping = {
            'subrip': 'srt',
            'srt': 'srt',
            'ass': 'ass',
            'ssa': 'ass',
            'webvtt': 'vtt',
            'vtt': 'vtt',
            'mov_text': 'srt',  # Convert to SRT
            'text': 'srt',     # Convert to SRT
        }
        return codec_mapping.get(self.codec.lower(), 'srt')


class VideoAnalyzer:
    """Analyzes video files using FFprobe"""
    
    def __init__(self, ffprobe_path: Optional[str] = None):
        """Initialize the video analyzer
        
        Args:
            ffprobe_path: Custom path to ffprobe binary
        """
        self.ffprobe_path = self._find_ffprobe(ffprobe_path)
        logger.debug(f"Using FFprobe at: {self.ffprobe_path}")
    
    def _find_ffprobe(self, custom_path: Optional[str]) -> str:
        """Find ffprobe binary"""
        if custom_path:
            if os.path.isfile(custom_path):
                return custom_path
            raise FFmpegError(f"Custom ffprobe path not found: {custom_path}")
        
        # Try to find ffprobe in PATH
        ffprobe_path = shutil.which("ffprobe")
        if ffprobe_path:
            return ffprobe_path
        
        # Try common locations
        common_paths = [
            "/usr/bin/ffprobe",
            "/usr/local/bin/ffprobe",
            "C:\\Program Files\\FFmpeg\\bin\\ffprobe.exe",
            "C:\\ffmpeg\\bin\\ffprobe.exe",
        ]
        
        for path in common_paths:
            if os.path.isfile(path):
                return path
        
        raise FFmpegError(
            "FFprobe not found. Please install FFmpeg or specify custom path."
        )
    
    def analyze_video(self, video_path: str) -> List[SubtitleTrackInfo]:
        """Analyze video file and return subtitle track information
        
        Args:
            video_path: Path to video file
            
        Returns:
            List of subtitle track information
            
        Raises:
            VideoAnalysisError: If analysis fails
            FFmpegError: If FFprobe execution fails
        """
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise VideoAnalysisError(f"Video file not found: {video_path}")
        
        if not video_path.is_file():
            raise VideoAnalysisError(f"Path is not a file: {video_path}")
        
        logger.info(f"Analyzing video: {video_path}")
        
        try:
            # Run ffprobe to get stream information
            cmd = [
                self.ffprobe_path,
                "-v", "quiet",
                "-print_format", "json",
                "-show_streams",
                "-select_streams", "s",  # Select subtitle streams only
                str(video_path)
            ]
            
            logger.debug(f"Running command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=30  # 30 second timeout
            )
            
            # Parse JSON output
            data = json.loads(result.stdout)
            streams = data.get("streams", [])
            
            # Extract subtitle track information
            subtitle_tracks = []
            for stream in streams:
                if stream.get("codec_type") == "subtitle":
                    track_info = self._parse_subtitle_stream(stream)
                    if track_info and track_info.is_text_based:
                        subtitle_tracks.append(track_info)
                        logger.debug(f"Found text subtitle track: {track_info}")
            
            logger.info(f"Found {len(subtitle_tracks)} text-based subtitle tracks")
            return subtitle_tracks
            
        except subprocess.TimeoutExpired:
            raise FFmpegError("FFprobe timed out while analyzing video")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else "Unknown error"
            raise FFmpegError(f"FFprobe failed: {error_msg}")
        except json.JSONDecodeError as e:
            raise FFmpegError(f"Failed to parse FFprobe output: {e}")
        except Exception as e:
            raise VideoAnalysisError(f"Unexpected error during analysis: {e}")
    
    def _parse_subtitle_stream(self, stream: dict) -> Optional[SubtitleTrackInfo]:
        """Parse subtitle stream information from FFprobe output"""
        try:
            index = stream.get("index")
            codec = stream.get("codec_name", "unknown")
            
            if index is None:
                logger.warning("Subtitle stream missing index, skipping")
                return None
            
            # Extract metadata
            tags = stream.get("tags", {})
            disposition = stream.get("disposition", {})
            
            # Language (try different tag keys)
            language = None
            for lang_key in ["language", "lang"]:
                if lang_key in tags:
                    language = tags[lang_key]
                    break
            
            # Title
            title = tags.get("title")
            
            # Flags
            default = disposition.get("default", 0) == 1
            forced = disposition.get("forced", 0) == 1
            
            return SubtitleTrackInfo(
                index=index,
                codec=codec,
                language=language,
                title=title,
                default=default,
                forced=forced
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse subtitle stream: {e}")
            return None
    
    def validate_video_file(self, video_path: str) -> bool:
        """Validate that the file is a valid video file
        
        Args:
            video_path: Path to video file
            
        Returns:
            True if valid, False otherwise
        """
        try:
            video_path = Path(video_path)
            
            if not video_path.exists() or not video_path.is_file():
                return False
            
            # Quick validation with ffprobe
            cmd = [
                self.ffprobe_path,
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=codec_type",
                "-of", "csv=p=0",
                str(video_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return result.returncode == 0 and "video" in result.stdout
            
        except Exception as e:
            logger.debug(f"Video validation failed: {e}")
            return False
    
    def get_video_duration(self, video_path: str) -> Optional[float]:
        """Get video duration in seconds
        
        Args:
            video_path: Path to video file
            
        Returns:
            Duration in seconds, or None if unknown
        """
        try:
            cmd = [
                self.ffprobe_path,
                "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                str(video_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            
            duration_str = result.stdout.strip()
            if duration_str and duration_str != "N/A":
                return float(duration_str)
            
        except Exception as e:
            logger.debug(f"Could not get video duration: {e}")
        
        return None