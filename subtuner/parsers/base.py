"""Base classes for subtitle parsers"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Subtitle:
    """Internal representation of a subtitle entry"""
    
    index: int
    start_time: float  # seconds
    end_time: float    # seconds
    text: str
    metadata: Dict[str, Any]  # Format-specific data
    
    @property
    def duration(self) -> float:
        """Get subtitle duration in seconds"""
        return self.end_time - self.start_time
    
    @property
    def char_count(self) -> int:
        """Get character count (excluding formatting)"""
        # Remove common HTML/formatting tags for character counting
        import re
        clean_text = re.sub(r'<[^>]*>', '', self.text)
        clean_text = re.sub(r'\{[^}]*\}', '', clean_text)  # ASS formatting
        return len(clean_text.strip())
    
    def with_start_time(self, start_time: float) -> "Subtitle":
        """Create a copy with new start time"""
        return Subtitle(
            index=self.index,
            start_time=start_time,
            end_time=self.end_time,
            text=self.text,
            metadata=self.metadata.copy()
        )
    
    def with_end_time(self, end_time: float) -> "Subtitle":
        """Create a copy with new end time"""
        return Subtitle(
            index=self.index,
            start_time=self.start_time,
            end_time=end_time,
            text=self.text,
            metadata=self.metadata.copy()
        )
    
    def with_times(self, start_time: float, end_time: float) -> "Subtitle":
        """Create a copy with new start and end times"""
        return Subtitle(
            index=self.index,
            start_time=start_time,
            end_time=end_time,
            text=self.text,
            metadata=self.metadata.copy()
        )
    
    def validate(self) -> bool:
        """Validate subtitle entry"""
        if self.start_time < 0:
            return False
        if self.end_time <= self.start_time:
            return False
        if not self.text or not self.text.strip():
            return False
        return True


class AbstractParser(ABC):
    """Abstract base class for subtitle parsers"""
    
    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """Get list of supported file extensions"""
        pass
    
    @property
    @abstractmethod
    def format_name(self) -> str:
        """Get human-readable format name"""
        pass
    
    @abstractmethod
    def parse(self, file_path: str, encoding: Optional[str] = None) -> List[Subtitle]:
        """Parse subtitle file and return list of subtitles
        
        Args:
            file_path: Path to subtitle file
            encoding: Text encoding (auto-detect if None)
            
        Returns:
            List of parsed subtitles
            
        Raises:
            ParsingError: If parsing fails
        """
        pass
    
    @abstractmethod
    def can_parse(self, file_path: str) -> bool:
        """Check if this parser can handle the given file
        
        Args:
            file_path: Path to subtitle file
            
        Returns:
            True if parser can handle this file
        """
        pass
    
    def detect_encoding(self, file_path: str) -> str:
        """Detect file encoding
        
        Args:
            file_path: Path to subtitle file
            
        Returns:
            Detected encoding name
        """
        import chardet
        
        try:
            with open(file_path, 'rb') as f:
                # Read first 32KB for detection
                raw_data = f.read(32768)
                
            if not raw_data:
                return 'utf-8'  # Default for empty files
            
            result = chardet.detect(raw_data)
            encoding = result.get('encoding', 'utf-8')
            confidence = result.get('confidence', 0.0)
            
            # Use UTF-8 if confidence is too low
            if confidence < 0.7:
                encoding = 'utf-8'
            
            # Handle common encoding issues
            if encoding and encoding.lower() in ['ascii']:
                encoding = 'utf-8'
            
            return encoding or 'utf-8'
            
        except Exception:
            # Fallback to UTF-8
            return 'utf-8'
    
    def read_file(self, file_path: str, encoding: Optional[str] = None) -> str:
        """Read subtitle file with proper encoding handling
        
        Args:
            file_path: Path to subtitle file
            encoding: Text encoding (auto-detect if None)
            
        Returns:
            File content as string
            
        Raises:
            ParsingError: If file cannot be read
        """
        from ..errors import ParsingError
        
        if encoding is None:
            encoding = self.detect_encoding(file_path)
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            return content
            
        except UnicodeDecodeError:
            # Try with different encodings
            fallback_encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
            
            for fallback in fallback_encodings:
                if fallback == encoding:
                    continue
                try:
                    with open(file_path, 'r', encoding=fallback) as f:
                        content = f.read()
                    return content
                except UnicodeDecodeError:
                    continue
            
            raise ParsingError(f"Could not decode file with any encoding: {file_path}")
            
        except Exception as e:
            raise ParsingError(f"Failed to read file {file_path}: {e}")
    
    def _parse_time_seconds(self, time_str: str) -> float:
        """Parse time string and return seconds
        
        This is a helper method that subclasses can use or override
        for format-specific time parsing.
        
        Args:
            time_str: Time string (format varies by subtitle type)
            
        Returns:
            Time in seconds as float
        """
        # This will be overridden by specific parsers
        raise NotImplementedError("Subclasses must implement time parsing")
    
    def _format_time_seconds(self, seconds: float) -> str:
        """Format seconds back to format-specific time string
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted time string
        """
        # This will be overridden by specific parsers
        raise NotImplementedError("Subclasses must implement time formatting")


def get_parser_for_file(file_path: str) -> Optional[AbstractParser]:
    """Get appropriate parser for a subtitle file
    
    Args:
        file_path: Path to subtitle file
        
    Returns:
        Parser instance, or None if no parser can handle the file
    """
    import logging
    logger = logging.getLogger(__name__)
    
    from .srt_parser import SRTParser
    from .vtt_parser import VTTParser
    from .ass_parser import ASSParser
    
    parsers = [SRTParser(), VTTParser(), ASSParser()]
    
    logger.debug(f"Trying to find parser for file: {file_path}")
    
    for parser in parsers:
        logger.debug(f"Testing {parser.__class__.__name__}")
        if parser.can_parse(file_path):
            logger.debug(f"Selected parser: {parser.__class__.__name__}")
            return parser
        else:
            logger.debug(f"{parser.__class__.__name__} cannot parse this file")
    
    logger.warning(f"No parser found for file: {file_path}")
    return None