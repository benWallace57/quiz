#!/usr/bin/env python3
"""Download the audio for every mashup in quizzes/mashup.html.

The quiz plays local audio files instead of embedding YouTube players.
Video IDs are read straight from the QUESTIONS array in mashup.html, so
adding a question there and re-running this script is all that's needed.

Output: quizzes/mashup_audio/<video id>.m4a  (full track, so the clip
start offsets can still be tuned in the page).

Usage:
    python3 tools/download_mashup_audio.py           # fetch missing files
    python3 tools/download_mashup_audio.py --force   # re-download all

Deps: yt-dlp, imageio-ffmpeg
    pip install --user --break-system-packages "yt-dlp[default]"
"""
import re
import sys
from pathlib import Path

import imageio_ffmpeg
import yt_dlp

ROOT = Path(__file__).resolve().parent.parent
QUIZ = ROOT / "quizzes" / "mashup.html"
OUT_DIR = ROOT / "quizzes" / "mashup_audio"


def video_ids():
    html = QUIZ.read_text(encoding="utf-8")
    block = re.search(r"const QUESTIONS = \[(.*?)\n\s*\];", html, re.S)
    if not block:
        sys.exit(f"Couldn't find the QUESTIONS array in {QUIZ}")
    return re.findall(r"\bid:\s*'([\w-]{11})'", block.group(1))


def ffmpeg_dir():
    # imageio-ffmpeg ships a binary with a versioned name; yt-dlp looks for
    # a file called "ffmpeg", so link it into a private directory.
    tool_dir = ROOT / "tools" / ".ffmpeg"
    tool_dir.mkdir(exist_ok=True)
    link = tool_dir / "ffmpeg"
    if not link.exists():
        link.symlink_to(imageio_ffmpeg.get_ffmpeg_exe())
    return str(tool_dir)


def main():
    force = "--force" in sys.argv
    ids = video_ids()
    OUT_DIR.mkdir(exist_ok=True)

    todo = [i for i in ids if force or not (OUT_DIR / f"{i}.m4a").exists()]
    print(f"{len(ids)} mashups, {len(todo)} to download")
    if not todo:
        return

    opts = {
        # Prefer YouTube's native AAC stream (plays everywhere, no re-encode);
        # fall back to any audio and convert it to m4a.
        "format": "bestaudio[ext=m4a]/bestaudio",
        "outtmpl": str(OUT_DIR / "%(id)s.%(ext)s"),
        "ffmpeg_location": ffmpeg_dir(),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "m4a",
        }],
        "overwrites": force,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": False,
        "progress": True,
    }
    # yt-dlp warns when there's no JS runtime (deno, or node >= 22) for
    # YouTube; audio formats still download fine without one. If downloads
    # start failing, install deno: https://github.com/yt-dlp/yt-dlp/wiki/EJS

    failed = []
    with yt_dlp.YoutubeDL(opts) as ydl:
        for vid in todo:
            print(f"-> {vid}")
            try:
                ydl.download([f"https://www.youtube.com/watch?v={vid}"])
            except yt_dlp.utils.DownloadError as e:
                print(f"   FAILED: {e}")
                failed.append(vid)

    for vid in ids:
        f = OUT_DIR / f"{vid}.m4a"
        size = f"{f.stat().st_size / 1e6:.1f} MB" if f.exists() else "missing"
        print(f"  {vid}: {size}")
    if failed:
        sys.exit(f"{len(failed)} download(s) failed: {', '.join(failed)}")


if __name__ == "__main__":
    main()
