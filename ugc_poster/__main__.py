"""Command line: python -m ugc_poster setup | post [--dry-run] [--limit N] [--only instagram|facebook]"""

import argparse
import json
import sys
from pathlib import Path

from .graph import PosterError
from .runner import PLATFORMS, run
from .setup_wizard import run_setup

ROOT = Path(__file__).resolve().parent.parent
SETTINGS = ROOT / "settings.json"


def main(argv=None):
    p = argparse.ArgumentParser(prog="python -m ugc_poster",
                                description="Post videos from ready/ to Instagram and Facebook Reels.")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("setup", help="connect your Facebook Page and Instagram (one time)")
    post = sub.add_parser("post", help="post every video in the ready folder")
    post.add_argument("--dry-run", action="store_true", help="show what would be posted without posting")
    post.add_argument("--limit", type=int, help="post at most this many videos")
    post.add_argument("--only", choices=PLATFORMS, help="post to just one platform")
    opts = p.parse_args(argv)

    try:
        if opts.command == "setup":
            run_setup(SETTINGS)
            return 0
        if not SETTINGS.is_file():
            if opts.dry_run:
                settings = {}
            else:
                print("Not set up yet. Run setup.bat first.", file=sys.stderr)
                return 1
        else:
            settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
        return 1 if run(ROOT, settings, opts.dry_run, opts.limit, opts.only) else 0
    except PosterError as e:
        print(f"\nError: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
