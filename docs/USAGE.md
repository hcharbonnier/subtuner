# SubTuner Usage Guide

This guide provides detailed usage instructions for SubTuner, the subtitle optimization CLI tool.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Command Line Options](#command-line-options)
4. [Usage Examples](#usage-examples)
5. [Configuration](#configuration)
6. [Output Files](#output-files)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Usage](#advanced-usage)

## Installation

### Prerequisites

1. **Python 3.8+**
2. **FFmpeg and FFprobe** (must be in system PATH)

### Install SubTuner

```bash
pip install subtuner
```

### Verify Installation

```bash
# Check SubTuner
subtuner --version

# Check FFmpeg
ffmpeg -version
ffprobe -version
```

## Quick Start

### Basic Usage

Optimize all subtitle tracks in a video:

```bash
subtuner movie.mkv
```

This will:
1. Extract all text-based subtitle tracks from `movie.mkv`
2. Apply optimization algorithms with default settings
3. Save optimized subtitles as separate files: `movie.0.srt`, `movie.1.ass`, etc.

### Preview Before Processing

See what changes would be made:

```bash
subtuner movie.mkv --dry-run
```

### Get Help

```bash
subtuner --help
```

## Command Line Options

### Required Arguments

- `VIDEO_PATH`: One or more paths to video files (MKV, MP4, etc.)

### Optimization Parameters

| Option | Default | Range | Description |
|--------|---------|-------|-------------|
| `--chars-per-sec` | 20.0 | 10-40 | Reading speed in characters per second |
| `--max-duration` | 8.0 | 3-15 | Maximum subtitle display duration (seconds) |
| `--min-duration` | 1.0 | 0.5-2 | Minimum subtitle display duration (seconds) |
| `--min-gap` | 0.05 | 0.01-0.2 | Minimum gap between subtitles (seconds) |
| `--max-anticipation` | 0.5 | 0-1 | Maximum time to start subtitles early (seconds) |
| `--short-threshold` | 0.8 | 0.5-1.5 | Threshold for "short" subtitle (seconds) |
| `--long-threshold` | 3.0 | 2-6 | Threshold for "long" subtitle (seconds) |

### Processing Options

| Option | Description |
|--------|-------------|
| `--output-dir PATH` | Output directory (default: same as input file) |
| `--dry-run` | Preview changes without writing files |
| `--verbose` | Show detailed processing information |
| `--quiet` | Suppress all output except errors |
| `--report-format` | Report format: console, json, markdown, csv |
| `--save-report PATH` | Save detailed report to file |

## Usage Examples

### Scenario 1: Fast-Paced Anime

For anime with rapid dialogue:

```bash
subtuner anime.mkv \
  --chars-per-sec 25 \
  --max-anticipation 0.6 \
  --short-threshold 0.6
```

**Why these settings?**
- Higher reading speed (25 chars/sec) for experienced viewers
- More anticipation (0.6s) to compensate for fast dialogue
- Lower short threshold (0.6s) to catch more brief dialogue

### Scenario 2: Educational Content

For documentaries or lectures:

```bash
subtuner lecture.mp4 \
  --chars-per-sec 15 \
  --min-duration 2.0 \
  --max-duration 10.0
```

**Why these settings?**
- Slower reading speed (15 chars/sec) for complex content
- Longer minimum duration (2s) for better comprehension
- Allow longer displays (10s) for detailed explanations

### Scenario 3: Accessibility

For viewers needing extra reading time:

```bash
subtuner movie.mkv \
  --chars-per-sec 12 \
  --min-duration 3.0 \
  --max-anticipation 0 \
  --min-gap 0.2
```

**Why these settings?**
- Very slow reading speed (12 chars/sec)
- Long minimum duration (3s)
- No anticipation (0s) for predictable timing
- Larger gaps (0.2s) for clear separation

### Scenario 4: Action Movies

For action films with quick dialogue:

```bash
subtuner action_movie.mkv \
  --chars-per-sec 22 \
  --max-anticipation 0.7 \
  --long-threshold 4.0
```

**Why these settings?**
- Faster reading speed (22 chars/sec)
- More anticipation (0.7s) for quick dialogue
- Higher long threshold (4s) to identify truly excessive subtitles

### Scenario 5: Foreign Films

For subtitled foreign language films:

```bash
subtuner foreign_film.mkv \
  --chars-per-sec 18 \
  --min-duration 1.5 \
  --max-duration 7.0
```

**Why these settings?**
- Moderate reading speed (18 chars/sec) for translation comprehension
- Slightly longer minimum (1.5s) for context switching
- Reasonable maximum (7s) to avoid excessive display

### Scenario 6: Batch Processing

Process an entire TV series:

```bash
subtuner series_s01/*.mkv \
  --output-dir ./optimized_subtitles/ \
  --verbose \
  --save-report series_report.json \
  --report-format json
```

### Scenario 7: Custom Output Location

Organize optimized subtitles in a specific directory:

```bash
subtuner movie.mkv \
  --output-dir ~/Downloads/optimized/ \
  --save-report ~/Downloads/optimization_report.md \
  --report-format markdown
```

## Configuration

### Reading Speed Guidelines

Choose `--chars-per-sec` based on your target audience:

| Audience | Chars/Sec | Notes |
|----------|-----------|-------|
| Children | 10-12 | Very slow, learning to read |
| Casual viewers | 15-18 | Comfortable reading pace |
| **Default** | **20** | **Average adult reading speed** |
| Experienced viewers | 22-25 | Fast readers, gamers |
| Native speakers | 25-30 | Very fast reading |
| Speed readers | 30-40 | Expert level |

### Duration Guidelines

Choose duration settings based on content type:

| Content Type | Min Duration | Max Duration | Notes |
|--------------|--------------|--------------|-------|
| Action/Anime | 0.8s | 6s | Fast paced content |
| **General** | **1.0s** | **8s** | **Default settings** |
| Documentary | 1.5s | 10s | Complex information |
| Educational | 2.0s | 12s | Learning content |
| Accessibility | 3.0s | 15s | Extra reading time |

### Anticipation Guidelines

| Use Case | Max Anticipation | Notes |
|----------|------------------|-------|
| Predictable timing | 0s | No anticipation |
| **General use** | **0.5s** | **Default setting** |
| Fast dialogue | 0.6-0.8s | More reading time |
| Overlapping speech | 0.3s | Conservative anticipation |

## Output Files

### Naming Convention

SubTuner saves optimized subtitles using this pattern:
```
{original_name}.{track_index}.{format}
```

Examples:
- `movie.mkv` with tracks 0 (SRT) and 1 (ASS) → `movie.0.srt`, `movie.1.ass`
- `episode_01.mp4` with track 0 (SRT) → `episode_01.0.srt`

### Format Preservation

- **SRT**: Preserves text formatting and line breaks
- **WebVTT**: Preserves styling tags, positioning, and cue settings
- **ASS/SSA**: Preserves all styles, effects, and override tags

### Output Directory

By default, files are saved in the same directory as the input video. Use `--output-dir` to specify a different location:

```bash
subtuner movie.mkv --output-dir ./subtitles/
```

## Troubleshooting

### Common Issues

#### 1. FFmpeg Not Found

**Error:**
```
FFmpeg not found. Please install FFmpeg or specify custom path.
```

**Solutions:**
```bash
# Install FFmpeg
# Windows (Chocolatey):
choco install ffmpeg

# macOS (Homebrew):
brew install ffmpeg

# Linux (apt):
sudo apt install ffmpeg

# Verify installation:
ffmpeg -version
```

#### 2. No Subtitle Tracks Found

**Error:**
```
No text-based subtitle tracks found
```

**Possible causes:**
- Video has no embedded subtitles
- Subtitles are image-based (PGS, VobSub) - not supported
- Subtitles are external files (use files directly with other tools)

**Check with:**
```bash
ffprobe -v quiet -select_streams s -show_streams movie.mkv
```

#### 3. Permission Denied

**Error:**
```
Permission denied writing to /path/
```

**Solutions:**
- Ensure write permissions in output directory
- Use different output directory with `--output-dir`
- Run with appropriate privileges

#### 4. Encoding Issues

**Error:**
```
Failed to parse subtitle file (encoding issue)
```

**Solutions:**
- SubTuner auto-detects encoding, but may fail with unusual files
- Try different video source
- Check subtitle integrity with media player

#### 5. Large File Processing

**Issue:** Processing very large files (>3 hours) slowly

**Solutions:**
```bash
# Use more conservative settings to reduce processing
subtuner large_movie.mkv \
  --max-anticipation 0.2 \
  --chars-per-sec 20
```

### Debug Mode

For troubleshooting, use verbose output:

```bash
subtuner movie.mkv --verbose
```

This shows:
- Track detection details
- Algorithm processing steps
- File I/O operations
- Performance timing

## Advanced Usage

### Custom Reading Speeds by Content

#### Technical Documentation
```bash
subtuner tech_doc.mp4 --chars-per-sec 12 --min-duration 3.0
```

#### Gaming Content
```bash
subtuner gameplay.mkv --chars-per-sec 28 --max-anticipation 0.8
```

#### Children's Content
```bash
subtuner kids_movie.mkv --chars-per-sec 10 --min-duration 2.5
```

### Optimization Profiles

Create shell functions for common profiles:

```bash
# Fast profile
alias subtuner-fast='subtuner --chars-per-sec 25 --max-anticipation 0.6'

# Slow profile  
alias subtuner-slow='subtuner --chars-per-sec 15 --min-duration 2.0'

# Accessibility profile
alias subtuner-a11y='subtuner --chars-per-sec 12 --min-duration 3.0 --max-anticipation 0'

# Use profiles
subtuner-fast anime.mkv
subtuner-slow documentary.mp4
subtuner-a11y educational.mkv
```

### Batch Processing with Filtering

Process specific file types:
```bash
# Process all MKV files
subtuner *.mkv

# Process with shell globbing
subtuner /path/to/videos/**/*.{mkv,mp4}

# Process series with pattern
subtuner "Series S01"/*.mkv --output-dir "./Series S01/Optimized/"
```

### Report Analysis

Generate detailed reports for analysis:

```bash
# JSON report for programmatic analysis
subtuner movie.mkv \
  --save-report analysis.json \
  --report-format json

# Markdown report for documentation
subtuner *.mkv \
  --save-report batch_report.md \
  --report-format markdown

# CSV report for spreadsheet analysis
subtuner series/*.mkv \
  --save-report series_stats.csv \
  --report-format csv
```

### Environment Variables

Override default paths with environment variables:

```bash
# Custom FFmpeg location
export SUBTUNER_FFMPEG_PATH=/custom/path/to/ffmpeg
export SUBTUNER_FFPROBE_PATH=/custom/path/to/ffprobe

# Custom temp directory
export SUBTUNER_TEMP_DIR=/fast/ssd/temp

# Default log level
export SUBTUNER_LOG_LEVEL=DEBUG
```

### Pipeline Integration

Integrate SubTuner into media processing pipelines:

```bash
#!/bin/bash
# Media processing pipeline

VIDEO_FILE="$1"
OUTPUT_DIR="processed"

# 1. Optimize subtitles
subtuner "$VIDEO_FILE" \
  --output-dir "$OUTPUT_DIR" \
  --report-format json \
  --save-report "$OUTPUT_DIR/optimization.json" \
  --quiet

# 2. Further processing...
echo "Subtitle optimization complete for $VIDEO_FILE"
```

### Performance Tuning

For large files or batch processing:

```bash
# Conservative settings for speed
subtuner large_file.mkv \
  --chars-per-sec 20 \
  --max-anticipation 0.3 \
  --long-threshold 4.0 \
  --quiet

# Process in smaller batches
find . -name "*.mkv" -print0 | xargs -0 -n 5 subtuner
```

## Best Practices

### 1. Test with Dry Run First

Always preview changes on important content:
```bash
subtuner important_movie.mkv --dry-run --verbose
```

### 2. Backup Important Files

For irreplaceable content, backup original subtitles:
```bash
# Extract original subtitles first
ffmpeg -i movie.mkv -c:s copy original_subtitles.srt

# Then optimize
subtuner movie.mkv
```

### 3. Validate Results

Check optimization results with a media player:
- Load optimized subtitles in VLC, MPV, or similar
- Verify timing feels natural
- Check for any overlaps or gaps

### 4. Use Appropriate Profiles

Match settings to content type:
- **Action/Anime**: Fast reading, more anticipation
- **Drama**: Standard settings
- **Documentary**: Slower reading, longer durations
- **Accessibility**: Very slow reading, no anticipation

### 5. Monitor Statistics

Pay attention to modification percentages:
- **<30%**: Minimal changes, subtitles were already good
- **30-60%**: Normal optimization, significant improvements
- **>60%**: Extensive changes, verify results carefully

### 6. Batch Processing Considerations

For large batch jobs:
- Use `--quiet` to reduce output
- Save reports for later analysis
- Monitor disk space for output files
- Consider processing in smaller batches

## Output Interpretation

### Statistics Report

Understanding the optimization report:

```
Duration Adjustments: 847 (55.6%)
  Average Change: +0.34s
```
- 55.6% of subtitles had their duration adjusted
- Average extension was 0.34 seconds

```
Rebalanced Pairs: 23 (1.5%)
  Total Time Transferred: 5.8s
```
- 23 subtitle pairs were rebalanced
- 5.8 seconds total was transferred from long to short subtitles

```
Anticipated Subtitles: 156 (10.2%)
  Average Anticipation: 0.28s
```
- 10.2% of subtitles were started earlier
- Average anticipation was 0.28 seconds

### File Size Changes

- **Minimal increase**: Optimized timing doesn't significantly increase file size
- **SRT files**: Usually 1-5% larger due to longer timestamps
- **ASS files**: Same size (timing changes only)
- **WebVTT files**: Minimal change

## Integration with Media Players

### VLC

Load optimized subtitles:
1. Open video in VLC
2. Go to **Subtitle** → **Add Subtitle File...**
3. Select optimized subtitle file
4. Adjust sync if needed with **J**/**K** keys

### MPV

Use optimized subtitles:
```bash
mpv movie.mkv --sub-file=movie.0.srt
```

### MPC-HC

1. Open video
2. Right-click → **Subtitles** → **Load Subtitle...**
3. Select optimized file

### Plex/Jellyfin

1. Place optimized subtitles in same directory as video
2. Name them according to server conventions:
   - `movie.eng.srt` for English subtitles
   - `movie.eng.forced.srt` for forced subtitles

## Automation Examples

### Automated Video Processing

```bash
#!/bin/bash
# Process new downloads automatically

DOWNLOAD_DIR="$HOME/Downloads"
PROCESSED_DIR="$HOME/Videos/Processed"

# Find new video files
find "$DOWNLOAD_DIR" -name "*.mkv" -o -name "*.mp4" | while read video; do
  echo "Processing: $(basename "$video")"
  
  # Optimize subtitles
  subtuner "$video" \
    --output-dir "$PROCESSED_DIR" \
    --save-report "$PROCESSED_DIR/$(basename "$video" .mkv)_report.json" \
    --report-format json \
    --quiet
  
  echo "Completed: $(basename "$video")"
done
```

### Series Processing Script

```bash
#!/bin/bash
# Process TV series with consistent settings

SERIES_DIR="$1"
if [ -z "$SERIES_DIR" ]; then
  echo "Usage: $0 <series_directory>"
  exit 1
fi

echo "Processing series in: $SERIES_DIR"

subtuner "$SERIES_DIR"/*.mkv \
  --chars-per-sec 22 \
  --output-dir "$SERIES_DIR/Subtitles/" \
  --save-report "$SERIES_DIR/optimization_report.md" \
  --report-format markdown \
  --verbose

echo "Series processing complete!"
echo "Report saved: $SERIES_DIR/optimization_report.md"
```

### Quality Control Script

```bash
#!/bin/bash
# Quality control script with validation

VIDEO="$1"
TEMP_DIR="/tmp/subtuner_qc"

mkdir -p "$TEMP_DIR"

# 1. Dry run first
echo "=== DRY RUN ANALYSIS ==="
subtuner "$VIDEO" --dry-run --verbose

# 2. Process with conservative settings
echo "=== PROCESSING ==="
subtuner "$VIDEO" \
  --output-dir "$TEMP_DIR" \
  --chars-per-sec 18 \
  --max-anticipation 0.3 \
  --save-report "$TEMP_DIR/report.json" \
  --report-format json

# 3. Analyze results
echo "=== RESULTS ANALYSIS ==="
python3 -c "
import json
with open('$TEMP_DIR/report.json') as f:
    data = json.load(f)
stats = data['track_statistics']
if stats['modification_percentage'] > 70:
    print('WARNING: High modification rate:', stats['modification_percentage'], '%')
else:
    print('GOOD: Reasonable modification rate:', stats['modification_percentage'], '%')
"

echo "Quality control complete. Files in: $TEMP_DIR"
```

## Performance Guidelines

### Expected Processing Times

| Video Length | Subtitle Count | Typical Time |
|--------------|----------------|--------------|
| 30 minutes | ~400 subtitles | 1-2 seconds |
| 1 hour | ~800 subtitles | 2-4 seconds |
| 2 hours | ~1500 subtitles | 5-10 seconds |
| 3+ hours | ~2500+ subtitles | 10-20 seconds |

### Memory Usage

SubTuner is designed to be memory efficient:
- Typical usage: 50-100 MB RAM
- Large files (3h+): 200-500 MB RAM
- Batch processing: Processes files sequentially to limit memory

### Optimization Tips

For faster processing:
1. Use `--quiet` to reduce I/O overhead
2. Process files individually rather than large batches
3. Use SSD for temporary files
4. Close other applications during large batch jobs

---

This usage guide covers the most common scenarios and configurations for SubTuner. For additional questions, refer to the [README.md](../README.md) or open an issue on GitHub.