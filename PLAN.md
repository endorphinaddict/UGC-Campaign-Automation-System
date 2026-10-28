# Plan

Campaign: **melty.gg**, submitted through MediaMaxxing for view-based payment. Single user, Windows PC.
About 50 videos a week, posted to Instagram Reels, Facebook Reels and YouTube Shorts.

## Editing: Voyager

Videos are edited in Voyager. The command-line editor in `ugc_editor/` ([docs/editor.md](docs/editor.md))
stays available as a free, batch-friendly alternative.

## Posting

- [x] Instagram Reels + Facebook Reels poster (`ugc_poster/`): posts everything in `ready/`, retries
      safely, moves posted videos, logs every link
- [ ] One-time Meta setup on the user's PC ([docs/meta-setup.md](docs/meta-setup.md))
- [ ] YouTube Shorts: YouTube Data API. Needs a Google Cloud project, and Google's audit before
      uploads can be public and before the daily quota (about 6 uploads) can be raised.

## Submission to MediaMaxxing

- [x] Each posting run writes a `links/links_<date>.txt` file (one link per line) for
      **Advanced Submit → Bulk Import**. No automation of MediaMaxxing's site, so no risk to payouts.

## Later

- [ ] Trend research and a "what performs well" report (`posted/posting_log.csv` is the starting data)
- [ ] View tracker across platforms (postponed)
- [ ] Run posting on a schedule (e.g. Windows Task Scheduler)
