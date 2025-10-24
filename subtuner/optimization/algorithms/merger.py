"""Subtitle merger algorithm for overlapping and identical subtitles"""

import logging
from typing import List

from ...config import OptimizationConfig
from ...parsers.base import Subtitle
from ..statistics import OptimizationStatistics

logger = logging.getLogger(__name__)


class SubtitleMerger:
    """Algorithm 0: Merge overlapping and identical subtitles (pre-processing)"""
    
    def __init__(self):
        self.name = "Subtitle Merger"
    
    def process(
        self,
        subtitles: List[Subtitle],
        config: OptimizationConfig,
        stats: OptimizationStatistics
    ) -> List[Subtitle]:
        """Merge overlapping and identical subtitles
        
        Args:
            subtitles: List of subtitles to process
            config: Optimization configuration
            stats: Statistics tracker
            
        Returns:
            List of subtitles with duplicates and overlaps merged
        """
        if not subtitles or not config.merge_duplicates:
            return subtitles
        
        logger.debug(f"Starting subtitle merging for {len(subtitles)} subtitles")
        
        merged = []
        i = 0
        
        while i < len(subtitles):
            current = subtitles[i]
            
            # Look ahead for mergeable subtitles
            merge_candidates = [current]
            j = i + 1
            
            while j < len(subtitles):
                next_sub = subtitles[j]
                
                # Check if we should merge with current group
                if self._should_merge(merge_candidates[-1], next_sub):
                    merge_candidates.append(next_sub)
                    j += 1
                else:
                    break
            
            # Merge the candidates if we found any
            if len(merge_candidates) > 1:
                merged_subtitle = self._merge_subtitles(merge_candidates)
                merged.append(merged_subtitle)
                stats.merged_subtitles += len(merge_candidates) - 1
                logger.debug(
                    f"Merged {len(merge_candidates)} subtitles at index {i}: "
                    f"'{merge_candidates[0].text[:30]}...' + {len(merge_candidates)-1} more"
                )
            else:
                merged.append(current)
            
            i = j
        
        logger.info(
            f"Subtitle merging complete: {len(subtitles)} → {len(merged)} subtitles "
            f"({stats.merged_subtitles} merged)"
        )
        
        return merged
    
    def _should_merge(self, current: Subtitle, next_sub: Subtitle) -> bool:
        """Determine if two subtitles should be merged
        
        Args:
            current: Current subtitle
            next_sub: Next subtitle to consider
            
        Returns:
            True if subtitles should be merged
        """
        # Check for identical text (case-insensitive, whitespace-normalized)
        current_text = self._normalize_text(current.text)
        next_text = self._normalize_text(next_sub.text)
        
        if current_text == next_text and current_text:
            # Identical text - merge if they overlap or are very close
            gap = next_sub.start_time - current.end_time
            if gap <= 0.5:  # Overlap or very small gap
                logger.debug(f"Found identical text with gap {gap:.3f}s")
                return True
        
        # Check for overlapping subtitles with similar or complementary text
        if current.end_time > next_sub.start_time:
            # They overlap - check if text is similar or complementary
            overlap_duration = current.end_time - next_sub.start_time
            
            # If significant overlap (>50% of shorter subtitle)
            min_duration = min(current.duration, next_sub.duration)
            if overlap_duration > min_duration * 0.5:
                # Check if one text contains the other (continuation)
                if (current_text in next_text or next_text in current_text or
                    self._is_continuation(current_text, next_text)):
                    logger.debug(
                        f"Found overlapping subtitles with continuation "
                        f"(overlap: {overlap_duration:.3f}s)"
                    )
                    return True
        
        return False
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        import re
        
        # Remove HTML/formatting tags
        clean = re.sub(r'<[^>]*>', '', text)
        clean = re.sub(r'\{[^}]*\}', '', clean)
        
        # Normalize whitespace
        clean = ' '.join(clean.split())
        
        # Convert to lowercase for comparison
        return clean.lower().strip()
    
    def _is_continuation(self, text1: str, text2: str) -> bool:
        """Check if text2 is a continuation of text1
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            True if text2 continues text1
        """
        # Check if text2 starts where text1 ends (allowing for punctuation)
        if not text1 or not text2:
            return False
        
        # Remove trailing punctuation from text1
        text1_stripped = text1.rstrip('.,!?;: ')
        
        # Check if text2 starts with the end of text1
        words1 = text1_stripped.split()
        words2 = text2.split()
        
        if len(words1) >= 2 and len(words2) >= 2:
            # Check if last 2 words of text1 match first 2 words of text2
            if words1[-2:] == words2[:2]:
                return True
            # Or if last word of text1 matches first word of text2
            if words1[-1] == words2[0]:
                return True
        
        return False
    
    def _merge_subtitles(self, subtitles: List[Subtitle]) -> Subtitle:
        """Merge multiple subtitles into one
        
        Args:
            subtitles: List of subtitles to merge
            
        Returns:
            Merged subtitle
        """
        if not subtitles:
            raise ValueError("Cannot merge empty list of subtitles")
        
        if len(subtitles) == 1:
            return subtitles[0]
        
        # Use earliest start time and latest end time
        start_time = min(sub.start_time for sub in subtitles)
        end_time = max(sub.end_time for sub in subtitles)
        
        # Merge text intelligently
        merged_text = self._merge_text([sub.text for sub in subtitles])
        
        # Use first subtitle's index and metadata as base
        first = subtitles[0]
        
        return Subtitle(
            index=first.index,
            start_time=start_time,
            end_time=end_time,
            text=merged_text,
            metadata=first.metadata.copy()
        )
    
    def _merge_text(self, texts: List[str]) -> str:
        """Merge multiple text strings intelligently
        
        Args:
            texts: List of text strings to merge
            
        Returns:
            Merged text
        """
        if not texts:
            return ""
        
        if len(texts) == 1:
            return texts[0]
        
        # Normalize texts for comparison
        normalized = [self._normalize_text(t) for t in texts]
        
        # If all texts are identical, return the first one
        if all(n == normalized[0] for n in normalized):
            return texts[0]
        
        # Check if texts are continuations - if so, use the longest
        # (it likely contains all the information)
        longest_idx = max(range(len(texts)), key=lambda i: len(normalized[i]))
        longest_text = normalized[longest_idx]
        
        # If the longest text contains all others, use it
        if all(n in longest_text or longest_text in n for n in normalized):
            return texts[longest_idx]
        
        # Otherwise, concatenate unique parts with line breaks
        unique_texts = []
        seen = set()
        
        for text, norm in zip(texts, normalized):
            if norm not in seen and norm:
                unique_texts.append(text.strip())
                seen.add(norm)
        
        return '\n'.join(unique_texts)