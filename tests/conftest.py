"""Pytest fixtures for SubTuner tests"""

import pytest
from typing import List

from subtuner.config import OptimizationConfig
from subtuner.parsers.base import Subtitle
from subtuner.optimization.statistics import OptimizationStatistics


@pytest.fixture
def default_config() -> OptimizationConfig:
    """Default optimization configuration for tests"""
    return OptimizationConfig()


@pytest.fixture
def strict_config() -> OptimizationConfig:
    """Strict optimization configuration for edge case tests"""
    return OptimizationConfig(
        chars_per_sec=15.0,
        max_duration=5.0,
        min_duration=1.5,
        min_gap=0.1,
        short_threshold=1.0,
        long_threshold=2.5,
        max_anticipation=0.3
    )


@pytest.fixture
def sample_subtitles() -> List[Subtitle]:
    """Sample subtitles for testing"""
    return [
        Subtitle(
            index=0,
            start_time=10.0,
            end_time=10.5,
            text="Hi!",
            metadata={'format': 'srt'}
        ),
        Subtitle(
            index=1,
            start_time=12.0,
            end_time=16.0,
            text="This is a much longer subtitle with more content to read.",
            metadata={'format': 'srt'}
        ),
        Subtitle(
            index=2,
            start_time=17.0,
            end_time=17.8,
            text="Quick",
            metadata={'format': 'srt'}
        ),
        Subtitle(
            index=3,
            start_time=20.0,
            end_time=22.5,
            text="Normal length subtitle",
            metadata={'format': 'srt'}
        ),
    ]


@pytest.fixture
def overlapping_subtitles() -> List[Subtitle]:
    """Subtitles with overlaps for validation testing"""
    return [
        Subtitle(
            index=0,
            start_time=10.0,
            end_time=12.0,
            text="First subtitle",
            metadata={'format': 'srt'}
        ),
        Subtitle(
            index=1,
            start_time=11.5,  # Overlaps with previous
            end_time=14.0,
            text="Second subtitle",
            metadata={'format': 'srt'}
        ),
        Subtitle(
            index=2,
            start_time=13.8,  # Too close to previous
            end_time=15.0,
            text="Third subtitle",
            metadata={'format': 'srt'}
        ),
    ]


@pytest.fixture
def invalid_subtitles() -> List[Subtitle]:
    """Invalid subtitles for validation testing"""
    return [
        Subtitle(
            index=0,
            start_time=10.0,
            end_time=10.1,  # Too short duration
            text="Too short",
            metadata={'format': 'srt'}
        ),
        Subtitle(
            index=1,
            start_time=15.0,
            end_time=14.0,  # Invalid: end before start
            text="Invalid times",
            metadata={'format': 'srt'}
        ),
        Subtitle(
            index=2,
            start_time=20.0,
            end_time=21.0,
            text="",  # Empty text
            metadata={'format': 'srt'}
        ),
    ]


@pytest.fixture
def dense_subtitles() -> List[Subtitle]:
    """Tightly packed subtitles for testing constraints"""
    return [
        Subtitle(
            index=0,
            start_time=0.0,
            end_time=1.0,
            text="First",
            metadata={'format': 'srt'}
        ),
        Subtitle(
            index=1,
            start_time=1.01,  # Very small gap
            end_time=2.0,
            text="Second",
            metadata={'format': 'srt'}
        ),
        Subtitle(
            index=2,
            start_time=2.02,
            end_time=3.0,
            text="Third",
            metadata={'format': 'srt'}
        ),
    ]


@pytest.fixture
def stats() -> OptimizationStatistics:
    """Fresh statistics object for testing"""
    return OptimizationStatistics()


@pytest.fixture
def single_subtitle() -> Subtitle:
    """Single subtitle for isolated testing"""
    return Subtitle(
        index=0,
        start_time=10.0,
        end_time=11.0,
        text="This is a test subtitle with some content.",
        metadata={'format': 'srt'}
    )


@pytest.fixture
def short_subtitle() -> Subtitle:
    """Very short subtitle"""
    return Subtitle(
        index=0,
        start_time=10.0,
        end_time=10.3,
        text="Hi",
        metadata={'format': 'srt'}
    )


@pytest.fixture
def long_subtitle() -> Subtitle:
    """Very long subtitle"""
    return Subtitle(
        index=0,
        start_time=10.0,
        end_time=15.0,
        text="This is a very long subtitle with lots of content that takes a while to read and should be considered long by the optimization algorithms when they evaluate it for potential rebalancing operations.",
        metadata={'format': 'srt'}
    )


@pytest.fixture
def first_subtitle() -> Subtitle:
    """First subtitle in sequence (no previous)"""
    return Subtitle(
        index=0,
        start_time=0.0,
        end_time=1.0,
        text="First subtitle",
        metadata={'format': 'srt'}
    )


@pytest.fixture
def last_subtitle() -> Subtitle:
    """Last subtitle in sequence (no next)"""
    return Subtitle(
        index=0,
        start_time=100.0,
        end_time=101.0,
        text="Last subtitle",
        metadata={'format': 'srt'}
    )


@pytest.fixture
def subtitle_pair() -> List[Subtitle]:
    """Pair of subtitles for rebalancing tests"""
    return [
        Subtitle(
            index=0,
            start_time=10.0,
            end_time=10.5,  # Short: 0.5s
            text="Short",
            metadata={'format': 'srt'}
        ),
        Subtitle(
            index=1,
            start_time=12.0,
            end_time=16.0,  # Long: 4.0s
            text="This is a much longer subtitle that has plenty of time available for reading and could spare some time for the previous short subtitle.",
            metadata={'format': 'srt'}
        ),
    ]


@pytest.fixture
def anticipation_candidate() -> List[Subtitle]:
    """Subtitles with anticipation potential"""
    return [
        Subtitle(
            index=0,
            start_time=10.0,
            end_time=11.0,
            text="Previous subtitle",
            metadata={'format': 'srt'}
        ),
        Subtitle(
            index=1,
            start_time=12.0,  # 1 second gap
            end_time=13.0,
            text="Can be anticipated",
            metadata={'format': 'srt'}
        ),
    ]


@pytest.fixture
def minimal_gap_subtitles() -> List[Subtitle]:
    """Subtitles with minimal gaps"""
    return [
        Subtitle(
            index=0,
            start_time=10.0,
            end_time=10.95,
            text="First",
            metadata={'format': 'srt'}
        ),
        Subtitle(
            index=1,
            start_time=11.0,  # Exactly min_gap (0.05s)
            end_time=12.0,
            text="Second",
            metadata={'format': 'srt'}
        ),
    ]