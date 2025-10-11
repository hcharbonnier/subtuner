"""Configuration classes for SubTuner"""

from dataclasses import dataclass
from typing import Optional

from .errors import ConfigurationError


@dataclass
class OptimizationConfig:
    """Configuration for optimization algorithms"""
    
    # Reading speed
    chars_per_sec: float = 20.0
    
    # Duration constraints
    max_duration: float = 8.0
    min_duration: float = 1.0
    
    # Timing constraints
    min_gap: float = 0.05
    
    # Rebalancing thresholds
    short_threshold: float = 0.8
    long_threshold: float = 3.0
    
    # Anticipation
    max_anticipation: float = 0.5
    
    def __post_init__(self):
        """Validate configuration parameters"""
        self.validate()
    
    def validate(self) -> None:
        """Validate all configuration parameters"""
        errors = []
        
        # Validate reading speed
        if not 10.0 <= self.chars_per_sec <= 40.0:
            errors.append("chars_per_sec must be between 10 and 40")
        
        # Validate duration constraints
        if not 3.0 <= self.max_duration <= 15.0:
            errors.append("max_duration must be between 3 and 15 seconds")
        
        if not 0.5 <= self.min_duration <= 2.0:
            errors.append("min_duration must be between 0.5 and 2 seconds")
        
        if self.min_duration >= self.max_duration:
            errors.append("min_duration must be less than max_duration")
        
        # Validate timing constraints
        if not 0.01 <= self.min_gap <= 0.2:
            errors.append("min_gap must be between 0.01 and 0.2 seconds")
        
        # Validate rebalancing thresholds
        if not 0.5 <= self.short_threshold <= 1.5:
            errors.append("short_threshold must be between 0.5 and 1.5 seconds")
        
        if not 2.0 <= self.long_threshold <= 6.0:
            errors.append("long_threshold must be between 2 and 6 seconds")
        
        if self.short_threshold >= self.long_threshold:
            errors.append("short_threshold must be less than long_threshold")
        
        # Validate anticipation
        if not 0.0 <= self.max_anticipation <= 1.0:
            errors.append("max_anticipation must be between 0 and 1 second")
        
        if errors:
            raise ConfigurationError("Invalid configuration: " + "; ".join(errors))


@dataclass
class ProcessingConfig:
    """Configuration for processing workflow"""
    
    # Output settings
    output_dir: Optional[str] = None
    output_label: str = "fixed"  # Label to add to optimized subtitle files
    dry_run: bool = False
    
    # Processing settings
    batch: bool = False
    verbose: bool = False
    quiet: bool = False
    
    # FFmpeg settings
    ffmpeg_path: Optional[str] = None
    ffprobe_path: Optional[str] = None
    temp_dir: Optional[str] = None
    
    def __post_init__(self):
        """Validate processing configuration"""
        if self.verbose and self.quiet:
            raise ConfigurationError("Cannot be both verbose and quiet")


@dataclass
class GlobalConfig:
    """Global configuration combining all settings"""
    
    optimization: OptimizationConfig
    processing: ProcessingConfig
    
    @classmethod
    def create_default(cls) -> "GlobalConfig":
        """Create default configuration"""
        return cls(
            optimization=OptimizationConfig(),
            processing=ProcessingConfig()
        )
    
    @classmethod
    def from_args(cls, **kwargs) -> "GlobalConfig":
        """Create configuration from CLI arguments"""
        # Separate optimization and processing arguments
        optimization_args = {}
        processing_args = {}
        
        optimization_fields = {
            'chars_per_sec', 'max_duration', 'min_duration', 'min_gap',
            'short_threshold', 'long_threshold', 'max_anticipation'
        }
        
        for key, value in kwargs.items():
            if value is not None:  # Only set non-None values
                if key in optimization_fields:
                    optimization_args[key] = value
                else:
                    processing_args[key] = value
        
        return cls(
            optimization=OptimizationConfig(**optimization_args),
            processing=ProcessingConfig(**processing_args)
        )