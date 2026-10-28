# UGC Campaign Automation System

Posts finished videos to **Instagram Reels** and **Facebook Reels**, and collects the post links into
a file for MediaMaxxing's **Bulk Import**. Videos are edited in Voyager. See [PLAN.md](PLAN.md) for
the roadmap.

## Daily use

1. Export finished videos from Voyager into the **`ready`** folder.
2. Captions (optional):
   - **Same caption for everything:** edit **`default_caption.txt`**.
   - **Caption for one video:** create a .txt file with the same name, e.g. `clip7.mp4` + `clip7.txt`.
3. Double-click **`post.bat`**. Each video is posted to Instagram and Facebook, then moved to the
   **`posted`** folder.
4. In MediaMaxxing go to **Advanced Submit → Bulk Import → Upload File** and pick the newest file in
   the **`links`** folder. Then click **Import Links** and **Submit All**.

If an upload fails, the video stays in `ready`. Run `post.bat` again: it only retries what's missing
and never posts the same video twice to a platform.

A record of everything posted (date, video, platform, link) is kept in `posted\posting_log.csv`,
which opens in Excel.

## One-time setup

1. **Python and the project files:** if you already did this for the editor, skip it. Otherwise
   install Python from https://www.python.org/downloads/ and download this project
   (**Code → Download ZIP** on GitHub, then right-click → **Extract All**). Nothing else needs installing.
2. **Connect Instagram and Facebook:** follow [docs/meta-setup.md](docs/meta-setup.md), which ends
   with double-clicking **`setup.bat`**.

Your access key is saved in `settings.json` on your PC. It's never uploaded to GitHub. Don't share it.

## Extra options

From PowerShell in the project folder (tip: type `powershell` in File Explorer's address bar):

| Command | What it does |
| --- | --- |
| `python -m ugc_poster post --dry-run` | Shows what would be posted, without posting |
| `python -m ugc_poster post --limit 5` | Posts only the 5 oldest videos (e.g. to spread posts through the day) |
| `python -m ugc_poster post --only facebook` | Posts to one platform only |

To turn a platform off permanently, open `settings.json` in Notepad and change `"instagram": true`
(or `"facebook"`) to `false`.

## Other tools

- [docs/editor.md](docs/editor.md): optional command-line video editor (split screen, music, captions)

## Running the tests

```
python -m unittest discover tests
```
