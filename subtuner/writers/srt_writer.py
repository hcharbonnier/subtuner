"""SRT subtitle writer"""

import logging
from typing import List

import pysrt

from .base import AbstractWriter
from ..errors import WritingError
from ..parsers.base import Subtitle

logger = logging.getLogger(__name__)


class SRTWriter(AbstractWriter):
    """Writer for SRT (SubRip) subtitle files"""
    
    @property
    def supported_extensions(self) -> List[str]:
        return ['.srt']
    
    @property
    def format_name(self) -> str:
        return "SRT (SubRip)"
    
    def write(
        self, 
        subtitles: List[Subtitle], 
        output_path: str,
        encoding: str = "utf-8"
    ) -> None:
        """Write subtitles to SRT file
        
        Args:
            subtitles: List of optimized subtitles
            output_path: Path to output SRT file
            encoding: Text encoding to use
            
        Raises:
            WritingError: If writing fails
        """
        try:
            logger.debug(f"Writing {len(subtitles)} subtitles to SRT: {output_path}")
            
            # Create pysrt subtitle file
            srt_file = pysrt.SubRipFile()
            
            for i, subtitle in enumerate(subtitles):
                srt_item = self._convert_to_srt_item(subtitle, i + 1)
                if srt_item:
                    srt_file.append(srt_item)
            
            # Write to file
            srt_file.save(output_path, encoding=encoding)
            
            logger.debug(f"Successfully wrote SRT file: {output_path}")
            
        except Exception as e:
            raise WritingError(f"Failed to write SRT file {output_path}: {e}") from e
    
    def _convert_to_srt_item(self, subtitle: Subtitle, index: int) -> pysrt.SubRipItem:
        """Convert internal Subtitle to pysrt SubRipItem
        
        Args:
            subtitle: Internal subtitle object
            index: 1-based index for SRT
            
        Returns:
            pysrt SubRipItem
        """
        try:
            # Create new SRT item
            item = pysrt.SubRipItem()
            item.index = index
            
            # Convert times
            item.start = self._seconds_to_pysrt_time(subtitle.start_time)
            item.end = self._seconds_to_pysrt_time(subtitle.end_time)
            
            # Use preserved original text if available, otherwise use current text
            if subtitle.metadata.get('format') == 'srt' and 'original_text' in subtitle.metadata:
                # Preserve original formatting and styling
                item.text = subtitle.metadata['original_text']
            else:
                # Use current text (may have been processed)
                item.text = subtitle.text
            
            return item
            
        except Exception as e:
            logger.warning(f"Failed to convert subtitle {index} to SRT item: {e}")
            # Create minimal valid item
            item = pysrt.SubRipItem()
            item.index = index
            item.start = self._seconds_to_pysrt_time(subtitle.start_time)
            item.end = self._seconds_to_pysrt_time(subtitle.end_time)
            item.text = subtitle.text
            return item
    
    def _seconds_to_pysrt_time(self, seconds: float) -> pysrt.SubRipTime:
        """Convert seconds to pysrt time
        
        Args:
            seconds: Time in seconds
            
        Returns:
            pysrt SubRipTime object
        """
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
    
    def can_write(self, format_name: str) -> bool:
        """Check if this writer can handle the given format"""
        return format_name.lower() in ['srt', 'subrip']
    
    def write_with_metadata_preservation(
        self, 
        subtitles: List[Subtitle], 
        output_path: str,
        encoding: str = "utf-8"
    ) -> None:
        """Write SRT file with enhanced metadata preservation
        
        This method tries to preserve as much original formatting as possible
        while updating the timing information.
        
        Args:
            subtitles: List of optimized subtitles
            output_path: Path to output SRT file
            encoding: Text encoding to use
        """
        try:
            logger.debug(f"Writing SRT with metadata preservation: {output_path}")
            
            lines = []
            
            for i, subtitle in enumerate(subtitles):
                # Add subtitle index
                lines.append(str(i + 1))
                
                # Add timing line
                start_time = self._format_srt_time(subtitle.start_time)
                end_time = self._format_srt_time(subtitle.end_time)
                lines.append(f"{start_time} --> {end_time}")
                
                # Add text (preserve original if available)
                if (subtitle.metadata.get('format') == 'srt' and 
                    'original_text' in subtitle.metadata):
                    text = subtitle.metadata['original_text']
                else:
                    text = subtitle.text
                
                # Handle multi-line text
                lines.extend(text.split('\n'))
                
                # Add blank line between subtitles
                lines.append('')
            
            # Write to file
            content = '\n'.join(lines)
            with open(output_path, 'w', encoding=encoding) as f:
                f.write(content)
            
        except Exception as e:
            # Fallback to standard method
            logger.warning(f"Metadata preservation failed, using standard method: {e}")
            self.write(subtitles, output_path, encoding)
    
    def _format_srt_time(self, seconds: float) -> str:
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
    
    def validate_srt_content(self, subtitles: List[Subtitle]) -> List[str]:
        """Validate SRT content and return any warnings
        
        Args:
            subtitles: List of subtitles to validate
            
        Returns:
            List of validation warnings
        """
        warnings = []
        
        for i, subtitle in enumerate(subtitles):
            # Check for empty text
            if not subtitle.text.strip():
                warnings.append(f"Subtitle {i + 1}: Empty text")
            
            # Check for very long text
            if len(subtitle.text) > 200:
                warnings.append(f"Subtitle {i + 1}: Very long text ({len(subtitle.text)} chars)")
            
            # Check for timing issues
            if subtitle.duration < 0.5:
                warnings.append(f"Subtitle {i + 1}: Very short duration ({subtitle.duration:.2f}s)")
            elif subtitle.duration > 10:
                warnings.append(f"Subtitle {i + 1}: Very long duration ({subtitle.duration:.2f}s)")
            
            # Check for overlapping with next
            if i < len(subtitles) - 1:
                next_subtitle = subtitles[i + 1]
                if subtitle.end_time > next_subtitle.start_time:
                    overlap = subtitle.end_time - next_subtitle.start_time
                    warnings.append(f"Subtitles {i + 1}-{i + 2}: Overlap ({overlap:.2f}s)")
        
        return warnings