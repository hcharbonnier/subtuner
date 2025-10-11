"""ASS/SSA subtitle parser"""

import logging
import os
import re
from typing import List, Optional, Any

import ass

from .base import AbstractParser, Subtitle
from ..errors import ParsingError

logger = logging.getLogger(__name__)


class ASSParser(AbstractParser):
    """Parser for ASS/SSA (Advanced SubStation Alpha) subtitle files"""
    
    @property
    def supported_extensions(self) -> List[str]:
        return ['.ass', '.ssa']
    
    @property
    def format_name(self) -> str:
        return "ASS (Advanced SubStation Alpha)"
    
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
            # ASS files should contain these sections
            return (
                '[Script Info]' in content or
                '[V4+ Styles]' in content or 
                '[V4 Styles]' in content or
                '[Events]' in content
            )
        except Exception:
            return False
    
    def parse(self, file_path: str, encoding: Optional[str] = None) -> List[Subtitle]:
        """Parse ASS/SSA file and return list of subtitles"""
        logger.info(f"Parsing ASS file: {os.path.basename(file_path)}")
        
        if not os.path.exists(file_path):
            raise ParsingError(f"ASS file not found: {file_path}")
        
        try:
            # Determine encoding
            if encoding is None:
                encoding = self.detect_encoding(file_path)
            
            logger.debug(f"Using encoding: {encoding}")
            
            # Parse with ass library
            with open(file_path, 'r', encoding=encoding) as f:
                doc = ass.parse(f)
            
            if not doc.events:
                raise ParsingError("No events found in ASS file")
            
            # Convert to internal format
            subtitles = []
            for i, event in enumerate(doc.events):
                try:
                    subtitle = self._convert_ass_event(event, i, doc)
                    if subtitle and subtitle.validate():
                        subtitles.append(subtitle)
                    else:
                        logger.warning(f"Skipping invalid event at index {i}")
                except Exception as e:
                    logger.warning(f"Failed to parse event at index {i}: {e}")
                    continue
            
            if not subtitles:
                raise ParsingError("No valid events found in ASS file")
            
            logger.info(f"Successfully parsed {len(subtitles)} events from ASS file")
            return subtitles
            
        except Exception as e:
            if "parsing" in str(e).lower():
                raise ParsingError(f"ASS parsing error: {e}")
            # Re-raise if not a parsing error
            raise
        except Exception as e:
            raise ParsingError(f"Failed to parse ASS file: {e}")
    
    def _convert_ass_event(self, event: Any, index: int, doc: Any) -> Optional[Subtitle]:
        """Convert ASS event to internal Subtitle format"""
        try:
            # Skip non-dialogue events (comments, etc.)
            if not hasattr(event, 'start') or not hasattr(event, 'end') or not hasattr(event, 'text'):
                return None
            
            # Check if this is a Dialogue event (not Comment)
            if event.__class__.__name__ != 'Dialogue':
                return None
            
            # Convert times to seconds (ASS uses centiseconds)
            start_time = event.start.total_seconds()
            end_time = event.end.total_seconds()
            
            # Get text content (remove ASS formatting tags)
            text = self._clean_ass_text(event.text)
            
            if not text:
                return None
            
            # Store original ASS data in metadata for writing back
            metadata = {
                'format': 'ass',
                'original_event': event,
                'original_text': event.text,
                'layer': event.layer,
                'style': event.style,
                'name': event.name,
                'margin_l': event.margin_l,
                'margin_r': event.margin_r,
                'margin_v': event.margin_v,
                'effect': event.effect,
                'document': doc,  # Keep reference to full document for styles
            }
            
            return Subtitle(
                index=index,
                start_time=start_time,
                end_time=end_time,
                text=text,
                metadata=metadata
            )
            
        except Exception as e:
            logger.warning(f"Failed to convert ASS event: {e}")
            return None
    
    def _clean_ass_text(self, text: str) -> str:
        """Clean ASS text by removing formatting tags but preserving content
        
        ASS uses override tags in the format {\tag} or {\tagvalue}
        
        Args:
            text: Raw ASS text with possible override tags
            
        Returns:
            Cleaned text suitable for character counting and display
        """
        if not text:
            return ""
        
        # Remove ASS override tags: {\tag}, {\tagvalue}, {\tag1\tag2}
        # Examples: {\i1}, {\b0}, {\c&Hffffff&}, {\pos(x,y)}, {\fad(500,500)}
        text = re.sub(r'\{[^}]*\}', '', text)
        
        # Remove line breaks (ASS uses \N for hard breaks, \n for soft breaks)
        text = text.replace('\\N', '\n').replace('\\n', ' ')
        
        # Remove other ASS escapes
        text = text.replace('\\h', ' ')  # Hard space
        
        # Clean up multiple spaces and newlines
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _ass_time_to_seconds(self, time_delta) -> float:
        """Convert ASS time (datetime.timedelta) to seconds"""
        return time_delta.total_seconds()
    
    def _seconds_to_ass_time(self, seconds: float):
        """Convert seconds to ASS time (datetime.timedelta)"""
        import datetime
        return datetime.timedelta(seconds=seconds)
    
    def _parse_time_seconds(self, time_str: str) -> float:
        """Parse ASS time string to seconds
        
        Args:
            time_str: Time in format "H:MM:SS.cc" (centiseconds)
            
        Returns:
            Time in seconds
        """
        try:
            # Parse format: "0:01:23.45" (H:MM:SS.cc)
            time_part, cs_part = time_str.split('.')
            h, m, s = map(int, time_part.split(':'))
            cs = int(cs_part)  # centiseconds
            
            return h * 3600 + m * 60 + s + cs / 100.0
            
        except Exception as e:
            raise ParsingError(f"Invalid ASS time format '{time_str}': {e}")
    
    def _format_time_seconds(self, seconds: float) -> str:
        """Format seconds to ASS time string
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Time in ASS format "H:MM:SS.cc"
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centiseconds = int((seconds % 1) * 100)
        
        return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"
    
    def get_styles(self, file_path: str, encoding: Optional[str] = None) -> dict:
        """Extract style information from ASS file
        
        This can be useful for preserving styling when writing back
        
        Args:
            file_path: Path to ASS file
            encoding: Text encoding
            
        Returns:
            Dictionary of style information
        """
        try:
            if encoding is None:
                encoding = self.detect_encoding(file_path)
            
            with open(file_path, 'r', encoding=encoding) as f:
                doc = ass.parse(f)
            
            styles = {}
            for style in doc.styles:
                styles[style.name] = {
                    'fontname': style.fontname,
                    'fontsize': style.fontsize,
                    'primary_color': style.primary_color,
                    'secondary_color': style.secondary_color,
                    'outline_color': style.outline_color,
                    'back_color': style.back_color,
                    'bold': style.bold,
                    'italic': style.italic,
                    'underline': style.underline,
                    'strikeout': style.strikeout,
                    'scale_x': style.scale_x,
                    'scale_y': style.scale_y,
                    'spacing': style.spacing,
                    'angle': style.angle,
                    'border_style': style.border_style,
                    'outline': style.outline,
                    'shadow': style.shadow,
                    'alignment': style.alignment,
                    'margin_l': style.margin_l,
                    'margin_r': style.margin_r,
                    'margin_v': style.margin_v,
                    'encoding': style.encoding,
                }
            
            return styles
            
        except Exception as e:
            logger.warning(f"Failed to extract styles from ASS file: {e}")
            return {}