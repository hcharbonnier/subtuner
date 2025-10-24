# ASS Subtitle Adjustments

This document describes the ASS-specific adjustment features added to SubTuner.

## Overview

SubTuner now supports adjusting font size and Y position for dialog subtitles in ASS format files. These adjustments are applied to the most-used style (typically the dialog style) in the subtitle file.

## Features

### 1. Font Size Adjustment

Adjust the font size of dialog subtitles by a specified amount.

**CLI Option:** `--ass-font-size-adjust`

**Example:**
```bash
# Increase font size by 2 points
subtuner subtitles.ass --ass-font-size-adjust 2

# Decrease font size by 2 points
subtuner subtitles.ass --ass-font-size-adjust -2
```

### 2. Y Position Adjustment

Adjust the vertical position of dialog subtitles by a specified number of pixels.

**CLI Option:** `--ass-y-position-adjust`

**Example:**
```bash
# Move subtitles up by 100 pixels
subtuner subtitles.ass --ass-y-position-adjust -100

# Move subtitles down by 100 pixels
subtuner subtitles.ass --ass-y-position-adjust 100
```

### 3. Combined Adjustments

Both adjustments can be used together:

```bash
subtuner subtitles.ass --ass-font-size-adjust 2 --ass-y-position-adjust -50
```

## How It Works

### Dialog Style Detection

The system automatically identifies the "dialog style" by analyzing which style is used most frequently in the subtitle file. This is typically the style used for character dialogue, as opposed to signs, songs, or other special text.

**Algorithm:**
1. Count the usage of each style across all subtitle events
2. Identify the most frequently used style
3. Apply adjustments only to that style

### Font Size Adjustment

- Modifies the `fontsize` property of the identified dialog style
- Ensures the resulting font size is at least 1 (minimum valid size)
- Original: `fontsize = 20` → With `+2`: `fontsize = 22`

### Y Position Adjustment

- Modifies the `margin_v` (vertical margin) property of the identified dialog style
- Positive values move subtitles down, negative values move them up
- Ensures the resulting margin is non-negative (minimum 0)
- Original: `margin_v = 10` → With `+100`: `margin_v = 110`

## Implementation Details

### Configuration

New fields added to [`ProcessingConfig`](subtuner/config.py):
- `ass_font_size_adjust: int = 0` - Font size adjustment
- `ass_y_position_adjust: int = 0` - Y position adjustment

### ASS Writer Enhancements

The [`ASSWriter`](subtuner/writers/ass_writer.py) class now includes:

1. **`set_adjustments(font_size_adjust, y_position_adjust)`**
   - Sets the adjustment values before writing

2. **`_identify_dialog_style(subtitles)`**
   - Analyzes subtitle events to find the most-used style
   - Returns the style name or None if not found

3. **`_apply_style_adjustments(doc, style_name)`**
   - Applies font size and Y position adjustments to the specified style
   - Validates and logs all changes

### CLI Integration

The [`SubTunerCLI`](subtuner/cli.py) class automatically:
1. Detects when processing ASS/SSA files
2. Passes adjustment values from config to the writer
3. Applies adjustments before writing the output file

## Examples

### Example 1: Increase Font Size for Better Readability

```bash
subtuner "movie.ass" --ass-font-size-adjust 3
```

This increases the dialog font size by 3 points, making subtitles easier to read on large screens.

### Example 2: Reposition Subtitles to Avoid Overlapping Video Content

```bash
subtuner "anime.ass" --ass-y-position-adjust -80
```

This moves dialog subtitles up by 80 pixels, useful when the original position overlaps with on-screen text or important visual elements.

### Example 3: Combined Optimization with Adjustments

```bash
subtuner "series.mkv" \
  --chars-per-sec 18 \
  --ass-font-size-adjust 2 \
  --ass-y-position-adjust -50 \
  --output-label "optimized"
```

This extracts subtitles from a video file, optimizes timing for slower reading speed, increases font size, repositions subtitles, and saves with a custom label.

## Technical Notes

### Style Preservation

- All original style properties are preserved except for the adjusted ones
- Only the dialog style is modified; other styles (signs, songs, etc.) remain unchanged
- The original document structure (script info, other styles) is fully preserved

### Logging

The implementation includes detailed logging:
- Info level: Reports which style was identified as dialog and the adjustments applied
- Debug level: Reports when adjustments are set and document processing details
- Warning level: Reports if style identification fails or adjustments cannot be applied

### Error Handling

- If no ASS styles are found, adjustments are skipped gracefully
- If the identified style doesn't exist in the document, a warning is logged
- Invalid adjustment values are validated (minimum font size of 1, non-negative margins)

## Limitations

1. **Single Style Adjustment**: Only the most-used style is adjusted. If you need to adjust multiple styles, you'll need to edit the ASS file manually or run the tool multiple times with different source files.

2. **ASS/SSA Only**: These adjustments only work with ASS and SSA format files. SRT and VTT formats don't support style-based adjustments.

3. **Margin-Based Positioning**: Y position adjustment uses the `margin_v` property, which may interact with other positioning properties in complex ASS files.

## Future Enhancements

Potential improvements for future versions:
- Support for adjusting multiple styles by name
- X position adjustment (horizontal positioning)
- Color adjustments for dialog text
- Border and shadow adjustments
- Per-event positioning overrides