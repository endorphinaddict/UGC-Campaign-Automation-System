"""Command line: python -m ugc_editor --top clip.mp4 --bottom me.mp4 --music song.mp3"""

import argparse
import sys
from pathlib import Path

from .editor import make_video
from .media import EditorError


def build_parser():
    p = argparse.ArgumentParser(
        prog="python -m ugc_editor",
        description="Stack two clips into one vertical 1080x1920 video with music and captions.",
    )
    p.add_argument("--top", required=True, help="video for the top half (e.g. the clip you're copying)")
    p.add_argument("--bottom", required=True, help="video for the bottom half (e.g. you filming yourself)")
    p.add_argument("--music", help="music file to play underneath (mp3, m4a, wav...)")
    p.add_argument("--out", help="where to save the finished video (default: output/<bottom name>_final.mp4)")

    g = p.add_argument_group("layout")
    g.add_argument("--split", type=float, default=0.5, help="share of the height for the top clip, 0.2-0.8 (default 0.5)")
    g.add_argument("--fit", choices=["crop", "blur"], default="crop",
                   help="crop = fill each half and trim edges; blur = show the whole clip over a blurred copy")
    g.add_argument("--length", choices=["shortest", "top", "bottom"], default="shortest",
                   help="which clip decides the video length (default: shortest)")
    g.add_argument("--max-seconds", type=float, help="cut the video off at this many seconds")

    g = p.add_argument_group("sound")
    g.add_argument("--audio", choices=["top", "bottom", "both", "none"], default="both",
                   help="which clips keep their own sound (default: both)")
    g.add_argument("--top-volume", type=float, default=1.0, help="volume of the top clip's sound (default 1.0)")
    g.add_argument("--bottom-volume", type=float, default=1.0, help="volume of the bottom clip's sound (default 1.0)")
    g.add_argument("--music-volume", type=float, default=0.15, help="music volume, 0-1 (default 0.15)")

    g = p.add_argument_group("captions")
    g.add_argument("--captions", choices=["auto", "none"], default="auto", help="auto = generate from speech (default)")
    g.add_argument("--srt", help="use this .srt caption file instead of generating captions")
    g.add_argument("--caption-position", choices=["middle", "top", "bottom"], default="middle",
                   help="middle = on the line between the two clips (default)")
    g.add_argument("--words-per-caption", type=int, default=3)
    g.add_argument("--font", default="Arial")
    g.add_argument("--font-size", type=int, default=80)
    g.add_argument("--caption-color", default="#FFFFFF")
    g.add_argument("--outline-color", default="#000000")
    g.add_argument("--outline", type=int, default=6, help="outline thickness (default 6)")
    g.add_argument("--no-uppercase", action="store_true", help="keep captions in normal case")
    g.add_argument("--whisper-model", default="base", help="tiny, base, small, medium (bigger = slower but more accurate)")
    g.add_argument("--language", help="speech language code like 'en' (default: detect)")

    g = p.add_argument_group("output")
    g.add_argument("--quality", type=int, default=20, help="18 = best/bigger file, 28 = smaller (default 20)")
    g.add_argument("--keep-temp", action="store_true", help="keep the temporary caption and audio files")
    return p


def main(argv=None):
    opts = build_parser().parse_args(argv)
    if not 0.2 <= opts.split <= 0.8:
        print("--split must be between 0.2 and 0.8", file=sys.stderr)
        return 2
    if opts.words_per_caption < 1:
        print("--words-per-caption must be at least 1", file=sys.stderr)
        return 2
    if not opts.out:
        opts.out = str(Path("output") / f"{Path(opts.bottom).stem}_final.mp4")
    try:
        make_video(opts)
    except EditorError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
