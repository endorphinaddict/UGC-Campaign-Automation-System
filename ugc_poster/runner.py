"""The posting run: take each video in ready/, post it everywhere, move it to posted/,
and write the new links to a .txt file for MediaMaxxing's Bulk Import."""

import csv
import json
import shutil
import time
from datetime import datetime
from pathlib import Path

from . import platforms
from .graph import DEFAULT_VERSION, AuthError, Graph, PosterError

VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v"}
PLATFORMS = ("instagram", "facebook")


def find_videos(ready):
    videos = [p for p in ready.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS]
    return sorted(videos, key=lambda p: (p.stat().st_mtime, p.name))


def caption_for(video, default_caption_file):
    """A .txt file with the same name as the video wins; otherwise the default caption."""
    for path in (video.with_suffix(".txt"), default_caption_file):
        if path.is_file():
            return path.read_text(encoding="utf-8-sig").strip()
    return ""


def _progress_path(video):
    return video.with_name(video.name + ".progress.json")


def _load_progress(video):
    path = _progress_path(video)
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def _save_progress(video, progress):
    _progress_path(video).write_text(json.dumps(progress, indent=2), encoding="utf-8")


def _free_name(folder, name):
    """posted/clip.mp4, or posted/clip (2).mp4 if that name is taken."""
    target = folder / name
    n = 2
    while target.exists():
        target = folder / f"{Path(name).stem} ({n}){Path(name).suffix}"
        n += 1
    return target


def _move_to_posted(video, posted):
    target = _free_name(posted, video.name)
    for extra in (video.with_suffix(".txt"), _progress_path(video)):
        if extra.is_file():
            # Keep the caption and progress record next to the moved video.
            new_name = target.with_suffix(".txt") if extra.suffix == ".txt" else target.with_name(target.name + ".progress.json")
            shutil.move(str(extra), str(new_name))
    shutil.move(str(video), str(target))


def run(root, settings, dry_run=False, limit=None, only=None, sleep=time.sleep, graph=None):
    """Returns the number of failures (0 means everything posted)."""
    root = Path(root)
    ready, posted, links_dir = root / "ready", root / "posted", root / "links"
    for folder in (ready, posted, links_dir):
        folder.mkdir(exist_ok=True)

    enabled = [p for p in PLATFORMS if settings.get("platforms", {}).get(p, True)]
    if only:
        enabled = [p for p in enabled if p == only]
    if "instagram" in enabled and settings and not settings.get("instagram_user_id"):
        print("No Instagram account is linked in settings.json, so skipping Instagram.")
        enabled.remove("instagram")
    if not enabled:
        print("No platforms to post to. Check settings.json.")
        return 1

    videos = find_videos(ready)
    if limit:
        videos = videos[:limit]
    if not videos:
        print(f"No videos waiting in {ready}. Put your finished videos there and run this again.")
        return 0

    default_caption = root / "default_caption.txt"
    if dry_run:
        print(f"Dry run: would post {len(videos)} video(s) to {', '.join(enabled)}:")
        for v in videos:
            todo = [p for p in enabled if p not in _load_progress(v)]
            print(f"  {v.name} -> {', '.join(todo) or 'already done'}")
            print(f"      caption: {caption_for(v, default_caption)[:80]!r}")
        return 0

    graph = graph or Graph(settings["access_token"], settings.get("graph_api_version", DEFAULT_VERSION))
    new_links, failures = [], 0
    log_path = posted / "posting_log.csv"

    for i, video in enumerate(videos, 1):
        print(f"\n[{i}/{len(videos)}] {video.name}")
        caption = caption_for(video, default_caption)
        progress = _load_progress(video)
        for platform in enabled:
            if platform in progress:
                print(f"  {platform}: already posted, skipping")
                continue
            print(f"  {platform}: uploading...")
            try:
                if platform == "instagram":
                    link = platforms.post_instagram(graph, settings["instagram_user_id"], video, caption,
                                                    settings.get("share_to_feed", True), sleep)
                else:
                    link = platforms.post_facebook(graph, settings["page_id"], video, caption, sleep)
            except AuthError:
                raise
            except PosterError as e:
                print(f"  {platform}: FAILED - {e}")
                failures += 1
                continue
            progress[platform] = link
            _save_progress(video, progress)
            new_links.append(link)
            new_log = not log_path.exists()
            with open(log_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if new_log:
                    writer.writerow(["posted_at", "video", "platform", "link"])
                writer.writerow([datetime.now().isoformat(timespec="seconds"), video.name, platform, link])
            print(f"  {platform}: done {link}")
        if all(p in progress for p in enabled):
            _move_to_posted(video, posted)

    if new_links:
        links_file = links_dir / f"links_{datetime.now():%Y-%m-%d_%H%M%S}.txt"
        links_file.write_text("\n".join(new_links) + "\n", encoding="utf-8")
        print(f"\n{len(new_links)} new link(s) saved to:\n  {links_file}")
        print("Upload that file in MediaMaxxing: Advanced Submit -> Bulk Import -> Upload File.")
    if failures:
        print(f"\n{failures} upload(s) failed. Those videos stay in 'ready' - run again to retry them.")
    return failures
