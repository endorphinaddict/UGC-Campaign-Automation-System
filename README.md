# UGC Campaign Automation System

Tools for making, posting and submitting UGC campaign videos. See [PLAN.md](PLAN.md) for the roadmap.

**Ready now:** the video editor. It takes two clips and makes one vertical 1080×1920 video:

```
┌──────────────┐
│  top clip    │  ← e.g. the video you're copying
│              │
│   CAPTIONS   │  ← auto-generated from speech, on the dividing line
│ bottom clip  │  ← e.g. you, filmed on your phone
│              │
└──────────────┘
   + music underneath
```

## One-time setup on Windows

1. **Install Python.** Download it from https://www.python.org/downloads/. In the installer, tick
   **"Add python.exe to PATH"** before clicking Install.
2. **Install ffmpeg** (the video engine). Open **PowerShell** (Start menu → type "PowerShell") and run:
   ```
   winget install Gyan.FFmpeg
   ```
   Close PowerShell and open it again afterwards.
3. **Download this project.** On the GitHub page click **Code → Download ZIP**, then unzip it somewhere
   easy, like `Documents\UGC`.
4. **Install the caption tool.** In PowerShell, go to the project folder and install:
   ```
   cd $HOME\Documents\UGC\UGC-Campaign-Automation-System
   pip install -r requirements.txt
   ```

Check it worked: `ffmpeg -version` and `python --version` should both print a version number.

## Making a video

In PowerShell, from the project folder:

```
python -m ugc_editor --top inspo.mp4 --bottom me.mp4 --music song.mp3
```

The finished video is saved in the `output` folder. Tip: you can drag a file from File Explorer into
the PowerShell window to paste its full path.

The first time you use auto captions, the speech model downloads (about 150 MB), so it takes a
little longer.

### Useful options

| Option | What it does |
| --- | --- |
| `--out my_video.mp4` | Choose where to save the result |
| `--split 0.6` | Give the top clip 60% of the screen (default 0.5 = half each) |
| `--fit blur` | Show each whole clip over a blurred copy instead of cropping the edges |
| `--audio bottom` | Keep only your own clip's sound. Choices: `top`, `bottom`, `both` (default), `none` |
| `--top-volume 0.5` | Make the top clip's sound quieter (same for `--bottom-volume`) |
| `--music-volume 0.25` | Louder music (default 0.15) |
| `--length bottom` | Make the video as long as the bottom clip (default: the shorter clip) |
| `--max-seconds 30` | Cut the video off at 30 seconds |
| `--captions none` | No captions |
| `--srt captions.srt` | Use your own caption file instead of auto captions |
| `--caption-position bottom` | Put captions low on the screen (`middle` is default, also `top`) |
| `--words-per-caption 2` | Fewer words on screen at a time |
| `--font-size 90 --caption-color "#FFE600"` | Bigger, yellow captions |
| `--no-uppercase` | Normal case instead of ALL CAPS |
| `--whisper-model small` | More accurate captions (slower) |

See every option with `python -m ugc_editor --help`.

### Example

Your clip on the bottom taking up a bit more space, only your voice, louder music, captions in the
lower part of the screen:

```
python -m ugc_editor --top inspo.mp4 --bottom me.mp4 --music song.mp3 --split 0.45 --audio bottom --music-volume 0.25 --caption-position bottom
```

## Running the tests

```
python -m unittest discover tests
```
