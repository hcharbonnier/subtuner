"""SRT subtitle parser"""

import logging
import os
from typing import List, Optional

import pysrt

from .base import AbstractParser, Subtitle
from ..errors import ParsingError

logger = logging.getLogger(__name__)


class SRTParser(AbstractParser):
    """Parser for SRT (SubRip) subtitle files"""
    
    @property
    def supported_extensions(self) -> List[str]:
        return ['.srt']
    
    @property
    def format_name(self) -> str:
        return "SRT (SubRip)"
    
    def can_parse(self, file_path: str) -> bool:
        """Check if this parser can handle the given file"""
        # Check extension
        if not file_path.lower().endswith('.srt'):
            return False
        
        # Check if file exists
        if not os.path.exists(file_path):
            return False
        
        # Try to peek at content structure
        try:
            content = self.read_file(file_path)
            # Simple heuristic: look for time patterns
            return '-->' in content and any(
                char.isdigit() for char in content[:1000]
            )
        except Exception:
            return False
    
    def parse(self, file_path: str, encoding: Optional[str] = None) -> List[Subtitle]:
        """Parse SRT file and return list of subtitles"""
        logger.info(f"Parsing SRT file: {os.path.basename(file_path)}")
        
        if not os.path.exists(file_path):
            raise ParsingError(f"SRT file not found: {file_path}")
        
        try:
            # Determine encoding
            if encoding is None:
                encoding = self.detect_encoding(file_path)
            
            logger.debug(f"Using encoding: {encoding}")
            
            # Parse with pysrt
            srt_file = pysrt.open(file_path, encoding=encoding)
            
            if not srt_file:
                raise ParsingError("No subtitles found in SRT file")
            
            # Convert to internal format
            subtitles = []
            for i, item in enumerate(srt_file):
                try:
                    subtitle = self._convert_srt_item(item, i)
                    if subtitle and subtitle.validate():
                        subtitles.append(subtitle)
                    else:
                        logger.warning(f"Skipping invalid subtitle at index {i}")
                except Exception as e:
                    logger.warning(f"Failed to parse subtitle at index {i}: {e}")
                    continue
            
            if not subtitles:
                raise ParsingError("No valid subtitles found in SRT file")
            
            logger.info(f"Successfully parsed {len(subtitles)} subtitles from SRT file")
            return subtitles
            
        except pysrt.Error as e:
            raise ParsingError(f"pysrt parsing error: {e}")
        except Exception as e:
            raise ParsingError(f"Failed to parse SRT file: {e}")
    
    def _convert_srt_item(self, item: pysrt.SubRipItem, index: int) -> Optional[Subtitle]:
        """Convert pysrt item to internal Subtitle format"""
        try:
            # Convert times to seconds
            start_time = self._pysrt_time_to_seconds(item.start)
            end_time = self._pysrt_time_to_seconds(item.end)
            
            # Get text content
            text = item.text.strip()
            
            if not text:
                return None
            
            # Store original pysrt data in metadata for writing back
            metadata = {
                'format': 'srt',
                'original_index': item.index,
                'original_start': item.start,
                'original_end': item.end,
                'original_text': item.text,
            }
            
            return Subtitle(
                index=index,
                start_time=start_time,
                end_time=end_time,
                text=text,
                metadata=metadata
            )
            
        except Exception as e:
            logger.warning(f"Failed to convert SRT item {item.index}: {e}")
            return None
    
    def _pysrt_time_to_seconds(self, pysrt_time: pysrt.SubRipTime) -> float:
        """Convert pysrt time to seconds"""
        return (
            pysrt_time.hours * 3600 +
            pysrt_time.minutes * 60 +
            pysrt_time.seconds +
            pysrt_time.milliseconds / 1000.0
        )
    
    def _seconds_to_pysrt_time(self, seconds: float) -> pysrt.SubRipTime:
        """Convert seconds to pysrt time"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        
        return pysrt.SubRipTime(
            hours=hours,
            minutes=minutes,
            seconds=secs,
            milliseconds=milliseconds
        )
    
    def _parse_time_seconds(self, time_str: str) -> float:
        """Parse SRT time string to seconds
        
        Args:
            time_str: Time in format "HH:MM:SS,mmm"
            
        Returns:
            Time in seconds
        """
        try:
            # Parse format: "00:01:23,456"
            time_part, ms_part = time_str.split(',')
            h, m, s = map(int, time_part.split(':'))
            ms = int(ms_part)
            
            return h * 3600 + m * 60 + s + ms / 1000.0
            
        except Exception as e:
            raise ParsingError(f"Invalid SRT time format '{time_str}': {e}")
    
    def _format_time_seconds(self, seconds: float) -> str:
        """Format seconds to SRT time string
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Time in SRT format "HH:MM:SS,mmm"
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"