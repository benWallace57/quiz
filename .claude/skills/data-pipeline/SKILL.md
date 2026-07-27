---
name: data-pipeline
description: Patterns for Python data generation scripts — API fetching, audio processing, data cleaning.
paths: ["generate_*.py", "**/*_generator.py", "**/*_data.py"]
user-invocable: true
---

# Data Pipeline Patterns

This skill auto-loads when editing Python data generation scripts.

## Standard Pipeline Structure

```python
# 1. Fetch raw data (API or file)
# 2. Transform/clean
# 3. Build relationships (edges for network quizzes)
# 4. Output JSON (inline-ready or companion file)
```

## API Catalog

See `${CLAUDE_SKILL_DIR}/references/api-catalog.md` for known data sources.

## Audio Pipeline (scipy + ffmpeg)

```python
import numpy as np
from scipy.io import wavfile
from scipy.signal import stft, find_peaks
import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
```

Key operations:
- **Download**: `requests.get(url).content` → save as `.m4a`
- **Convert**: `subprocess.run([FFMPEG, '-i', input, '-ar', '44100', '-ac', '1', output])`
- **Beat detection**: STFT spectral flux + `find_peaks(flux, distance=min_gap)`
- **Spectral centroid**: `np.sum(freqs * magnitudes) / np.sum(magnitudes)` per frame
- **Segment splitting**: Force-split segments longer than 1.0s at midpoints

## Network Data Pipeline

```python
import json

# Output format for network quizzes:
output = {
    "nodes": [{"id": 1, "name": "...", "weight": 10, "community": 0, "aliases": []}],
    "edges": [{"source": 1, "target": 2, "weight": 5}]
}

# Inline into HTML:
html_template.replace('// DATA_PLACEHOLDER', f'const DATA = {json.dumps(output)};')
```

## Common Pitfalls

- iTunes previews expire after ~24h — download and cache locally
- Always use `imageio_ffmpeg.get_ffmpeg_exe()` not system ffmpeg
- Normalize weights to avoid vis-network rendering issues (sqrt scaling)
- Rate-limit API calls (add `time.sleep(0.5)` between requests)