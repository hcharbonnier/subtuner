# SubTuner - Optimization Algorithms Specification

This document provides detailed specifications for the four optimization algorithms used by SubTuner.

## Table of Contents

1. [Overview](#overview)
2. [Algorithm 1: Duration Adjustment](#algorithm-1-duration-adjustment)
3. [Algorithm 2: Temporal Rebalancing](#algorithm-2-temporal-rebalancing)
4. [Algorithm 3: Conditional Anticipatory Offset](#algorithm-3-conditional-anticipatory-offset)
4. [Algorithm 4: Temporal Constraints Validation](#algorithm-4-temporal-constraints-validation)
5. [Algorithm Orchestration](#algorithm-orchestration)
6. [Edge Cases](#edge-cases)
7. [Examples](#examples)

## Overview

### Design Principles

1. **Readability First**: Optimize for viewer comprehension
2. **Semantic Preservation**: Maintain original subtitle boundaries
3. **Graceful Degradation**: Never make subtitles worse than original
4. **Deterministic**: Same input always produces same output
5. **Configurable**: All thresholds are user-adjustable

### Execution Order

The algorithms are applied in this specific order:

```
Original Subtitles
       ↓
1. Duration Adjustment (per subtitle)
       ↓
2. Temporal Rebalancing (pairwise)
       ↓
3. Anticipatory Offset (per subtitle)
       ↓
4. Constraints Validation (global)
       ↓
Optimized Subtitles
```

### Configuration Parameters

```python
@dataclass
class OptimizationConfig:
    # Reading speed
    chars_per_sec: float = 20.0      # Characters per second
    
    # Duration constraints
    max_duration: float = 8.0         # Maximum display time (seconds)
    min_duration: float = 1.0         # Minimum display time (seconds)
    
    # Timing constraints
    min_gap: float = 0.05            # Minimum gap between subtitles
    
    # Rebalancing thresholds
    short_threshold: float = 0.8     # Define "short" subtitle
    long_threshold: float = 3.0      # Define "long" subtitle
    
    # Anticipation
    max_anticipation: float = 0.5    # Maximum time to start earlier
```

## Algorithm 1: Duration Adjustment

### Purpose
Adjust each subtitle's display duration based on reading speed while respecting the available time window.

### Input
- Current subtitle
- Next subtitle (if exists)
- Configuration parameters

### Logic

```python
def adjust_duration(current: Subtitle, next: Optional[Subtitle], 
                   config: OptimizationConfig) -> Subtitle:
    """
    Adjust subtitle duration based on character count and reading speed.
    """
    # Calculate ideal duration based on reading speed
    char_count = len(current.text)
    ideal_duration = char_count / config.chars_per_sec
    
    # Apply duration constraints
    target_duration = max(config.min_duration, 
                         min(config.max_duration, ideal_duration))
    
    # Calculate available time window
    if next is not None:
        # Can extend until min_gap before next subtitle
        available_end_time = next.start_time - config.min_gap
        max_possible_duration = available_end_time - current.start_time
    else:
        # Last subtitle: no constraint from next
        max_possible_duration = float('inf')
    
    # Use minimum of target and available duration
    new_duration = min(target_duration, max_possible_duration)
    
    # Only extend, never shorten (semantic preservation)
    final_duration = max(new_duration, current.duration)
    
    return current.with_end_time(current.start_time + final_duration)
```

### Examples

**Example 1: Short subtitle with room to extend**
```
Original: "Hi!" (0.3s, 3 chars)
Ideal:    3 / 20 = 0.15s
Applied:  1.0s (min_duration constraint)
Result:   Extended from 0.3s to 1.0s
```

**Example 2: Long subtitle clamped by max_duration**
```
Original: "This is a very long subtitle..." (5.0s, 180 chars)
Ideal:    180 / 20 = 9.0s
Applied:  8.0s (max_duration constraint)
Result:   Extended from 5.0s to 8.0s
```

**Example 3: Limited by next subtitle**
```
Current:  "Hello" at 10.0-10.5s (5 chars)
Next:     Starts at 11.0s
Ideal:    5 / 20 = 0.25s
Available: 11.0 - 0.05 - 10.0 = 0.95s
Applied:  0.95s (limited by next subtitle)
Result:   Extended to 10.0-10.95s
```

## Algorithm 2: Temporal Rebalancing

### Purpose
Transfer time from abnormally long subtitles to abnormally short ones to balance display times.

### Rationale
Sometimes a short subtitle is followed by a long one with ample time. Rebalancing improves readability of the short subtitle without significantly impacting the long one.

### Logic

```python
def rebalance_pair(current: Subtitle, next: Subtitle,
                  config: OptimizationConfig) -> Tuple[Subtitle, Subtitle, float]:
    """
    Rebalance time between a short subtitle and following long subtitle.
    """
    # Check if rebalancing conditions are met
    is_current_short = current.duration < config.short_threshold
    is_next_long = next.duration > config.long_threshold
    
    if not (is_current_short and is_next_long):
        return current, next, 0.0  # No rebalancing needed
    
    # Calculate how much time we want to add to current
    current_deficit = config.short_threshold - current.duration
    
    # Calculate how much we can take from next
    next_surplus = next.duration - config.long_threshold
    
    # Transfer amount is minimum of deficit and surplus
    transfer_amount = min(current_deficit, next_surplus)
    
    if transfer_amount <= 0:
        return current, next, 0.0
    
    # Apply the transfer while maintaining min_gap
    new_current_end = current.end_time + transfer_amount
    new_next_start = new_current_end + config.min_gap
    
    # Verify we don't create invalid state
    if new_next_start >= next.end_time:
        return current, next, 0.0  # Transfer would make next too short
    
    new_current = current.with_end_time(new_current_end)
    new_next = next.with_start_time(new_next_start)
    
    return new_current, new_next, transfer_amount
```

### Examples

**Example 1: Successful rebalancing**
```
Current: "Hi" at 10.0-10.5s (0.5s duration, short!)
Next:    "This is a much longer subtitle" at 11.0-15.0s (4.0s, long)

Analysis:
- Current is short (0.5s < 0.8s threshold)
- Next is long (4.0s > 3.0s threshold)
- Current deficit: 0.8 - 0.5 = 0.3s
- Next surplus: 4.0 - 3.0 = 1.0s
- Transfer: min(0.3, 1.0) = 0.3s

Result:
- Current: 10.0-10.8s (0.8s duration) ← gained 0.3s
- Next:    10.85-15.0s (4.15s duration) ← lost 0.3s + gap
```

**Example 2: No rebalancing needed**
```
Current: "Hello" at 10.0-11.5s (1.5s duration, not short)
Next:    "World" at 12.0-13.0s (1.0s duration, not long)

Result: No changes, conditions not met
```

## Algorithm 3: Conditional Anticipatory Offset

### Purpose
Start subtitles earlier when it increases display duration without excessive overlap with previous subtitle.

### Rationale
Viewers can process text that appears slightly before the speech begins. Starting subtitles earlier can provide more reading time, especially beneficial for fast dialogue.

### Logic

```python
def apply_anticipation(current: Subtitle, previous: Optional[Subtitle],
                      config: OptimizationConfig) -> Tuple[Subtitle, float]:
    """
    Start subtitle earlier to increase display duration.
    """
    if previous is None:
        # First subtitle: can anticipate freely
        max_offset = config.max_anticipation
    else:
        # Calculate maximum offset without violating min_gap
        gap_to_previous = current.start_time - previous.end_time
        max_offset = max(0, gap_to_previous - config.min_gap)
    
    # Limit to configured maximum
    actual_offset = min(max_offset, config.max_anticipation)
    
    # Only apply if it actually increases duration
    if actual_offset <= 0:
        return current, 0.0
    
    # Calculate new times
    new_start = current.start_time - actual_offset
    new_duration = current.end_time - new_start
    
    # Verify anticipation increases duration meaningfully
    duration_increase = new_duration - current.duration
    if duration_increase < 0.1:  # Minimum benefit threshold
        return current, 0.0
    
    new_current = Subtitle(
        index=current.index,
        start_time=new_start,
        end_time=current.end_time,  # Keep end_time fixed
        text=current.text,
        metadata=current.metadata
    )
    
    return new_current, actual_offset
```

### Examples

**Example 1: Successful anticipation**
```
Previous: Ends at 10.0s
Current:  "Hello world" at 11.0-12.0s (1.0s duration)

Analysis:
- Gap to previous: 11.0 - 10.0 = 1.0s
- Available for anticipation: 1.0 - 0.05 = 0.95s
- Configured maximum: 0.5s
- Actual offset: min(0.95, 0.5) = 0.5s
- Duration increase: 0.5s (meaningful)

Result:
- Current: 10.5-12.0s (1.5s duration)
- Started 0.5s earlier
```

**Example 2: Limited by previous subtitle**
```
Previous: Ends at 10.8s
Current:  "Quick!" at 11.0-11.5s (0.5s duration)

Analysis:
- Gap to previous: 11.0 - 10.8 = 0.2s
- Available: 0.2 - 0.05 = 0.15s
- Configured maximum: 0.5s
- Actual offset: min(0.15, 0.5) = 0.15s

Result:
- Current: 10.85-11.5s (0.65s duration)
- Started 0.15s earlier
```

**Example 3: No anticipation (insufficient benefit)**
```
Previous: Ends at 10.95s
Current:  "Hi" at 11.0-12.0s (1.0s duration)

Analysis:
- Gap to previous: 11.0 - 10.95 = 0.05s
- Available: 0.05 - 0.05 = 0.0s

Result: No change (no room for anticipation)
```

## Algorithm 4: Temporal Constraints Validation

### Purpose
Ensure all subtitles meet hard constraints after optimization.

### Logic

```python
def validate_and_fix(subtitles: List[Subtitle],
                    config: OptimizationConfig) -> List[Subtitle]:
    """
    Enforce hard constraints across all subtitles.
    """
    validated = []
    
    for i, current in enumerate(subtitles):
        previous = validated[-1] if validated else None
        
        # Fix 1: Enforce minimum duration
        if current.duration < config.min_duration:
            # Try to extend end_time
            target_end = current.start_time + config.min_duration
            
            # Check if next subtitle allows this
            if i + 1 < len(subtitles):
                next_sub = subtitles[i + 1]
                max_end = next_sub.start_time - config.min_gap
                target_end = min(target_end, max_end)
            
            current = current.with_end_time(max(target_end, current.end_time))
        
        # Fix 2: Enforce minimum gap with previous
        if previous is not None:
            required_start = previous.end_time + config.min_gap
            if current.start_time < required_start:
                # Shift current subtitle forward
                shift = required_start - current.start_time
                current = Subtitle(
                    index=current.index,
                    start_time=required_start,
                    end_time=current.end_time + shift,
                    text=current.text,
                    metadata=current.metadata
                )
        
        # Fix 3: Ensure chronological order
        if previous is not None and current.start_time < previous.start_time:
            # Serious error: skip this subtitle
            continue
        
        # Fix 4: Ensure start < end
        if current.start_time >= current.end_time:
            # Serious error: skip this subtitle
            continue
        
        validated.append(current)
    
    return validated
```

### Fixes Applied

1. **Minimum Duration**: Extend subtitles shorter than min_duration
2. **Minimum Gap**: Shift subtitles that are too close to previous
3. **Chronological Order**: Remove subtitles out of sequence (rare)
4. **Valid Time Range**: Remove subtitles with invalid times (rare)

## Algorithm Orchestration

### Complete Processing Pipeline

```python
def optimize_subtitle_track(subtitles: List[Subtitle],
                           config: OptimizationConfig) -> OptimizationResult:
    """
    Apply all optimization algorithms in sequence.
    """
    stats = OptimizationStatistics()
    optimized = subtitles.copy()
    
    # Phase 1: Duration Adjustment
    for i in range(len(optimized)):
        current = optimized[i]
        next_sub = optimized[i + 1] if i + 1 < len(optimized) else None
        
        adjusted = adjust_duration(current, next_sub, config)
        if adjusted.duration != current.duration:
            stats.duration_adjustments += 1
            stats.total_duration_change += (adjusted.duration - current.duration)
        
        optimized[i] = adjusted
    
    # Phase 2: Temporal Rebalancing
    i = 0
    while i < len(optimized) - 1:
        current = optimized[i]
        next_sub = optimized[i + 1]
        
        new_current, new_next, transferred = rebalance_pair(
            current, next_sub, config
        )
        
        if transferred > 0:
            stats.rebalanced_pairs += 1
            stats.total_time_transferred += transferred
            optimized[i] = new_current
            optimized[i + 1] = new_next
        
        i += 1
    
    # Phase 3: Anticipatory Offset
    for i in range(len(optimized)):
        current = optimized[i]
        previous = optimized[i - 1] if i > 0 else None
        
        anticipated, offset = apply_anticipation(current, previous, config)
        if offset > 0:
            stats.anticipated_subtitles += 1
            stats.total_anticipation += offset
        
        optimized[i] = anticipated
    
    # Phase 4: Constraints Validation
    optimized = validate_and_fix(optimized, config)
    
    # Calculate final statistics
    stats.original_count = len(subtitles)
    stats.final_count = len(optimized)
    stats.total_modifications = (
        stats.duration_adjustments +
        stats.rebalanced_pairs +
        stats.anticipated_subtitles
    )
    
    return OptimizationResult(
        subtitles=optimized,
        statistics=stats
    )
```

## Edge Cases

### Case 1: Very Dense Subtitles
```
Problem: Subtitles with minimal gaps between them
Solution: Algorithms respect min_gap constraint, won't force overlaps
```

### Case 2: First Subtitle
```
Problem: No previous subtitle for anticipation context
Solution: Can anticipate up to max_anticipation freely
```

### Case 3: Last Subtitle
```
Problem: No next subtitle for duration calculation
Solution: Can extend up to max_duration freely
```

### Case 4: Single Character Subtitle
```
Problem: Calculated duration < min_duration
Solution: min_duration constraint ensures readability
```

### Case 5: Already Optimal
```
Problem: Subtitle already has ideal duration
Solution: No changes made (graceful degradation)
```

### Case 6: Conflicting Constraints
```
Problem: Can't achieve min_duration without violating min_gap
Solution: Prioritize min_gap (don't create overlaps)
```

## Examples

### Complete Example

**Original Subtitle Sequence:**
```
1. "Hi!" at 10.0-10.3s (0.3s, 3 chars)
2. "How are you doing today? This is quite a long subtitle." 
   at 11.0-15.0s (4.0s, 57 chars)
3. "Good!" at 15.5-16.0s (0.5s, 5 chars)
```

**Configuration:**
```python
config = OptimizationConfig(
    chars_per_sec=20.0,
    max_duration=8.0,
    min_duration=1.0,
    min_gap=0.05,
    short_threshold=0.8,
    long_threshold=3.0,
    max_anticipation=0.5
)
```

**Processing Steps:**

1. **Duration Adjustment:**
   - Sub 1: 3/20 = 0.15s → 1.0s (min_duration) → extend to 10.0-11.0s
   - Sub 2: 57/20 = 2.85s → keep 4.0s (already above ideal)
   - Sub 3: 5/20 = 0.25s → 1.0s (min_duration) → extend to 15.5-16.5s

2. **Temporal Rebalancing:**
   - Pair 1-2: Sub 1 now 1.0s (not short), skip
   - Pair 2-3: Sub 2 is 4.0s (long), Sub 3 is 1.0s (not short), skip

3. **Anticipatory Offset:**
   - Sub 1: First subtitle, no anticipation needed
   - Sub 2: Gap from Sub 1: 0.05s, can't anticipate
   - Sub 3: Gap from Sub 2: 0.5s, can anticipate 0.45s
     → New: 15.05-16.5s (1.45s duration)

4. **Validation:**
   - All constraints met ✓

**Final Result:**
```
1. "Hi!" at 10.0-11.0s (1.0s) ← extended from 0.3s
2. "How are you..." at 11.05-15.0s (3.95s) ← slight gap adjustment
3. "Good!" at 15.05-16.5s (1.45s) ← extended + anticipated
```

**Statistics:**
- Duration adjustments: 2 (Sub 1, Sub 3)
- Rebalanced pairs: 0
- Anticipated subtitles: 1 (Sub 3)
- Total modifications: 3

## Performance Characteristics

### Time Complexity
- **Duration Adjustment**: O(n)
- **Rebalancing**: O(n)
- **Anticipation**: O(n)
- **Validation**: O(n)
- **Total**: O(n) where n = number of subtitles

### Space Complexity
- O(n) for storing modified subtitles
- Algorithms process in-place where possible

### Optimization for Large Files
- Stream processing: Process subtitles in chunks
- Early termination: Skip remaining checks if no changes possible
- Lazy evaluation: Only compute statistics when needed

## Testing Requirements

Each algorithm must be tested with:

1. **Normal cases**: Typical subtitle sequences
2. **Edge cases**: First/last subtitles, single subtitle
3. **Boundary conditions**: Values at threshold limits
4. **Invalid inputs**: Out-of-order, negative durations
5. **Large datasets**: 2000+ subtitles for performance
6. **Real-world samples**: Actual video subtitle files

## Conclusion

These algorithms work together to optimize subtitle readability while preserving the original semantic structure. The modular design allows each algorithm to be:
- Tested independently
- Configured separately
- Disabled if needed
- Extended with new rules

The key insight is that subtitle optimization is not about perfect precision but about improving readability within practical constraints.