# SubTuner - Project Setup Guide

This document provides detailed setup instructions and configuration specifications for the SubTuner project.

## Project Configuration

### pyproject.toml

```toml
[tool.poetry]
name = "subtuner"
version = "0.1.0"
description = "Python CLI tool for optimizing embedded video subtitles"
authors = ["Your Name <your.email@example.com>"]
license = "MIT"
readme = "README.md"
homepage = "https://github.com/yourusername/subtuner"
repository = "https://github.com/yourusername/subtuner"
keywords = ["subtitles", "video", "optimization", "cli"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: End Users/Desktop",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Multimedia :: Video",
    "Topic :: Text Processing",
]

[tool.poetry.dependencies]
python = "^3.8"
click = "^8.1.7"
pysrt = "^1.1.2"
webvtt-py = "^0.5.0"
ass = "^0.5.2"
chardet = "^5.2.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.3"
pytest-cov = "^4.1.0"
black = "^23.12.1"
mypy = "^1.7.1"
flake8 = "^6.1.0"
isort = "^5.13.2"
pylint = "^3.0.3"

[tool.poetry.scripts]
subtuner = "subtuner.cli:main"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.black]
line-length = 100
target-version = ['py38']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
ignore_missing_imports = true

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --strict-markers --cov=subtuner --cov-report=term-missing"
testpaths = ["tests"]
pythonpath = ["."]

[tool.coverage.run]
source = ["subtuner"]
omit = ["tests/*", "**/__pycache__/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

### requirements.txt

```txt
click>=8.1.7
pysrt>=1.1.2
webvtt-py>=0.5.0
ass>=0.5.2
chardet>=5.2.0
```

### requirements-dev.txt

```txt
-r requirements.txt
pytest>=7.4.3
pytest-cov>=4.1.0
black>=23.12.1
mypy>=1.7.1
flake8>=6.1.0
isort>=5.13.2
pylint>=3.0.3
```

### setup.py (for pip install)

```python
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="subtuner",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Python CLI tool for optimizing embedded video subtitles",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/subtuner",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Video",
        "Topic :: Text Processing",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.1.7",
        "pysrt>=1.1.2",
        "webvtt-py>=0.5.0",
        "ass>=0.5.2",
        "chardet>=5.2.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-cov>=4.1.0",
            "black>=23.12.1",
            "mypy>=1.7.1",
            "flake8>=6.1.0",
            "isort>=5.13.2",
            "pylint>=3.0.3",
        ],
    },
    entry_points={
        "console_scripts": [
            "subtuner=subtuner.cli:main",
        ],
    },
)
```

## Directory Structure

Create the following directory structure:

```
subtuner/
├── subtuner/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── errors.py
│   ├── config.py
│   │
│   ├── video/
│   │   ├── __init__.py
│   │   └── analyzer.py
│   │
│   ├── extraction/
│   │   ├── __init__.py
│   │   └── extractor.py
│   │
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── srt_parser.py
│   │   ├── vtt_parser.py
│   │   └── ass_parser.py
│   │
│   ├── optimization/
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   ├── config.py
│   │   └── algorithms/
│   │       ├── __init__.py
│   │       ├── duration_adjuster.py
│   │       ├── rebalancer.py
│   │       ├── anticipator.py
│   │       └── validator.py
│   │
│   ├── writers/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── srt_writer.py
│   │   ├── vtt_writer.py
│   │   └── ass_writer.py
│   │
│   ├── statistics/
│   │   ├── __init__.py
│   │   └── reporter.py
│   │
│   └── batch/
│       ├── __init__.py
│       └── processor.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_parsers.py
│   ├── test_optimization.py
│   ├── test_algorithms.py
│   ├── test_writers.py
│   ├── test_cli.py
│   ├── test_integration.py
│   └── fixtures/
│       ├── sample.srt
│       ├── sample.vtt
│       ├── sample.ass
│       └── test_video.mkv
│
├── docs/
│   ├── README.md
│   ├── USAGE.md
│   └── API.md
│
├── .gitignore
├── .flake8
├── pyproject.toml
├── setup.py
├── requirements.txt
├── requirements-dev.txt
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── ARCHITECTURE.md
├── ALGORITHMS.md
└── README.md
```

## Setup Instructions

### 1. Initial Setup

```bash
# Clone or initialize repository
git clone https://github.com/yourusername/subtuner.git
cd subtuner

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Unix/macOS:
source venv/bin/activate
```

### 2. Install Dependencies

**Using Poetry (recommended):**
```bash
# Install Poetry if not already installed
pip install poetry

# Install dependencies
poetry install

# Activate poetry shell
poetry shell
```

**Using pip:**
```bash
# Install in editable mode
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

### 3. Verify FFmpeg Installation

```bash
# Check FFmpeg
ffmpeg -version

# Check FFprobe
ffprobe -version
```

If not installed, follow the installation instructions in README.md.

### 4. Create Initial Files

**Create `.gitignore`:**
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# OS
.DS_Store
Thumbs.db

# Project specific
*.mkv
*.mp4
*.avi
*.srt
*.vtt
*.ass
*.ssa
!tests/fixtures/*.srt
!tests/fixtures/*.vtt
!tests/fixtures/*.ass
```

**Create `.flake8`:**
```ini
[flake8]
max-line-length = 100
extend-ignore = E203, E501, W503
exclude =
    .git,
    __pycache__,
    build,
    dist,
    .eggs,
    *.egg-info,
    .venv,
    venv
```

**Create `LICENSE`:**
```
MIT License

Copyright (c) 2024 Your Name

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Development Workflow

### 1. Code Style

```bash
# Format code with black
black subtuner/

# Sort imports
isort subtuner/

# Lint with flake8
flake8 subtuner/

# Type check with mypy
mypy subtuner/

# Lint with pylint
pylint subtuner/
```

### 2. Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=subtuner --cov-report=html

# Run specific test file
pytest tests/test_algorithms.py

# Run specific test
pytest tests/test_algorithms.py::test_duration_adjustment

# Run with verbose output
pytest -v

# Run only failed tests from last run
pytest --lf
```

### 3. Continuous Integration

**GitHub Actions workflow (`.github/workflows/ci.yml`):**
```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install FFmpeg
      uses: FedericoCarboni/setup-ffmpeg@v2
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    
    - name: Lint with flake8
      run: |
        flake8 subtuner/
    
    - name: Type check with mypy
      run: |
        mypy subtuner/
    
    - name: Test with pytest
      run: |
        pytest --cov=subtuner --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## Package Building

### Build for Distribution

```bash
# Using Poetry
poetry build

# Using setuptools
python setup.py sdist bdist_wheel
```

### Install Locally

```bash
# From wheel
pip install dist/subtuner-0.1.0-py3-none-any.whl

# From source distribution
pip install dist/subtuner-0.1.0.tar.gz
```

### Publish to PyPI

```bash
# Using Poetry
poetry publish --build

# Using twine
pip install twine
python setup.py sdist bdist_wheel
twine upload dist/*
```

## Environment Variables

SubTuner supports these environment variables:

```bash
# Override FFmpeg path
export SUBTUNER_FFMPEG_PATH=/custom/path/to/ffmpeg
export SUBTUNER_FFPROBE_PATH=/custom/path/to/ffprobe

# Set default log level
export SUBTUNER_LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR

# Set temporary directory
export SUBTUNER_TEMP_DIR=/custom/temp/dir
```

## Docker Support (Optional)

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

# Install FFmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -e .

# Set entry point
ENTRYPOINT ["subtuner"]
CMD ["--help"]
```

**Build and run:**
```bash
# Build image
docker build -t subtuner .

# Run
docker run -v $(pwd):/data subtuner /data/movie.mkv
```

## Troubleshooting Setup

### Issue: FFmpeg not found

**Solution:**
```bash
# Verify installation
which ffmpeg
which ffprobe

# Add to PATH if needed
export PATH=$PATH:/path/to/ffmpeg/bin
```

### Issue: Module import errors

**Solution:**
```bash
# Reinstall in editable mode
pip uninstall subtuner
pip install -e .

# Or use PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue: Poetry lock file issues

**Solution:**
```bash
# Update lock file
poetry lock --no-update

# Or recreate from scratch
rm poetry.lock
poetry install
```

## Next Steps

After completing the setup:

1. **Implement Core Modules**: Start with [`video/analyzer.py`](video/analyzer.py)
2. **Write Tests**: Create tests alongside implementation
3. **Run Code Quality Checks**: Use black, flake8, mypy regularly
4. **Update Documentation**: Keep README and ARCHITECTURE in sync
5. **Create Sample Fixtures**: Add test subtitle files in [`tests/fixtures/`](tests/fixtures/)

## Useful Commands Reference

```bash
# Development
poetry run subtuner --help          # Run CLI
poetry run pytest                   # Run tests
poetry run black subtuner/          # Format code
poetry run mypy subtuner/           # Type check

# Package management
poetry add <package>                # Add dependency
poetry add --group dev <package>    # Add dev dependency
poetry update                       # Update dependencies
poetry show                         # List dependencies

# Git workflow
git checkout -b feature/your-feature
git add .
git commit -m "feat: your feature"
git push origin feature/your-feature
```

## Resources

- **Poetry Documentation**: https://python-poetry.org/docs/
- **Click Documentation**: https://click.palletsprojects.com/
- **pytest Documentation**: https://docs.pytest.org/
- **FFmpeg Documentation**: https://ffmpeg.org/documentation.html
- **PEP 8 Style Guide**: https://peps.python.org/pep-0008/

---

This setup guide ensures a consistent development environment across all contributors and platforms.