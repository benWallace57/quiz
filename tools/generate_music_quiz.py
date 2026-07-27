#!/usr/bin/env python3
"""
Generate music quiz data: 5 mashup questions, each interleaving 3 songs.
Fetch iTunes previews, run beat detection + spectral centroid analysis,
output pre-computed segment data for the HTML player.
"""

import json
import os
import subprocess
import tempfile
import time

import numpy as np
import requests
import scipy.io.wavfile as wavfile
import scipy.signal

FFMPEG = None

def get_ffmpeg():
    global FFMPEG
    if FFMPEG is None:
        import imageio_ffmpeg
        FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
    return FFMPEG


MASHUPS = [
    {
        "label": "Mashup 1",
        "songs": [
            {"term": "kenny loggins footloose", "answer": "Footloose", "artist": "Kenny Loggins"},
            {"term": "cyndi lauper girls just want to have fun", "answer": "Girls Just Want to Have Fun", "artist": "Cyndi Lauper"},
            {"term": "wham wake me up before you go go", "answer": "Wake Me Up Before You Go-Go", "artist": "Wham!"},
        ],
    },
    {
        "label": "Mashup 2",
        "songs": [
            {"term": "queen we will rock you", "answer": "We Will Rock You", "artist": "Queen"},
            {"term": "ac dc back in black", "answer": "Back in Black", "artist": "AC/DC"},
            {"term": "bon jovi livin on a prayer", "answer": "Livin' on a Prayer", "artist": "Bon Jovi"},
        ],
    },
    {
        "label": "Mashup 3",
        "songs": [
            {"term": "whitney houston i wanna dance with somebody", "answer": "I Wanna Dance with Somebody", "artist": "Whitney Houston"},
            {"term": "madonna like a prayer", "answer": "Like a Prayer", "artist": "Madonna"},
            {"term": "michael jackson thriller", "answer": "Thriller", "artist": "Michael Jackson"},
        ],
    },
    {
        "label": "Mashup 4",
        "songs": [
            {"term": "queen dont stop me now", "answer": "Don't Stop Me Now", "artist": "Queen"},
            {"term": "earth wind fire september", "answer": "September", "artist": "Earth, Wind & Fire"},
            {"term": "stevie wonder superstition", "answer": "Superstition", "artist": "Stevie Wonder"},
        ],
    },
    {
        "label": "Mashup 5",
        "songs": [
            {"term": "beyonce crazy in love", "answer": "Crazy in Love", "artist": "Beyonce"},
            {"term": "outkast hey ya", "answer": "Hey Ya!", "artist": "Outkast"},
            {"term": "kelly clarkson since u been gone", "answer": "Since U Been Gone", "artist": "Kelly Clarkson"},
        ],
    },
]


def fetch_itunes_preview(term):
    r = requests.get("https://itunes.apple.com/search", params={
        "term": term, "entity": "song", "limit": 1,
    })
    r.raise_for_status()
    data = r.json()
    if not data["results"]:
        return None
    result = data["results"][0]
    return {
        "previewUrl": result.get("previewUrl"),
        "trackName": result.get("trackName"),
        "artistName": result.get("artistName"),
    }


def download_and_convert(url, out_wav_path):
    """Download m4a from URL and convert to mono 44.1kHz WAV."""
    r = requests.get(url)
    r.raise_for_status()

    with tempfile.NamedTemporaryFile(suffix=".m4a", delete=False) as f:
        f.write(r.content)
        m4a_path = f.name

    try:
        subprocess.run([
            get_ffmpeg(), "-y", "-i", m4a_path,
            "-ar", "44100", "-ac", "1", "-f", "wav", out_wav_path,
        ], capture_output=True, check=True)
    finally:
        os.unlink(m4a_path)


def detect_beats(data, sr):
    """Detect beat/onset timestamps using spectral flux."""
    f, t, Zxx = scipy.signal.stft(data, fs=sr, nperseg=2048, noverlap=1536)
    mag = np.abs(Zxx)

    flux = np.sum(np.maximum(0, np.diff(mag, axis=1)), axis=0)

    min_distance = int(0.3 * sr / 512)
    prominence = np.median(flux) * 1.5

    peaks, _ = scipy.signal.find_peaks(flux, distance=min_distance, prominence=prominence)

    beat_times = t[peaks + 1] if len(peaks) > 0 else np.array([])

    beats = [0.0]
    for bt in beat_times:
        if bt - beats[-1] >= 0.25:
            beats.append(float(bt))

    duration = len(data) / sr
    if duration - beats[-1] > 0.1:
        beats.append(duration)

    return beats


def force_split_segments(beats, max_len=1.0, min_len=0.3):
    """Force-split any segment longer than max_len into equal sub-segments."""
    result = [beats[0]]
    for i in range(1, len(beats)):
        seg_len = beats[i] - result[-1]
        if seg_len > max_len:
            n_splits = int(np.ceil(seg_len / max_len))
            sub_len = seg_len / n_splits
            for j in range(1, n_splits):
                result.append(result[-1] + sub_len)
        result.append(beats[i])

    final = [result[0]]
    for i in range(1, len(result)):
        if result[i] - final[-1] >= min_len or i == len(result) - 1:
            final.append(result[i])
    return final


def find_chorus_window(data, sr, window_sec=10):
    """Find the most energetic window (likely the chorus)."""
    window_samples = int(window_sec * sr)
    if len(data) <= window_samples:
        return 0, len(data)

    chunk = int(sr * 0.5)
    energies = []
    for i in range(0, len(data) - chunk, chunk):
        energies.append(np.sum(data[i:i+chunk] ** 2))

    win_chunks = int(window_sec / 0.5)
    best_start = 0
    best_energy = 0
    for i in range(len(energies) - win_chunks):
        e = sum(energies[i:i+win_chunks])
        if e > best_energy:
            best_energy = e
            best_start = i

    start_sample = best_start * chunk
    end_sample = min(start_sample + window_samples, len(data))
    return start_sample, end_sample


def analyze_track(wav_path):
    """Run full analysis: beat detection, spectral centroid sort."""
    sr, data = wavfile.read(wav_path)
    data = data.astype(np.float32) / 32768.0

    chorus_start, chorus_end = find_chorus_window(data, sr, window_sec=10)
    data = data[chorus_start:chorus_end]
    chorus_offset = chorus_start / sr
    print(f"    Duration: {len(data)/sr:.2f}s (from {chorus_offset:.1f}s), SR: {sr}")

    beats = detect_beats(data, sr)
    print(f"    Raw beats: {len(beats) - 1} segments")

    beats = force_split_segments(beats, max_len=1.0, min_len=0.3)
    num_segments = len(beats) - 1
    print(f"    After splitting: {num_segments} segments")

    pitches = []
    for i in range(num_segments):
        start_sample = int(beats[i] * sr)
        end_sample = int(beats[i + 1] * sr)
        segment = data[start_sample:end_sample]
        fft_mag = np.abs(np.fft.rfft(segment))
        freqs = np.fft.rfftfreq(len(segment), 1.0 / sr)
        if np.sum(fft_mag) > 0:
            pitch = float(np.sum(freqs * fft_mag) / np.sum(fft_mag))
        else:
            pitch = 0.0
        pitches.append(pitch)

    indexed = [(i, p) for i, p in enumerate(pitches)]
    indexed.sort(key=lambda x: -x[1])
    order = [i for i, _ in indexed]

    segments = [round(b + chorus_offset, 4) for b in beats]

    pitched = [p for p in pitches if p > 0]
    if pitched:
        print(f"    Pitch range: {min(pitched):.0f}Hz - {max(pitched):.0f}Hz")

    return segments, order


def main():
    output = {"mashups": []}

    with tempfile.TemporaryDirectory() as tmpdir:
        for mi, mashup in enumerate(MASHUPS):
            print(f"\n{'='*60}")
            print(f"[Mashup {mi+1}/5] {mashup['label']}")
            print(f"{'='*60}")

            mashup_data = {
                "id": mi + 1,
                "label": mashup["label"],
                "songs": [],
            }

            for si, song in enumerate(mashup["songs"]):
                print(f"\n  [{si+1}/3] {song['artist']} - {song['answer']}")

                print("    Fetching iTunes metadata...")
                result = fetch_itunes_preview(song["term"])
                if not result or not result["previewUrl"]:
                    print("    FAILED - no preview URL")
                    continue

                wav_path = os.path.join(tmpdir, f"mashup_{mi}_song_{si}.wav")
                print(f"    Downloading & converting to WAV...")
                download_and_convert(result["previewUrl"], wav_path)

                print("    Analyzing...")
                segments, order = analyze_track(wav_path)

                mashup_data["songs"].append({
                    "answer": song["answer"],
                    "artist": song["artist"],
                    "previewUrl": result["previewUrl"],
                    "segments": segments,
                    "order": order,
                })

                time.sleep(0.3)

            output["mashups"].append(mashup_data)

    with open("music_quiz_data.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nWrote music_quiz_data.json with {len(output['mashups'])} mashups.")


if __name__ == "__main__":
    main()
