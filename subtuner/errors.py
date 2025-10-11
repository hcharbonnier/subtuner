"""Custom exceptions for SubTuner"""


class SubTunerError(Exception):
    """Base exception for all SubTuner errors"""
    pass


class VideoAnalysisError(SubTunerError):
    """Raised when video analysis fails"""
    pass


class SubtitleExtractionError(SubTunerError):
    """Raised when subtitle extraction fails"""
    pass


class ParsingError(SubTunerError):
    """Raised when subtitle parsing fails"""
    pass


class OptimizationError(SubTunerError):
    """Raised when optimization algorithms fail"""
    pass


class WritingError(SubTunerError):
    """Raised when writing optimized subtitles fails"""
    pass


class FFmpegError(SubTunerError):
    """Raised when FFmpeg/FFprobe operations fail"""
    pass


class ConfigurationError(SubTunerError):
    """Raised when configuration is invalid"""
    pass