"""
Vocal Swap Tool — CLI for managing a stems database.

Commands:
    search <query>  — Search iTunes for songs
    add <query>     — Download, separate stems, detect beats, add to database
    list            — Show all songs in the database
    serve [port]    — Start local server with API + mixer UI (default port 8765)

Usage:
    python3 vocal_swap_tool.py search "billie jean"
    python3 vocal_swap_tool.py add "crazy in love beyonce"
    python3 vocal_swap_tool.py list
    python3 vocal_swap_tool.py serve
"""

import os
import sys
import json
import re
import tempfile
import subprocess
import requests
import numpy as np
import librosa
import soundfile as sf

SAMPLE_RATE = 44100
STEMS_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stems_db")
DB_FILE = os.path.join(STEMS_DB, "database.json")


def get_ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE) as f:
            return json.load(f)
    return []


def save_db(entries):
    os.makedirs(STEMS_DB, exist_ok=True)
    with open(DB_FILE, 'w') as f:
        json.dump(entries, f, indent=2)


def fetch_itunes_preview(term, limit=5):
    r = requests.get("https://itunes.apple.com/search", params={
        "term": term, "entity": "song", "limit": limit,
    })
    r.raise_for_status()
    return r.json().get("results", [])


def download_and_convert(url, out_wav_path):
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
    import demucs.separate

    demucs.separate.main([
        "--two-stems", "vocals",
        "-n", "htdemucs",
        "--out", output_dir,
        wav_path,
    ])

    basename = os.path.splitext(os.path.basename(wav_path))[0]
    stems_dir = os.path.join(output_dir, "htdemucs", basename)

    return (
        os.path.join(stems_dir, "vocals.wav"),
        os.path.join(stems_dir, "no_vocals.wav"),
    )


def detect_beats(wav_path):
    y, sr = librosa.load(wav_path, sr=SAMPLE_RATE, mono=True)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    if hasattr(tempo, '__len__'):
        tempo = tempo[0]
    beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()
    duration = len(y) / sr
    return float(tempo), beat_times, float(duration)


def cmd_search(query):
    results = fetch_itunes_preview(query)
    if not results:
        print("No results found.")
        return

    print(f"Found {len(results)} result(s):\n")
    for i, r in enumerate(results, 1):
        print(f"  {i}. {r['trackName']} — {r['artistName']}")
        if r.get('previewUrl'):
            print(f"     Preview: {r['previewUrl']}")
        print()


def cmd_add(query):
    print(f"Searching iTunes for: {query}")
    results = fetch_itunes_preview(query, limit=1)

    if not results:
        sys.exit("No results found.")

    result = results[0]
    track = result['trackName']
    artist = result['artistName']
    preview_url = result.get('previewUrl')

    if not preview_url:
        sys.exit(f"No preview available for: {track} — {artist}")

    song_id = slugify(f"{artist}-{track}")
    song_dir = os.path.join(STEMS_DB, song_id)

    db = load_db()
    if any(e['id'] == song_id for e in db):
        print(f"Already in database: {track} — {artist}")
        return

    print(f"  Track: {track}")
    print(f"  Artist: {artist}")
    print(f"  ID: {song_id}")

    os.makedirs(song_dir, exist_ok=True)

    # Download
    print("\n  Downloading preview...")
    source_wav = os.path.join(song_dir, "source.wav")
    download_and_convert(preview_url, source_wav)

    # Separate stems
    print("  Separating stems with demucs (~20-30s on CPU)...")
    demucs_out = os.path.join(song_dir, "_demucs")
    vocals_path, instrumental_path = separate_stems(source_wav, demucs_out)

    # Move stems to final location
    final_vocals = os.path.join(song_dir, "vocals.wav")
    final_instrumental = os.path.join(song_dir, "instrumental.wav")
    os.rename(vocals_path, final_vocals)
    os.rename(instrumental_path, final_instrumental)

    # Clean up demucs output dir and source
    import shutil
    shutil.rmtree(demucs_out, ignore_errors=True)
    os.unlink(source_wav)

    # Detect beats
    print("  Detecting BPM and beats...")
    bpm, beats, duration = detect_beats(final_instrumental)
    print(f"  BPM: {bpm:.1f}, Beats: {len(beats)}, Duration: {duration:.1f}s")

    # Save metadata
    metadata = {
        "id": song_id,
        "name": track,
        "artist": artist,
        "bpm": round(bpm, 1),
        "duration": round(duration, 2),
        "beats": [round(b, 4) for b in beats],
    }
    with open(os.path.join(song_dir, "metadata.json"), 'w') as f:
        json.dump(metadata, f, indent=2)

    # Update database index
    db.append(metadata)
    save_db(db)

    print(f"\n  Added to database: {track} — {artist} ({bpm:.0f} BPM)")


def cmd_list():
    db = load_db()
    if not db:
        print("Database is empty. Use 'add' to add songs.")
        return

    print(f"Stems database ({len(db)} songs):\n")
    for entry in db:
        print(f"  {entry['artist']} — {entry['name']}")
        print(f"    BPM: {entry['bpm']}, Duration: {entry['duration']}s, Beats: {len(entry['beats'])}")
        print()


def cmd_serve(port=8765):
    from http.server import HTTPServer, SimpleHTTPRequestHandler
    import urllib.parse
    import threading

    tool_dir = os.path.dirname(os.path.abspath(__file__))
    processing = {}

    class MixerHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=tool_dir, **kwargs)

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == '/api/search':
                self._handle_search(parsed)
            elif parsed.path == '/api/list':
                self._handle_list()
            elif parsed.path == '/api/status':
                self._handle_status(parsed)
            else:
                super().do_GET()

        def do_POST(self):
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == '/api/add':
                self._handle_add()
            else:
                self.send_error(404)

        def _json_response(self, data, status=200):
            body = json.dumps(data).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(body))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(body)

        def _handle_search(self, parsed):
            params = urllib.parse.parse_qs(parsed.query)
            query = params.get('q', [''])[0]
            if not query:
                self._json_response({'error': 'Missing ?q= parameter'}, 400)
                return
            results = fetch_itunes_preview(query, limit=8)
            self._json_response([{
                'trackName': r.get('trackName'),
                'artistName': r.get('artistName'),
                'previewUrl': r.get('previewUrl'),
                'artworkUrl': r.get('artworkUrl100', ''),
            } for r in results])

        def _handle_list(self):
            self._json_response(load_db())

        def _handle_status(self, parsed):
            params = urllib.parse.parse_qs(parsed.query)
            song_id = params.get('id', [''])[0]
            if song_id in processing:
                self._json_response({'status': processing[song_id]})
            else:
                db = load_db()
                if any(e['id'] == song_id for e in db):
                    self._json_response({'status': 'done'})
                else:
                    self._json_response({'status': 'unknown'})

        def _handle_add(self):
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            track = body.get('trackName', '')
            artist = body.get('artistName', '')
            preview_url = body.get('previewUrl', '')

            if not preview_url or not track:
                self._json_response({'error': 'Missing trackName or previewUrl'}, 400)
                return

            song_id = slugify(f"{artist}-{track}")
            db = load_db()
            if any(e['id'] == song_id for e in db):
                self._json_response({'id': song_id, 'status': 'exists'})
                return

            processing[song_id] = 'downloading'
            self._json_response({'id': song_id, 'status': 'processing'})

            def process():
                try:
                    song_dir = os.path.join(STEMS_DB, song_id)
                    os.makedirs(song_dir, exist_ok=True)

                    processing[song_id] = 'downloading'
                    source_wav = os.path.join(song_dir, "source.wav")
                    download_and_convert(preview_url, source_wav)

                    processing[song_id] = 'separating'
                    demucs_out = os.path.join(song_dir, "_demucs")
                    vocals_path, instrumental_path = separate_stems(source_wav, demucs_out)

                    final_vocals = os.path.join(song_dir, "vocals.wav")
                    final_instrumental = os.path.join(song_dir, "instrumental.wav")
                    os.rename(vocals_path, final_vocals)
                    os.rename(instrumental_path, final_instrumental)

                    import shutil
                    shutil.rmtree(demucs_out, ignore_errors=True)
                    os.unlink(source_wav)

                    processing[song_id] = 'detecting beats'
                    bpm, beats, duration = detect_beats(final_instrumental)

                    metadata = {
                        "id": song_id,
                        "name": track,
                        "artist": artist,
                        "bpm": round(bpm, 1),
                        "duration": round(duration, 2),
                        "beats": [round(b, 4) for b in beats],
                    }
                    with open(os.path.join(song_dir, "metadata.json"), 'w') as f:
                        json.dump(metadata, f, indent=2)

                    db = load_db()
                    db.append(metadata)
                    save_db(db)

                    processing[song_id] = 'done'
                    print(f"  [server] Added: {track} — {artist} ({bpm:.0f} BPM)")
                except Exception as e:
                    processing[song_id] = f'error: {e}'
                    print(f"  [server] Error processing {song_id}: {e}")

            threading.Thread(target=process, daemon=True).start()

        def log_message(self, format, *args):
            if '/api/' in (args[0] if args else ''):
                super().log_message(format, *args)

    HTTPServer.allow_reuse_address = True
    server = HTTPServer(('', port), MixerHandler)
    print(f"Serving mixer at http://localhost:{port}/mixer.html")
    print(f"API endpoints:")
    print(f"  GET  /api/search?q=...  — search iTunes")
    print(f"  GET  /api/list          — list stems database")
    print(f"  POST /api/add           — add song (triggers background processing)")
    print(f"  GET  /api/status?id=... — check processing status")
    print(f"\nPress Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "search":
        if len(sys.argv) < 3:
            sys.exit("Usage: vocal_swap_tool.py search <query>")
        cmd_search(" ".join(sys.argv[2:]))

    elif cmd == "add":
        if len(sys.argv) < 3:
            sys.exit("Usage: vocal_swap_tool.py add <query>")
        cmd_add(" ".join(sys.argv[2:]))

    elif cmd == "list":
        cmd_list()

    elif cmd == "serve":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8765
        cmd_serve(port)

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
