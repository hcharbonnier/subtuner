"""Base classes for subtitle writers"""

import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from ..errors import WritingError
from ..parsers.base import Subtitle

logger = logging.getLogger(__name__)


class AbstractWriter(ABC):
    """Abstract base class for subtitle writers"""
    
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
    def write(
        self, 
        subtitles: List[Subtitle], 
        output_path: str,
        encoding: str = "utf-8"
    ) -> None:
        """Write subtitles to file
        
        Args:
            subtitles: List of subtitles to write
            output_path: Path to output file
            encoding: Text encoding to use
            
        Raises:
            WritingError: If writing fails
        """
        pass
    
    def can_write(self, format_name: str) -> bool:
        """Check if this writer can handle the given format
        
        Args:
            format_name: Format name from subtitle metadata
            
        Returns:
            True if writer can handle this format
        """
        return format_name.lower() in [ext.lower() for ext in self.supported_extensions]
    
    def ensure_output_directory(self, output_path: str) -> None:
        """Ensure output directory exists
        
        Args:
            output_path: Path to output file
            
        Raises:
            WritingError: If directory cannot be created
        """
        try:
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise WritingError(f"Failed to create output directory: {e}")
    
    def validate_subtitles(self, subtitles: List[Subtitle]) -> None:
        """Validate subtitles before writing
        
        Args:
            subtitles: List of subtitles to validate
            
        Raises:
            WritingError: If subtitles are invalid
        """
        if not subtitles:
            raise WritingError("No subtitles to write")
        
        for i, subtitle in enumerate(subtitles):
            if not subtitle.validate():
                raise WritingError(f"Invalid subtitle at index {i}")
    
    def write_safely(
        self, 
        subtitles: List[Subtitle], 
        output_path: str,
        encoding: str = "utf-8"
    ) -> None:
        """Write subtitles with error handling and logging
        
        Args:
            subtitles: List of subtitles to write
            output_path: Path to output file
            encoding: Text encoding to use
        """
        logger.info(f"Writing {len(subtitles)} subtitles to {output_path}")
        
        try:
            # Validate inputs
            self.validate_subtitles(subtitles)
            self.ensure_output_directory(output_path)
            
            # Write subtitles
            self.write(subtitles, output_path, encoding)
            
            # Verify output
            if not os.path.exists(output_path):
                raise WritingError(f"Output file was not created: {output_path}")
            
            file_size = os.path.getsize(output_path)
            logger.info(f"Successfully wrote {output_path} ({file_size} bytes)")
            
        except Exception as e:
            if isinstance(e, WritingError):
                raise
            raise WritingError(f"Failed to write {output_path}: {e}") from e
    
    def get_output_path(
        self,
        video_path: str,
        track_index: int,
        output_dir: Optional[str] = None,
        language: Optional[str] = None,
        label: Optional[str] = None
    ) -> str:
        """Generate output path for subtitle file
        
        Args:
            video_path: Original video file path
            track_index: Subtitle track index
            output_dir: Output directory (default: same as video)
            language: Language code (e.g., 'eng', 'fra')
            label: Optional label to add to filename (e.g., 'fixed')
            
        Returns:
            Output file path
        """
        video_path = Path(video_path)
        base_name = video_path.stem
        extension = self.supported_extensions[0]  # Use primary extension
        
        if output_dir:
            output_directory = Path(output_dir)
        else:
            output_directory = video_path.parent
        
        # Build filename with optional components
        parts = [base_name, str(track_index)]
        
        if language:
            parts.append(language)
        
        if label:
            parts.append(label)
        
        output_filename = ".".join(parts) + extension
        
        return str(output_directory / output_filename)
    
    def backup_existing_file(self, file_path: str) -> Optional[str]:
        """Create backup of existing file
        
        Args:
            file_path: Path to file to backup
            
        Returns:
            Path to backup file, or None if no backup needed
        """
        if not os.path.exists(file_path):
            return None
        
        backup_path = f"{file_path}.backup"
        counter = 1
        
        # Find unique backup filename
        while os.path.exists(backup_path):
            backup_path = f"{file_path}.backup.{counter}"
            counter += 1
        
        try:
            import shutil
            shutil.copy2(file_path, backup_path)
            logger.debug(f"Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            logger.warning(f"Failed to create backup of {file_path}: {e}")
            return None


def get_writer_for_format(format_name: str) -> Optional[AbstractWriter]:
    """Get appropriate writer for a subtitle format
    
    Args:
        format_name: Format name (e.g., 'srt', 'vtt', 'ass')
        
    Returns:
        Writer instance, or None if no writer can handle the format
    """
    from .srt_writer import SRTWriter
    from .vtt_writer import VTTWriter
    from .ass_writer import ASSWriter
    
    writers = [SRTWriter(), VTTWriter(), ASSWriter()]
    
    for writer in writers:
        if writer.can_write(format_name):
            return writer
    
    return None


def get_writer_for_extension(extension: str) -> Optional[AbstractWriter]:
    """Get appropriate writer for a file extension
    
    Args:
        extension: File extension (e.g., '.srt', '.vtt', '.ass')
        
    Returns:
        Writer instance, or None if no writer can handle the extension
    """
    from .srt_writer import SRTWriter
    from .vtt_writer import VTTWriter
    from .ass_writer import ASSWriter
    
    writers = [SRTWriter(), VTTWriter(), ASSWriter()]
    
    # Normalize extension
    if not extension.startswith('.'):
        extension = f'.{extension}'
    
    for writer in writers:
        if extension.lower() in [ext.lower() for ext in writer.supported_extensions]:
            return writer
    
    return None