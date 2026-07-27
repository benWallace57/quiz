---
name: audio-quiz
description: Reference patterns for creating audio-based quizzes (pitch scrambles, mashups, sound recognition). Use when building any quiz involving audio playback, song recognition, or audio manipulation.
when_to_use: audio quiz, music quiz, song quiz, mashup, pitch scramble, sound recognition, Web Audio API
user-invocable: true
---

# Audio Quiz Pattern

## Architecture

```
Python generator script
  → fetch audio (iTunes 30s previews)
  → convert m4a → WAV (ffmpeg via imageio_ffmpeg)
  → DSP: beat detection + spectral analysis (scipy)
  → output JSON with segment timestamps + sort order

HTML player
  → fetch audio URL from JSON
  → decode with Web Audio API
  → slice AudioBuffer at pre-computed timestamps
  → concatenate segments in scrambled order
  → play with pause/resume support
```

## Python Generation Pipeline

### iTunes Preview API
```python
requests.get("https://itunes.apple.com/search", params={
    "term": "artist song", "entity": "song", "limit": 1
})
# Returns 30-second m4a preview URL (CORS open, no auth needed)
```

### m4a → WAV conversion
```python
import imageio_ffmpeg
ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
subprocess.run([ffmpeg, "-y", "-i", input_m4a, "-ar", "44100", "-ac", "1", "-f", "wav", output_wav])
```

### Beat Detection (spectral flux)
```python
f, t, Zxx = scipy.signal.stft(data, fs=sr, nperseg=2048, noverlap=1536)
mag = np.abs(Zxx)
flux = np.sum(np.maximum(0, np.diff(mag, axis=1)), axis=0)
peaks, _ = scipy.signal.find_peaks(flux, distance=min_distance, prominence=np.median(flux) * 1.5)
```

### Spectral Centroid (sorting metric)
```python
fft_mag = np.abs(np.fft.rfft(segment))
freqs = np.fft.rfftfreq(len(segment), 1.0 / sr)
centroid = np.sum(freqs * fft_mag) / np.sum(fft_mag)
```

**Why spectral centroid, not YIN pitch:**
- YIN latches onto bass fundamentals (~60Hz), giving nearly identical values across segments
- Spectral centroid measures "brightness" — gives wide spread (2000-7000Hz range)
- Better scrambling: high-centroid segments (cymbals, vocals) sort away from low-centroid (bass, drums)

### Force-splitting long segments
```python
def force_split_segments(beats, max_len=1.0, min_len=0.3):
    # Split any segment > max_len into equal sub-segments
    # Merge any segment < min_len with next
```

### Chorus Window Finding
```python
def find_chorus_window(data, sr, window_sec=10):
    # Compute energy in 0.5s chunks
    # Slide window to find highest-energy region
    # Return start_sample, end_sample
```

## JSON Output Format

```json
{
  "mashups": [
    {
      "id": 1,
      "label": "Mashup 1",
      "songs": [
        {
          "answer": "Song Title",
          "artist": "Artist Name",
          "previewUrl": "https://audio-ssl.itunes.apple.com/...",
          "segments": [3.5, 4.1, 4.7, ...],  // timestamps in seconds (absolute)
          "order": [5, 2, 8, 0, ...]           // segment indices sorted by centroid
        }
      ]
    }
  ]
}
```

## HTML Player — Key Patterns

### Building Scrambled Buffer
```javascript
function buildScrambledBuffer(buffer, segments, order) {
  const sr = buffer.sampleRate;
  // For each index in order: extract segment from AudioBuffer, concatenate
  for (const idx of order) {
    const startSample = Math.floor(segments[idx] * sr);
    const endSample = Math.floor(segments[idx + 1] * sr);
    // Copy channel data to output buffer at writePos
  }
}
```

### Mashup Building (interleave round-robin)
```javascript
function buildMashup(buffers, songs) {
  // Get segment queues for each song (in scrambled order)
  // Interleave: take 1 segment from each song in round-robin
  // Stop at maxDuration (e.g. 10 seconds)
}
```

### Pause/Resume Pattern

**Critical:** `AudioBufferSourceNode.onended` fires when `.stop()` is called (including pause). Must set `isPlaying = false` BEFORE calling `.stop()` so `onended` doesn't clear `pauseOffset`.

```javascript
let isPlaying = false;
let pauseOffset = 0;
let playStartTime = 0;

function playBuffer(buffer, offset) {
  currentSource = audioCtx.createBufferSource();
  currentSource.buffer = buffer;
  currentSource.connect(audioCtx.destination);
  currentSource.start(0, offset || 0);
  playStartTime = audioCtx.currentTime - (offset || 0);
  isPlaying = true;
  currentSource.onended = () => {
    if (isPlaying) {  // Only reset if natural end, not pause
      isPlaying = false;
      pauseOffset = 0;
    }
  };
}

function pausePlayback() {
  if (currentSource && isPlaying) {
    isPlaying = false;  // Set BEFORE .stop() to prevent onended from clearing offset
    pauseOffset = audioCtx.currentTime - playStartTime;
    currentSource.stop();
    currentSource = null;
  }
}

function togglePlay() {
  if (audioCtx.state === 'suspended') audioCtx.resume();
  if (isPlaying) pausePlayback();
  else playBuffer(scrambledBuffer, pauseOffset);
}
```

### Fuzzy Matching for Song Guesses
```javascript
function fuzzyMatch(guess, answer) {
  const normalize = s => s.toLowerCase().replace(/[^a-z0-9\s]/g, '').trim();
  // Exact match, substring (>3 chars), or 60%+ word overlap
}
```

## UI Pattern

- Play/pause button: large circle, toggles ▶ / ⏸
- Guess input: text field with Enter to submit
- Progress: count of songs guessed (e.g. "2/3")
- Reveal area: shows all answers on give-up or completion
- Question selector sidebar: numbered buttons to jump between questions

## Mashup Quiz Mechanics

- Each question = N songs (typically 3) spliced together
- Segments interleaved round-robin in pitch-scrambled order
- Cap total duration at ~10 seconds per question
- Player guesses each song — partial credit shown (e.g. "Got it! Song X (2/3)")
- All N correct = question passed
