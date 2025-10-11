"""WebVTT subtitle parser"""

import logging
import os
import re
from typing import List, Optional

import webvtt

from .base import AbstractParser, Subtitle
from ..errors import ParsingError

logger = logging.getLogger(__name__)


class VTTParser(AbstractParser):
    """Parser for WebVTT subtitle files"""
    
    @property
    def supported_extensions(self) -> List[str]:
        return ['.vtt', '.webvtt']
    
    @property
    def format_name(self) -> str:
        return "WebVTT"
    
    def can_parse(self, file_path: str) -> bool:
        """Check if this parser can handle the given file"""
        # Check extension
        if not any(file_path.lower().endswith(ext) for ext in self.supported_extensions):
            return False
        
        # Check if file exists
        if not os.path.exists(file_path):
            return False
        
        # Try to peek at content structure
        try:
            content = self.read_file(file_path)
            # WebVTT files should start with "WEBVTT" or have timestamp arrows
            return (
                content.startswith('WEBVTT') or
                '-->' in content[:1000]
            )
        except Exception:
            return False
    
    def parse(self, file_path: str, encoding: Optional[str] = None) -> List[Subtitle]:
        """Parse WebVTT file and return list of subtitles"""
        logger.info(f"Parsing WebVTT file: {os.path.basename(file_path)}")
        
        if not os.path.exists(file_path):
            raise ParsingError(f"WebVTT file not found: {file_path}")
        
        try:
            # Parse with webvtt-py library
            vtt_file = webvtt.read(file_path)
            
            if not vtt_file:
                raise ParsingError("No captions found in WebVTT file")
            
            # Convert to internal format
            subtitles = []
            for i, caption in enumerate(vtt_file):
                try:
                    subtitle = self._convert_vtt_caption(caption, i)
                    if subtitle and subtitle.validate():
                        subtitles.append(subtitle)
                    else:
                        logger.warning(f"Skipping invalid caption at index {i}")
                except Exception as e:
                    logger.warning(f"Failed to parse caption at index {i}: {e}")
                    continue
            
            if not subtitles:
                raise ParsingError("No valid captions found in WebVTT file")
            
            logger.info(f"Successfully parsed {len(subtitles)} captions from WebVTT file")
            return subtitles
            
        except webvtt.errors.MalformedFileError as e:
            raise ParsingError(f"Malformed WebVTT file: {e}")
        except Exception as e:
            raise ParsingError(f"Failed to parse WebVTT file: {e}")
    
    def _convert_vtt_caption(self, caption: webvtt.Caption, index: int) -> Optional[Subtitle]:
        """Convert WebVTT caption to internal Subtitle format"""
        try:
            # Convert times to seconds
            start_time = self._vtt_time_to_seconds(caption.start)
            end_time = self._vtt_time_to_seconds(caption.end)
            
            # Get text content (remove VTT formatting tags)
            text = self._clean_vtt_text(caption.text)
            
            if not text:
                return None
            
            # Store original WebVTT data in metadata for writing back
            metadata = {
                'format': 'vtt',
                'original_start': caption.start,
                'original_end': caption.end,
                'original_text': caption.text,
                'identifier': getattr(caption, 'identifier', None),
            }
            
            # Store WebVTT-specific styling and positioning
            if hasattr(caption, 'style'):
                metadata['style'] = caption.style
            
            return Subtitle(
                index=index,
                start_time=start_time,
                end_time=end_time,
                text=text,
                metadata=metadata
            )
            
        except Exception as e:
            logger.warning(f"Failed to convert WebVTT caption at {caption.start}: {e}")
            return None
    
    def _vtt_time_to_seconds(self, time_str: str) -> float:
        """Convert WebVTT time string to seconds
        
        Args:
            time_str: Time in format "MM:SS.mmm" or "HH:MM:SS.mmm"
            
        Returns:
            Time in seconds
        """
        try:
            # Handle both formats: "MM:SS.mmm" and "HH:MM:SS.mmm"
            parts = time_str.split(':')
            
            if len(parts) == 2:
                # Format: "MM:SS.mmm"
                minutes = int(parts[0])
                seconds_ms = parts[1].split('.')
                seconds = int(seconds_ms[0])
                milliseconds = int(seconds_ms[1]) if len(seconds_ms) > 1 else 0
                
                return minutes * 60 + seconds + milliseconds / 1000.0
                
            elif len(parts) == 3:
                # Format: "HH:MM:SS.mmm"
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds_ms = parts[2].split('.')
                seconds = int(seconds_ms[0])
                milliseconds = int(seconds_ms[1]) if len(seconds_ms) > 1 else 0
                
                return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
            
            else:
                raise ValueError(f"Invalid time format: {time_str}")
                
        except Exception as e:
            raise ParsingError(f"Invalid WebVTT time format '{time_str}': {e}")
    
    def _seconds_to_vtt_time(self, seconds: float) -> str:
        """Convert seconds to WebVTT time string
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Time in WebVTT format "HH:MM:SS.mmm"
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"
        else:
            return f"{minutes:02d}:{secs:02d}.{milliseconds:03d}"
    
    def _clean_vtt_text(self, text: str) -> str:
        """Clean WebVTT text by removing formatting tags but preserving content
        
        Args:
            text: Raw WebVTT text with possible tags
            
        Returns:
            Cleaned text suitable for character counting and display
        """
        if not text:
            return ""
        
        # Remove WebVTT styling tags but keep the content
        # Examples: <c.red>text</c>, <v Speaker>text</v>, <i>text</i>
        
        # Remove voice tags: <v Speaker>text</v> -> text
        text = re.sub(r'<v[^>]*>', '', text)
        text = re.sub(r'</v>', '', text)
        
        # Remove class tags: <c.classname>text</c> -> text
        text = re.sub(r'<c[^>]*>', '', text)
        text = re.sub(r'</c>', '', text)
        
        # Keep basic formatting but remove tags for counting
        # <i>, <b>, <u> tags - remove tags but keep content
        text = re.sub(r'<(/?)([ibuIBU])>', r'', text)
        
        # Remove timestamp tags: <00:01:30.000>
        text = re.sub(r'<\d{2}:\d{2}:\d{2}\.\d{3}>', '', text)
        
        # Clean up multiple spaces and newlines
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _parse_time_seconds(self, time_str: str) -> float:
        """Parse WebVTT time string to seconds"""
        return self._vtt_time_to_seconds(time_str)
    
    def _format_time_seconds(self, seconds: float) -> str:
        """Format seconds to WebVTT time string"""
        return self._seconds_to_vtt_time(seconds)