# SubTuner 🎬📝

A powerful Python CLI tool for optimizing embedded subtitles in video files (MKV, MP4) to improve readability while preserving semantic structure.

## Features

✨ **Smart Optimization**
- **Duplicate Merging**: Automatically merges overlapping and identical subtitles (enabled by default)
- **Duration Adjustment**: Automatically calculates optimal display duration based on reading speed (default: 20 chars/sec)
- **Temporal Rebalancing**: Transfers time from long subtitles to short ones for balanced viewing
- **Anticipatory Display**: Shows subtitles slightly earlier when beneficial
- **Strict Constraints**: Ensures minimum display times and gaps between subtitles

🎯 **Robust Processing**
- Extracts all text subtitle tracks from video files
- Supports SRT, WebVTT, and ASS/SSA formats
- Preserves original formatting and styles
- **ASS-specific adjustments**: Font size and Y position for dialog subtitles
- Handles corrupted files and encoding issues gracefully

📊 **Detailed Statistics**
- Tracks all modifications per subtitle track
- Reports processing time and optimization metrics
- Provides before/after comparisons

🚀 **Productivity Features**
- Batch processing for multiple videos
- Dry-run mode to preview changes
- Configurable parameters for fine-tuning
- Multi-level logging for debugging

## Requirements

### System Dependencies
- **Python 3.8+**
- **FFmpeg** and **FFprobe** (must be in PATH)

### Installation

#### Option 1: From PyPI (when published)
```bash
pip install subtuner
```

#### Option 2: From Source
```bash
git clone https://github.com/hcharbonnier/subtuner
cd subtuner
pip install -e .
```

#### Option 3: Using Poetry
```bash
poetry install
```

### Installing FFmpeg

**Windows:**
```bash
# Using Chocolatey
choco install ffmpeg

# Or download from https://ffmpeg.org/download.html
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
# Debian/Ubuntu
sudo apt-get install ffmpeg

# Fedora
sudo dnf install ffmpeg

# Arch
sudo pacman -S ffmpeg
```

## Quick Start

### Basic Usage

Optimize a single video file:
```bash
subtuner movie.mkv
```

This will:
1. Extract all subtitle tracks from `movie.mkv`
2. Optimize each track with default settings
3. Save optimized subtitles as `movie.0.srt`, `movie.1.srt`, etc.

### Preview Changes (Dry Run)

See what would change without writing files:
```bash
subtuner movie.mkv --dry-run
```

### Batch Processing

Optimize multiple videos at once:
```bash
subtuner movie1.mkv movie2.mp4 series_s01e01.mkv
```

Or use wildcards (shell expansion):
```bash
subtuner *.mkv
```

## Usage Examples

### Adjust Reading Speed

For slower readers (15 chars/sec):
```bash
subtuner movie.mkv --chars-per-sec 15
```

For faster readers (25 chars/sec):
```bash
subtuner movie.mkv --chars-per-sec 25
```

### Custom Duration Constraints

Set minimum and maximum display times:
```bash
subtuner movie.mkv --min-duration 1.5 --max-duration 6.0
```

### Fine-tune Anticipation

Control how early subtitles appear:
```bash
subtuner movie.mkv --max-anticipation 0.3
```

Disable anticipation entirely:
```bash
subtuner movie.mkv --max-anticipation 0
```

### ASS Subtitle Adjustments

Adjust font size for dialog subtitles in ASS files:
```bash
# Increase font size by 2 points
subtuner subtitles.ass --ass-font-size-adjust 2

# Decrease font size by 2 points
subtuner subtitles.ass --ass-font-size-adjust -2
```

Adjust Y position (vertical positioning) for dialog subtitles:
```bash
# Move subtitles up by 100 pixels
subtuner subtitles.ass --ass-y-position-adjust -100

# Move subtitles down by 100 pixels
subtuner subtitles.ass --ass-y-position-adjust 100
```

Combine both adjustments:
```bash
subtuner anime.ass --ass-font-size-adjust 2 --ass-y-position-adjust -50
```

See [ASS_ADJUSTMENTS.md](ASS_ADJUSTMENTS.md) for detailed documentation.

### Disable Duplicate Merging

By default, SubTuner merges overlapping and identical subtitles. To disable this:
```bash
subtuner movie.mkv --no-merge-duplicates
```

### Adjust Rebalancing Thresholds

Define what counts as "short" and "long" subtitles:
```bash
subtuner movie.mkv --short-threshold 0.6 --long-threshold 4.0
```

### Custom Output Directory

Save optimized subtitles to a specific folder:
```bash
subtuner movie.mkv --output-dir ./optimized_subs/
```

### Verbose Output

See detailed processing information:
```bash
subtuner movie.mkv --verbose
```

### Quiet Mode

Suppress all output except errors:
```bash
subtuner movie.mkv --quiet
```

### Complete Example

Process a video with custom settings:
```bash
subtuner movie.mkv \
  --chars-per-sec 18 \
  --min-duration 1.2 \
  --max-duration 7.0 \
  --max-anticipation 0.4 \
  --output-dir ./subs/ \
  --verbose
```

## Command-Line Options

```
Usage: subtuner [OPTIONS] VIDEO_PATH [VIDEO_PATH...]

Arguments:
  VIDEO_PATH              Path to video file(s) to process

Options:
  --chars-per-sec FLOAT   Reading speed in characters per second
                          [default: 20.0, range: 10-40]
  
  --max-duration FLOAT    Maximum subtitle display duration in seconds
                          [default: 8.0, range: 3-15]
  
  --min-duration FLOAT    Minimum subtitle display duration in seconds
                          [default: 1.0, range: 0.5-2]
  
  --min-gap FLOAT         Minimum gap between consecutive subtitles
                          [default: 0.05, range: 0.01-0.2]
  
  --max-anticipation FLOAT
                          Maximum time (seconds) to start subtitles early
                          [default: 0.5, range: 0-1]
  
  --short-threshold FLOAT Threshold for "short" subtitle in seconds
                          [default: 0.8, range: 0.5-1.5]
  
  --long-threshold FLOAT  Threshold for "long" subtitle in seconds
                          [default: 3.0, range: 2-6]
  
  --merge-duplicates / --no-merge-duplicates
                          Merge overlapping and identical subtitles
                          [default: enabled]
  
  --ass-font-size-adjust INTEGER
                          Adjust font size for dialog subtitles in ASS format
                          (e.g., +2 or -2) [default: 0]
  
  --ass-y-position-adjust INTEGER
                          Adjust Y position for dialog subtitles in ASS format
                          (e.g., +100 or -100 pixels) [default: 0]
  
  --output-dir PATH       Output directory for optimized subtitles
                          [default: same as input file]
  
  --dry-run              Preview changes without writing files
  
  --verbose / --quiet     Control output verbosity
  
  --version              Show version and exit
  
  --help                 Show this message and exit
```

## Output Format

SubTuner saves optimized subtitles with this naming pattern:
```
{original_name}.{track_index}.{format}
```

Examples:
- `movie.mkv` with 2 subtitle tracks → `movie.0.srt`, `movie.1.srt`
- `episode.mp4` with 1 ASS track → `episode.0.ass`

Original format and styling are preserved.

## Statistics Report

After processing, SubTuner displays detailed statistics:

```
=== SubTuner Optimization Report ===

Video: movie.mkv
Processing Time: 3.45 seconds

Track 0 (English, SRT)
  Original Subtitles: 1,523
  Optimized Subtitles: 1,523
  
  Duration Adjustments: 847 (55.6%)
    Average Change: +0.34s
  
  Rebalanced Pairs: 23 (1.5%)
    Total Time Transferred: 5.8s
  
  Anticipated Subtitles: 156 (10.2%)
    Average Anticipation: 0.28s
  
  Validation Fixes: 5
    - Min Duration: 3
    - Min Gap: 2
  
  Total Modifications: 1,031 (67.7%)

Output: movie.0.srt (saved)
```

## Optimization Algorithms

SubTuner applies five complementary algorithms in sequence:

### 0. Subtitle Merging (Pre-processing)
Intelligently merges overlapping and identical subtitles:
- Detects identical text appearing in consecutive subtitles
- Merges subtitles that overlap significantly (>50% of shorter duration)
- Handles text continuations (when one subtitle continues another)
- Combines time ranges (earliest start, latest end)
- Preserves formatting and metadata from first subtitle

This phase runs before other optimizations to clean up duplicate content.

### 1. Duration Adjustment
Calculates optimal display time based on reading speed:
```
target_duration = character_count / chars_per_sec
```
Clamped to `[min_duration, max_duration]` and available time window.

### 2. Temporal Rebalancing
Transfers time from abnormally long subtitles to short ones:
- Detects short subtitle (<0.8s) followed by long one (>3s)
- Transfers surplus time to balance display durations
- Maintains minimum gap between subtitles

### 3. Conditional Anticipatory Offset
Starts subtitles earlier to increase reading time:
- Advances start time by up to 0.5s
- Only when it increases display duration
- Respects minimum gap with previous subtitle

### 4. Temporal Constraints Validation
Enforces hard constraints:
- Minimum display time: 1.0s
- Minimum gap: 0.05s
- No overlaps or reversed timestamps (except intentional overlaps preserved from original)
- Chronological order

See [ALGORITHMS.md](ALGORITHMS.md) for detailed specifications.

## Architecture

SubTuner is built with a modular architecture:

```
CLI → Video Analyzer → Subtitle Extractor → Parser → 
Optimization Engine → Writer → Statistics Reporter
```

Key components:
- **Video Analyzer**: FFprobe wrapper for metadata extraction
- **Subtitle Extractor**: FFmpeg-based track extraction
- **Parsers**: Format-specific subtitle parsing (SRT, VTT, ASS)
- **Optimization Engine**: Applies algorithms in sequence
- **Writers**: Format-specific subtitle writing with style preservation
- **Statistics Reporter**: Tracks and reports modifications

See [ARCHITECTURE.md](ARCHITECTURE.md) for complete design.

## Use Cases

### 1. Fast-Paced Dialogue
Anime or action movies with rapid dialogue benefit from anticipation and rebalancing:
```bash
subtuner anime.mkv --chars-per-sec 22 --max-anticipation 0.6
```

### 2. Educational Content
Slower reading speed for educational videos:
```bash
subtuner lecture.mp4 --chars-per-sec 15 --min-duration 1.5
```

### 3. Accessibility
Longer minimum durations for accessibility:
```bash
subtuner movie.mkv --min-duration 2.0 --max-anticipation 0
```

### 4. Documentary
Balanced settings for documentaries:
```bash
subtuner documentary.mkv --chars-per-sec 18 --long-threshold 5.0
```

### 5. ASS Subtitle Customization
Adjust font size and position for better readability on different screen sizes:
```bash
# For 4K displays - increase font size and move subtitles up
subtuner anime.mkv --ass-font-size-adjust 4 --ass-y-position-adjust -150

# For projectors - larger font and higher position
subtuner movie.mkv --ass-font-size-adjust 6 --ass-y-position-adjust -200

# Combined with optimization for slower reading
subtuner series.mkv --chars-per-sec 16 --ass-font-size-adjust 3 --ass-y-position-adjust -100
```

## Limitations

- **Text Subtitles Only**: Does not process image-based subtitles (PGS, VobSub)
- **External Subtitles**: Only processes embedded tracks (for external files, use directly)
- **No Re-muxing**: Does not embed optimized subtitles back into video
- **Single Language**: Uses same reading speed for all languages

## Troubleshooting

### FFmpeg Not Found
```
Error: FFmpeg/FFprobe not found in PATH
```
**Solution**: Install FFmpeg and ensure it's in your system PATH.

### No Subtitle Tracks Found
```
Warning: No text subtitle tracks found in video.mkv
```
**Solution**: Verify video has embedded text subtitles using a media player or MediaInfo.

### Permission Denied
```
Error: Permission denied writing to /path/
```
**Solution**: Ensure you have write permissions in the output directory.

### Encoding Errors
```
Error: Failed to parse subtitle file (encoding issue)
```
**Solution**: SubTuner attempts to handle various encodings automatically. File a bug report with the problematic file if issues persist.

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Development

### Setup Development Environment

```bash
git clone https://github.com/hcharbonnier/subtuner
cd subtuner

# Install with development dependencies
pip install -e ".[dev]"

# Or using Poetry
poetry install
```

### Run Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=subtuner --cov-report=html

# Run specific test file
pytest tests/test_algorithms.py
```

### Code Quality

```bash
# Format code
black subtuner/

# Lint
flake8 subtuner/

# Type checking
mypy subtuner/
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Click](https://click.palletsprojects.com/) for CLI
- Uses [pysrt](https://github.com/byroot/pysrt) for SRT parsing
- Uses [ass](https://github.com/chirlu/asslib) for ASS parsing
- Powered by [FFmpeg](https://ffmpeg.org/) for video processing

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.


## Related Projects

- [Subtitle Edit](https://www.nikse.dk/subtitleedit/) - GUI subtitle editor
- [ffsubsync](https://github.com/smacke/ffsubsync) - Automatic subtitle synchronization
- [subliminal](https://github.com/Diaoul/subliminal) - Subtitle download tool

---

**Made with ❤️ for subtitle enthusiasts**