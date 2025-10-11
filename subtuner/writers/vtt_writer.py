"""WebVTT subtitle writer"""

import logging
from typing import List

import webvtt

from .base import AbstractWriter
from ..errors import WritingError
from ..parsers.base import Subtitle

logger = logging.getLogger(__name__)


class VTTWriter(AbstractWriter):
    """Writer for WebVTT subtitle files"""
    
    @property
    def supported_extensions(self) -> List[str]:
        return ['.vtt', '.webvtt']
    
    @property
    def format_name(self) -> str:
        return "WebVTT"
    
    def write(
        self, 
        subtitles: List[Subtitle], 
        output_path: str,
        encoding: str = "utf-8"
    ) -> None:
        """Write subtitles to WebVTT file
        
        Args:
            subtitles: List of optimized subtitles
            output_path: Path to output WebVTT file
            encoding: Text encoding to use
            
        Raises:
            WritingError: If writing fails
        """
        try:
            logger.debug(f"Writing {len(subtitles)} subtitles to WebVTT: {output_path}")
            
            # Create WebVTT file
            vtt_file = webvtt.WebVTT()
            
            for subtitle in subtitles:
                caption = self._convert_to_vtt_caption(subtitle)
                if caption:
                    vtt_file.captions.append(caption)
            
            # Write to file
            vtt_file.save(output_path)
            
            logger.debug(f"Successfully wrote WebVTT file: {output_path}")
            
        except Exception as e:
            raise WritingError(f"Failed to write WebVTT file {output_path}: {e}") from e
    
    def _convert_to_vtt_caption(self, subtitle: Subtitle) -> webvtt.Caption:
        """Convert internal Subtitle to WebVTT Caption
        
        Args:
            subtitle: Internal subtitle object
            
        Returns:
            WebVTT Caption object
        """
        try:
            # Create new caption
            caption = webvtt.Caption()
            
            # Set timing
            caption.start = self._seconds_to_vtt_time(subtitle.start_time)
            caption.end = self._seconds_to_vtt_time(subtitle.end_time)
            
            # Use preserved original text if available, otherwise use current text
            if subtitle.metadata.get('format') == 'vtt' and 'original_text' in subtitle.metadata:
                # Preserve original WebVTT formatting and styling
                caption.text = subtitle.metadata['original_text']
            else:
                # Use current text (may need WebVTT formatting)
                caption.text = self._format_text_for_vtt(subtitle.text)
            
            # Preserve identifier if available
            if subtitle.metadata.get('identifier'):
                caption.identifier = subtitle.metadata['identifier']
            
            return caption
            
        except Exception as e:
            logger.warning(f"Failed to convert subtitle to WebVTT caption: {e}")
            # Create minimal valid caption
            caption = webvtt.Caption()
            caption.start = self._seconds_to_vtt_time(subtitle.start_time)
            caption.end = self._seconds_to_vtt_time(subtitle.end_time)
            caption.text = subtitle.text
            return caption
    
    def _seconds_to_vtt_time(self, seconds: float) -> str:
        """Convert seconds to WebVTT time string
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Time in WebVTT format "HH:MM:SS.mmm" or "MM:SS.mmm"
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"
        else:
            return f"{minutes:02d}:{secs:02d}.{milliseconds:03d}"
    
    def _format_text_for_vtt(self, text: str) -> str:
        """Format text for WebVTT output
        
        Args:
            text: Input text
            
        Returns:
            Text formatted for WebVTT
        """
        # WebVTT uses different line break conventions
        # Convert standard line breaks to WebVTT format if needed
        return text.replace('\n', '\n')  # Keep as-is for now
    
    def can_write(self, format_name: str) -> bool:
        """Check if this writer can handle the given format"""
        return format_name.lower() in ['vtt', 'webvtt']
    
    def write_with_metadata_preservation(
        self, 
        subtitles: List[Subtitle], 
        output_path: str,
        encoding: str = "utf-8"
    ) -> None:
        """Write WebVTT file with enhanced metadata preservation
        
        Args:
            subtitles: List of optimized subtitles
            output_path: Path to output WebVTT file
            encoding: Text encoding to use
        """
        try:
            logger.debug(f"Writing WebVTT with metadata preservation: {output_path}")
            
            lines = ['WEBVTT', '']  # Start with WebVTT header
            
            for subtitle in subtitles:
                # Add identifier if available
                if subtitle.metadata.get('identifier'):
                    lines.append(subtitle.metadata['identifier'])
                
                # Add timing line
                start_time = self._seconds_to_vtt_time(subtitle.start_time)
                end_time = self._seconds_to_vtt_time(subtitle.end_time)
                lines.append(f"{start_time} --> {end_time}")
                
                # Add text (preserve original if available)
                if (subtitle.metadata.get('format') == 'vtt' and 
                    'original_text' in subtitle.metadata):
                    text = subtitle.metadata['original_text']
                else:
                    text = self._format_text_for_vtt(subtitle.text)
                
                # Handle multi-line text
                lines.extend(text.split('\n'))
                
                # Add blank line between captions
                lines.append('')
            
            # Write to file
            content = '\n'.join(lines)
            with open(output_path, 'w', encoding=encoding) as f:
                f.write(content)
            
        except Exception as e:
            # Fallback to standard method
            logger.warning(f"Metadata preservation failed, using standard method: {e}")
            self.write(subtitles, output_path, encoding)
    
    def add_webvtt_styling(
        self, 
        subtitles: List[Subtitle], 
        output_path: str,
        style_css: str = None
    ) -> None:
        """Write WebVTT file with custom styling
        
        Args:
            subtitles: List of optimized subtitles
            output_path: Path to output WebVTT file
            style_css: Optional CSS styling for WebVTT
        """
        try:
            lines = ['WEBVTT']
            
            # Add styling if provided
            if style_css:
                lines.extend(['', 'STYLE', style_css, ''])
            else:
                lines.append('')
            
            for subtitle in subtitles:
                # Add identifier if available
                if subtitle.metadata.get('identifier'):
                    lines.append(subtitle.metadata['identifier'])
                
                # Add timing line with positioning/styling if available
                start_time = self._seconds_to_vtt_time(subtitle.start_time)
                end_time = self._seconds_to_vtt_time(subtitle.end_time)
                
                timing_line = f"{start_time} --> {end_time}"
                
                # Add WebVTT cue settings if available in metadata
                cue_settings = subtitle.metadata.get('cue_settings', '')
                if cue_settings:
                    timing_line += f" {cue_settings}"
                
                lines.append(timing_line)
                
                # Add text with preserved formatting
                text = subtitle.metadata.get('original_text', subtitle.text)
                lines.extend(text.split('\n'))
                lines.append('')
            
            # Write to file
            content = '\n'.join(lines)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
        except Exception as e:
            raise WritingError(f"Failed to write styled WebVTT file: {e}") from e
    
    def validate_vtt_content(self, subtitles: List[Subtitle]) -> List[str]:
        """Validate WebVTT content and return any warnings
        
        Args:
            subtitles: List of subtitles to validate
            
        Returns:
            List of validation warnings
        """
        warnings = []
        
        for i, subtitle in enumerate(subtitles):
            # Check for empty text
            if not subtitle.text.strip():
                warnings.append(f"Caption {i + 1}: Empty text")
            
            # Check for WebVTT-specific issues
            text = subtitle.text
            
            # Check for unclosed tags
            open_tags = text.count('<') - text.count('</')
            close_tags = text.count('>')  - text.count('/>')
            if open_tags != close_tags:
                warnings.append(f"Caption {i + 1}: Possible unclosed WebVTT tags")
            
            # Check for invalid time stamps in text
            if '<' in text and '>' in text:
                # Look for timestamp tags
                import re
                timestamp_pattern = r'<\d{2}:\d{2}:\d{2}\.\d{3}>'
                timestamps = re.findall(timestamp_pattern, text)
                for ts in timestamps:
                    # Extract timestamp and validate it's within caption duration
                    time_str = ts[1:-1]  # Remove < and >
                    try:
                        ts_seconds = self._vtt_time_to_seconds(time_str)
                        if not (subtitle.start_time <= ts_seconds <= subtitle.end_time):
                            warnings.append(f"Caption {i + 1}: Timestamp {ts} outside caption duration")
                    except:
                        warnings.append(f"Caption {i + 1}: Invalid timestamp format {ts}")
            
            # Check timing
            if subtitle.duration < 0.3:
                warnings.append(f"Caption {i + 1}: Very short duration ({subtitle.duration:.2f}s)")
        
        return warnings
    
    def _vtt_time_to_seconds(self, time_str: str) -> float:
        """Convert WebVTT time string to seconds (for validation)"""
        parts = time_str.split(':')
        if len(parts) == 2:
            # MM:SS.mmm
            minutes = int(parts[0])
            seconds_ms = parts[1].split('.')
            seconds = int(seconds_ms[0])
            milliseconds = int(seconds_ms[1]) if len(seconds_ms) > 1 else 0
            return minutes * 60 + seconds + milliseconds / 1000.0
        elif len(parts) == 3:
            # HH:MM:SS.mmm
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds_ms = parts[2].split('.')
            seconds = int(seconds_ms[0])
            milliseconds = int(seconds_ms[1]) if len(seconds_ms) > 1 else 0
            return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
        else:
            raise ValueError(f"Invalid WebVTT time format: {time_str}")