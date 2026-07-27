# Quiz Project

Collection of self-contained HTML quiz files at `/home/ben/quiz/`.

## Directory structure

```
quiz/
├── index.html              # Landing page (links to quizzes/)
├── quizzes/                # All quiz HTML files
│   ├── breaking-bad.html
│   ├── europe.html
│   ├── eurovision.html
│   ├── harry-potter.html
│   ├── music.html
│   ├── pokemon.html
│   ├── world.html
│   └── sprites/            # Pokemon sprites + silhouettes
├── tools/                  # Audio tools, generators, data pipelines
│   ├── vocal_swap_tool.py  # CLI + server for stems database
│   ├── mixer.html          # Interactive vocal swap mixer UI
│   ├── generate_music_quiz.py
│   ├── generate_vocal_swap.py
│   ├── pokemon_data.py
│   └── stems_db/           # Generated stems (gitignored)
└── .claude/                # Skills, plans, memory
```

## Tech stack

- Each quiz is a **single `.html` file** with all CSS/JS inline — no build step, no bundler
- Network graph quizzes use **vis-network** from CDN: `https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/vis-network.min.js`
- Audio quiz uses **Web Audio API** (AudioContext, AudioBuffer, AudioBufferSourceNode) + pre-generated JSON data
- Python scripts in `tools/` generate data (e.g. `generate_music_quiz.py` outputs `music_quiz_data.json`)
- Dark theme throughout — backgrounds: `#0d1117` or `#1a1a2e`, accent colors vary per quiz
- To serve quizzes: `python3 -m http.server` from root directory
- To serve mixer: `python3 tools/vocal_swap_tool.py serve` (port 8765)

## Quiz types

| File | Format | Topic |
|------|--------|-------|
| `quizzes/breaking-bad.html` | Network graph | Breaking Bad characters |
| `quizzes/europe.html` | Network graph | European country borders |
| `quizzes/world.html` | Network graph | World country borders (area sizing, border-length edges) |
| `quizzes/pokemon.html` | Network graph | Pokémon |
| `quizzes/harry-potter.html` | Network graph | Harry Potter characters |
| `quizzes/eurovision.html` | Network graph | Eurovision |
| `quizzes/music.html` | Audio mashup | Song recognition from pitch-scrambled mashups |

## Tools

- `tools/vocal_swap_tool.py` — CLI + local server for vocal swap mixing
  - `search <query>` — search iTunes
  - `add <query>` — download, demucs separation, beat detection
  - `list` — show stems database
  - `serve [port]` — start local server with API + mixer UI
- `tools/mixer.html` — Browser-based mixer (search, waveforms, offset, speed, export)
- `tools/generate_music_quiz.py` — generates pitch-scramble quiz data
- `tools/generate_vocal_swap.py` — standalone vocal swap pipeline

## Data generation

- `generate_music_quiz.py` — fetches iTunes 30s previews, converts m4a→WAV via ffmpeg (`imageio_ffmpeg`), runs scipy DSP (beat detection, spectral centroid), outputs segment timestamps + sort order
- Python deps: `numpy`, `scipy`, `requests`, `imageio-ffmpeg` (provides bundled ffmpeg binary)
- Mixer deps: `demucs`, `librosa`, `soundfile`, `torch`
- ffmpeg path: `imageio_ffmpeg.get_ffmpeg_exe()`

## Conventions

- All data is inline in the HTML or in a companion `.json` file — no external databases
- Game state managed in a simple object (sets for revealed/guessed, selected node, attempts counter)
- Fuzzy matching for text guesses (normalize, substring, word-overlap threshold)
- Quizzes are designed to work offline once loaded (all assets from CDN or inline)
