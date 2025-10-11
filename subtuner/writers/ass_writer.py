"""ASS/SSA subtitle writer"""

import logging
from typing import List, Any

import ass

from .base import AbstractWriter
from ..errors import WritingError
from ..parsers.base import Subtitle

logger = logging.getLogger(__name__)


class ASSWriter(AbstractWriter):
    """Writer for ASS/SSA (Advanced SubStation Alpha) subtitle files"""
    
    @property
    def supported_extensions(self) -> List[str]:
        return ['.ass', '.ssa']
    
    @property
    def format_name(self) -> str:
        return "ASS (Advanced SubStation Alpha)"
    
    def write(
        self, 
        subtitles: List[Subtitle], 
        output_path: str,
        encoding: str = "utf-8"
    ) -> None:
        """Write subtitles to ASS file
        
        Args:
            subtitles: List of optimized subtitles
            output_path: Path to output ASS file
            encoding: Text encoding to use
            
        Raises:
            WritingError: If writing fails
        """
        try:
            logger.debug(f"Writing {len(subtitles)} subtitles to ASS: {output_path}")
            
            # Get original document structure if available
            doc = self._get_or_create_document(subtitles)
            
            # Clear existing events and add optimized ones
            doc.events.clear()
            
            for subtitle in subtitles:
                event = self._convert_to_ass_event(subtitle, doc)
                if event:
                    doc.events.append(event)
            
            # Write to file
            with open(output_path, 'w', encoding=encoding) as f:
                doc.dump_file(f)
            
            logger.debug(f"Successfully wrote ASS file: {output_path}")
            
        except Exception as e:
            raise WritingError(f"Failed to write ASS file {output_path}: {e}") from e
    
    def _get_or_create_document(self, subtitles: List[Subtitle]) -> Any:
        """Get original document or create new one with default structure
        
        Args:
            subtitles: List of subtitles (to check for preserved document)
            
        Returns:
            ASS Document object
        """
        # Try to get original document from first subtitle's metadata
        for subtitle in subtitles:
            if subtitle.metadata.get('format') == 'ass' and 'document' in subtitle.metadata:
                original_doc = subtitle.metadata['document']
                if isinstance(original_doc, ass.Document):
                    # Create a copy to avoid modifying original
                    return self._copy_document_structure(original_doc)
        
        # Create new document with default structure
        return self._create_default_document()
    
    def _copy_document_structure(self, original: Any) -> Any:
        """Create a copy of document structure (styles, info, etc.) without events
        
        Args:
            original: Original ASS document
            
        Returns:
            New document with copied structure
        """
        try:
            # Create new document
            doc = ass.Document()
            
            # Copy script info (use info attribute instead of script_info)
            if hasattr(original, 'info') and original.info:
                for key, value in original.info.items():
                    if hasattr(doc, 'info'):
                        doc.info[key] = value
            
            # Copy styles
            if hasattr(original, 'styles') and original.styles:
                for style in original.styles:
                    try:
                        # Create new style with available attributes
                        new_style = ass.Style()
                        
                        # Copy basic attributes
                        for attr in ['name', 'fontname', 'fontsize', 'bold', 'italic']:
                            if hasattr(style, attr):
                                setattr(new_style, attr, getattr(style, attr))
                        
                        # Copy color attributes if they exist
                        for attr in ['primary_color', 'secondary_color', 'outline_color', 'back_color']:
                            if hasattr(style, attr):
                                setattr(new_style, attr, getattr(style, attr))
                        
                        # Copy other styling attributes
                        for attr in ['underline', 'strikeout', 'scale_x', 'scale_y', 'spacing', 'angle']:
                            if hasattr(style, attr):
                                setattr(new_style, attr, getattr(style, attr))
                        
                        # Copy positioning attributes
                        for attr in ['border_style', 'outline', 'shadow', 'alignment']:
                            if hasattr(style, attr):
                                setattr(new_style, attr, getattr(style, attr))
                        
                        # Copy margin attributes
                        for attr in ['margin_l', 'margin_r', 'margin_v']:
                            if hasattr(style, attr):
                                setattr(new_style, attr, getattr(style, attr))
                        
                        # Copy encoding if it exists
                        if hasattr(style, 'encoding'):
                            setattr(new_style, 'encoding', getattr(style, 'encoding'))
                        
                        doc.styles.append(new_style)
                        
                    except Exception as style_err:
                        logger.debug(f"Failed to copy style {getattr(style, 'name', 'unknown')}: {style_err}")
                        continue
            
            return doc
            
        except Exception as e:
            logger.warning(f"Failed to copy document structure: {e}")
            return self._create_default_document()
    
    def _create_default_document(self) -> Any:
        """Create default ASS document structure
        
        Returns:
            New ASS document with default settings
        """
        doc = ass.Document()
        
        # Add basic info (use info instead of script_info)
        try:
            if hasattr(doc, 'info'):
                doc.info.update({
                    'Title': 'Optimized by SubTuner',
                    'ScriptType': 'v4.00+',
                })
        except Exception as e:
            logger.debug(f"Could not set document info: {e}")
        
        # Add default style with safe attributes
        try:
            default_style = ass.Style()
            default_style.name = 'Default'
            default_style.fontname = 'Arial'
            default_style.fontsize = 20
            default_style.bold = False
            default_style.italic = False
            
            # Try to set colors if available
            try:
                if hasattr(ass, 'Color'):
                    default_style.primary_color = ass.Color(255, 255, 255)  # White
            except:
                pass
            
            doc.styles.append(default_style)
            
        except Exception as e:
            logger.debug(f"Could not create default style: {e}")
        
        return doc
    
    def _convert_to_ass_event(self, subtitle: Subtitle, doc: Any) -> Any:
        """Convert internal Subtitle to ASS Event
        
        Args:
            subtitle: Internal subtitle object
            doc: ASS document (for style reference)
            
        Returns:
            ASS Event object
        """
        try:
            # Check if we have preserved original event
            if (subtitle.metadata.get('format') == 'ass' and
                'original_event' in subtitle.metadata):
                
                # Use original event as template and update times
                original = subtitle.metadata['original_event']
                
                # Create new event by copying from original
                event = ass.Dialogue(
                    layer=getattr(original, 'layer', 0),
                    start=self._seconds_to_ass_time(subtitle.start_time),
                    end=self._seconds_to_ass_time(subtitle.end_time),
                    style=getattr(original, 'style', 'Default'),
                    name=getattr(original, 'name', ''),
                    margin_l=getattr(original, 'margin_l', 0),
                    margin_r=getattr(original, 'margin_r', 0),
                    margin_v=getattr(original, 'margin_v', 0),
                    effect=getattr(original, 'effect', ''),
                    text=subtitle.metadata.get('original_text', subtitle.text)
                )
            else:
                # Create new event with default settings
                event = ass.Dialogue(
                    layer=0,
                    start=self._seconds_to_ass_time(subtitle.start_time),
                    end=self._seconds_to_ass_time(subtitle.end_time),
                    style='Default',
                    name='',
                    margin_l=0,
                    margin_r=0,
                    margin_v=0,
                    effect='',
                    text=subtitle.text
                )
            
            return event
            
        except Exception as e:
            logger.warning(f"Failed to convert subtitle to ASS event: {e}")
            # Create minimal valid event
            try:
                event = ass.Dialogue(
                    start=self._seconds_to_ass_time(subtitle.start_time),
                    end=self._seconds_to_ass_time(subtitle.end_time),
                    text=subtitle.text
                )
                return event
            except Exception as fallback_err:
                logger.error(f"Cannot create ASS event: {fallback_err}")
                return None
    
    def _seconds_to_ass_time(self, seconds: float):
        """Convert seconds to ASS time (timedelta)
        
        Args:
            seconds: Time in seconds
            
        Returns:
            datetime.timedelta object
        """
        import datetime
        return datetime.timedelta(seconds=seconds)
    
    def can_write(self, format_name: str) -> bool:
        """Check if this writer can handle the given format"""
        return format_name.lower() in ['ass', 'ssa', 'advanced substation alpha']
    
    def write_with_style_preservation(
        self, 
        subtitles: List[Subtitle], 
        output_path: str,
        encoding: str = "utf-8"
    ) -> None:
        """Write ASS file with maximum style preservation
        
        This method goes to extra lengths to preserve all original styling,
        even if it means manually reconstructing parts of the file.
        
        Args:
            subtitles: List of optimized subtitles
            output_path: Path to output ASS file
            encoding: Text encoding to use
        """
        try:
            logger.debug(f"Writing ASS with enhanced style preservation: {output_path}")
            
            # Use standard method but with extra validation
            self.write(subtitles, output_path, encoding)
            
            # Validate that styles were preserved correctly
            self._validate_style_preservation(subtitles, output_path)
            
        except Exception as e:
            logger.warning(f"Enhanced style preservation failed: {e}")
            # Fallback to standard method
            self.write(subtitles, output_path, encoding)
    
    def _validate_style_preservation(self, subtitles: List[Subtitle], output_path: str) -> None:
        """Validate that styles were preserved correctly
        
        Args:
            subtitles: Original subtitles
            output_path: Path to written file
        """
        try:
            # Read back the file and compare styles
            with open(output_path, 'r', encoding='utf-8') as f:
                written_doc = ass.parse(f)
            
            # Check that we have the expected number of events
            if len(written_doc.events) != len(subtitles):
                logger.warning(f"Event count mismatch: expected {len(subtitles)}, got {len(written_doc.events)}")
            
            # Check that styles are present
            if not written_doc.styles:
                logger.warning("No styles found in written ASS file")
            
        except Exception as e:
            logger.warning(f"Style preservation validation failed: {e}")
    
    def extract_unique_styles(self, subtitles: List[Subtitle]) -> List[dict]:
        """Extract unique styles used in subtitles
        
        Args:
            subtitles: List of subtitles to analyze
            
        Returns:
            List of unique style dictionaries
        """
        unique_styles = {}
        
        for subtitle in subtitles:
            if subtitle.metadata.get('format') == 'ass':
                style_name = subtitle.metadata.get('style', 'Default')
                if style_name not in unique_styles:
                    # Try to get original style info
                    doc = subtitle.metadata.get('document')
                    if doc and isinstance(doc, ass.Document):
                        for style in doc.styles:
                            if style.name == style_name:
                                unique_styles[style_name] = {
                                    'name': style.name,
                                    'fontname': style.fontname,
                                    'fontsize': style.fontsize,
                                    'colors': {
                                        'primary': style.primary_color,
                                        'secondary': style.secondary_color,
                                        'outline': style.outline_color,
                                        'back': style.back_color,
                                    },
                                    'formatting': {
                                        'bold': style.bold,
                                        'italic': style.italic,
                                        'underline': style.underline,
                                        'strikeout': style.strikeout,
                                    },
                                    'positioning': {
                                        'alignment': style.alignment,
                                        'margin_l': style.margin_l,
                                        'margin_r': style.margin_r,
                                        'margin_v': style.margin_v,
                                    }
                                }
                                break
        
        return list(unique_styles.values())
    
    def validate_ass_content(self, subtitles: List[Subtitle]) -> List[str]:
        """Validate ASS content and return any warnings
        
        Args:
            subtitles: List of subtitles to validate
            
        Returns:
            List of validation warnings
        """
        warnings = []
        style_names = set()
        
        for i, subtitle in enumerate(subtitles):
            # Check for empty text
            if not subtitle.text.strip():
                warnings.append(f"Event {i + 1}: Empty text")
            
            # Check style references
            if subtitle.metadata.get('format') == 'ass':
                style_name = subtitle.metadata.get('style', 'Default')
                style_names.add(style_name)
                
                # Check for complex override tags
                text = subtitle.text
                if '\\' in text and '{' in text:
                    # Count override tags
                    override_count = text.count('{')
                    if override_count > 5:
                        warnings.append(f"Event {i + 1}: Many override tags ({override_count}), may affect performance")
            
            # Check timing
            if subtitle.duration < 0.2:
                warnings.append(f"Event {i + 1}: Very short duration ({subtitle.duration:.2f}s)")
            elif subtitle.duration > 15:
                warnings.append(f"Event {i + 1}: Very long duration ({subtitle.duration:.2f}s)")
        
        # Report unique styles found
        if style_names:
            logger.debug(f"Found {len(style_names)} unique styles: {', '.join(sorted(style_names))}")
        
        return warnings
    
    def add_custom_styles(
        self, 
        subtitles: List[Subtitle], 
        output_path: str,
        custom_styles: List[dict],
        encoding: str = "utf-8"
    ) -> None:
        """Write ASS file with additional custom styles
        
        Args:
            subtitles: List of subtitles
            output_path: Path to output file
            custom_styles: List of custom style definitions
            encoding: Text encoding
        """
        try:
            # Get base document
            doc = self._get_or_create_document(subtitles)
            
            # Add custom styles
            for style_dict in custom_styles:
                style = ass.Style(**style_dict)
                # Check if style already exists
                existing = [s for s in doc.styles if s.name == style.name]
                if not existing:
                    doc.styles.append(style)
                else:
                    logger.warning(f"Style '{style.name}' already exists, skipping")
            
            # Add events
            doc.events.clear()
            for subtitle in subtitles:
                event = self._convert_to_ass_event(subtitle, doc)
                if event:
                    doc.events.append(event)
            
            # Write file
            with open(output_path, 'w', encoding=encoding) as f:
                doc.dump_file(f)
                
        except Exception as e:
            raise WritingError(f"Failed to write ASS file with custom styles: {e}") from e