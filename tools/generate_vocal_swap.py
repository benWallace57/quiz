"""
Vocal Swap Generator

Takes two songs, extracts vocals from one and instrumental from the other,
matches their BPMs via time-stretching, and mixes them together.

Example: Beyoncé's vocals from "Crazy in Love" over Michael Jackson's
"Billie Jean" instrumental.

Dependencies: demucs, librosa, numpy, scipy, requests, imageio-ffmpeg
"""

import os
import sys
import tempfile
import subprocess
import requests
import numpy as np
import librosa
import soundfile as sf

SAMPLE_RATE = 44100
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "vocal_swaps")


def get_ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"


def fetch_itunes_preview(term):
    """Search iTunes for a song and return preview URL + metadata."""
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
    """Download m4a preview and convert to stereo 44.1kHz WAV."""
    r = requests.get(url)
    r.raise_for_status()

    with tempfile.NamedTemporaryFile(suffix=".m4a", delete=False) as f:
        f.write(r.content)
        m4a_path = f.name

    try:
        subprocess.run([
            get_ffmpeg(), "-y", "-i", m4a_path,
            "-ar", str(SAMPLE_RATE), "-ac", "2", "-f", "wav", out_wav_path,
        ], capture_output=True, check=True)
    finally:
        os.unlink(m4a_path)


def separate_stems(wav_path, output_dir):
    """Run demucs to separate vocals and instrumental stems."""
    import demucs.separate

    demucs.separate.main([
        "--two-stems", "vocals",
        "-n", "htdemucs",
        "--out", output_dir,
        wav_path,
    ])

    basename = os.path.splitext(os.path.basename(wav_path))[0]
    stems_dir = os.path.join(output_dir, "htdemucs", basename)

    vocals_path = os.path.join(stems_dir, "vocals.wav")
    no_vocals_path = os.path.join(stems_dir, "no_vocals.wav")

    return vocals_path, no_vocals_path


def detect_bpm(wav_path):
    """Detect BPM using librosa."""
    y, sr = librosa.load(wav_path, sr=SAMPLE_RATE, mono=True)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    if hasattr(tempo, '__len__'):
        tempo = tempo[0]
    return float(tempo)


def time_stretch_audio(wav_path, rate):
    """Time-stretch audio by the given rate (>1 = faster, <1 = slower)."""
    y, sr = librosa.load(wav_path, sr=SAMPLE_RATE, mono=False)

    if y.ndim == 1:
        stretched = librosa.effects.time_stretch(y, rate=rate)
    else:
        # Stretch each channel independently
        stretched = np.array([
            librosa.effects.time_stretch(y[ch], rate=rate)
            for ch in range(y.shape[0])
        ])

    return stretched, sr


def mix_audio(vocals, instrumental, vocal_gain=0.75, inst_gain=0.85):
    """Mix vocals and instrumental together with gain balancing."""
    # Make mono if needed for comparison, but keep stereo for output
    if vocals.ndim == 1:
        vocals = np.array([vocals, vocals])
    if instrumental.ndim == 1:
        instrumental = np.array([instrumental, instrumental])

    # Trim to shortest length
    min_len = min(vocals.shape[1], instrumental.shape[1])
    vocals = vocals[:, :min_len]
    instrumental = instrumental[:, :min_len]

    # Mix with gains
    mixed = instrumental * inst_gain + vocals * vocal_gain

    # Normalize to prevent clipping
    peak = np.max(np.abs(mixed))
    if peak > 0.95:
        mixed = mixed * (0.95 / peak)

    return mixed


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # --- Configuration ---
    vocal_song = "Crazy in Love Beyonce"
    instrumental_song = "Billie Jean Michael Jackson"

    print(f"=== Vocal Swap Generator ===")
    print(f"Vocals from: {vocal_song}")
    print(f"Instrumental from: {instrumental_song}")
    print()

    # --- Step 1: Fetch previews ---
    print("1. Fetching iTunes previews...")
    vocal_info = fetch_itunes_preview(vocal_song)
    inst_info = fetch_itunes_preview(instrumental_song)

    if not vocal_info or not vocal_info["previewUrl"]:
        sys.exit(f"Could not find preview for: {vocal_song}")
    if not inst_info or not inst_info["previewUrl"]:
        sys.exit(f"Could not find preview for: {instrumental_song}")

    print(f"   Vocal source: {vocal_info['trackName']} - {vocal_info['artistName']}")
    print(f"   Inst source:  {inst_info['trackName']} - {inst_info['artistName']}")

    # --- Step 2: Download and convert ---
    print("\n2. Downloading and converting to WAV...")
    vocal_wav = os.path.join(OUTPUT_DIR, "source_vocal.wav")
    inst_wav = os.path.join(OUTPUT_DIR, "source_instrumental.wav")

    download_and_convert(vocal_info["previewUrl"], vocal_wav)
    download_and_convert(inst_info["previewUrl"], inst_wav)
    print("   Done.")

    # --- Step 3: Separate stems ---
    print("\n3. Separating stems with demucs (this may take 30-60s on CPU)...")
    stems_dir = os.path.join(OUTPUT_DIR, "stems")
    os.makedirs(stems_dir, exist_ok=True)

    vocals_path, _ = separate_stems(vocal_wav, stems_dir)
    _, no_vocals_path = separate_stems(inst_wav, stems_dir)

    print(f"   Vocals extracted: {vocals_path}")
    print(f"   Instrumental extracted: {no_vocals_path}")

    # --- Step 4: Detect BPMs ---
    print("\n4. Detecting BPMs...")
    vocal_bpm = detect_bpm(vocal_wav)
    inst_bpm = detect_bpm(inst_wav)
    print(f"   Vocal source BPM: {vocal_bpm:.1f}")
    print(f"   Instrumental BPM: {inst_bpm:.1f}")

    # --- Step 5: Time-stretch vocals to match instrumental ---
    stretch_rate = inst_bpm / vocal_bpm
    print(f"\n5. Time-stretching vocals by {stretch_rate:.3f}x to match instrumental...")

    vocals_stretched, sr = time_stretch_audio(vocals_path, stretch_rate)
    print("   Done.")

    # --- Step 6: Load instrumental and mix ---
    print("\n6. Mixing vocals with instrumental...")
    instrumental, _ = librosa.load(no_vocals_path, sr=SAMPLE_RATE, mono=False)

    mixed = mix_audio(vocals_stretched, instrumental)

    # --- Step 7: Export ---
    output_name = (
        f"{vocal_info['artistName']}_vocals_over_"
        f"{inst_info['artistName']}_beat.wav"
    ).replace(" ", "_").replace("'", "")

    output_path = os.path.join(OUTPUT_DIR, output_name)
    sf.write(output_path, mixed.T, SAMPLE_RATE)

    print(f"\n=== Output saved to: {output_path} ===")
    print(f"    Duration: {mixed.shape[1] / SAMPLE_RATE:.1f}s")
    print(f"    BPM: {inst_bpm:.0f} (matched to instrumental)")


if __name__ == "__main__":
    main()
