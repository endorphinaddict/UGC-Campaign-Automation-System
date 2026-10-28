"""Small helpers around ffmpeg / ffprobe."""

import json
import shutil
import subprocess


class EditorError(Exception):
    """A problem the user can fix (missing file, missing tool, bad option)."""


def require_tools():
    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            raise EditorError(
                f"'{tool}' was not found. Install ffmpeg (see README.md, step 2) "
                "and open a new terminal window."
            )


def probe(path):
    """Return (duration_seconds, has_audio) for a media file."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise EditorError(f"Could not read '{path}'. Is it a video or audio file?")
    info = json.loads(result.stdout)
    duration = float(info.get("format", {}).get("duration") or 0)
    has_audio = any(s.get("codec_type") == "audio" for s in info.get("streams", []))
    return duration, has_audio


def run_ffmpeg(args, cwd=None):
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args]
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise EditorError("ffmpeg failed:\n" + result.stderr.strip())
