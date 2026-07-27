# Quiz Project

Collection of self-contained HTML quiz files at `/home/ben/quiz/`.

## Tech stack

- Each quiz is a **single `.html` file** with all CSS/JS inline — no build step, no bundler
- Network graph quizzes use **vis-network** from CDN: `https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/vis-network.min.js`
- Audio quiz uses **Web Audio API** (AudioContext, AudioBuffer, AudioBufferSourceNode) + pre-generated JSON data
- Python scripts in this directory generate data (e.g. `generate_music_quiz.py` outputs `music_quiz_data.json`)
- Dark theme throughout — backgrounds: `#0d1117` or `#1a1a2e`, accent colors vary per quiz
- To serve: `python3 -m http.server` from this directory, then open in browser

## Quiz types

| File | Format | Topic |
|------|--------|-------|
| `index.html` | Network graph | Breaking Bad characters |
| `europe.html` | Network graph | European country borders |
| `world.html` | Network graph | World country borders (area sizing, border-length edges) |
| `pokemon.html` | Network graph | Pokémon |
| `harry-potter.html` | Network graph | Harry Potter characters |
| `eurovision.html` | Network graph | Eurovision |
| `music.html` | Audio mashup | Song recognition from pitch-scrambled mashups |

## Data generation

- `generate_music_quiz.py` — fetches iTunes 30s previews, converts m4a→WAV via ffmpeg (`imageio_ffmpeg`), runs scipy DSP (beat detection, spectral centroid), outputs segment timestamps + sort order
- Python deps: `numpy`, `scipy`, `requests`, `imageio-ffmpeg` (provides bundled ffmpeg binary)
- ffmpeg path: `imageio_ffmpeg.get_ffmpeg_exe()`

## Conventions

- All data is inline in the HTML or in a companion `.json` file — no external databases
- Game state managed in a simple object (sets for revealed/guessed, selected node, attempts counter)
- Fuzzy matching for text guesses (normalize, substring, word-overlap threshold)
- Quizzes are designed to work offline once loaded (all assets from CDN or inline)
