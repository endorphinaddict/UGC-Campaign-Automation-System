"""Caption generation: speech-to-text with faster-whisper, or an existing .srt file,
written out as a styled .ass subtitle file that ffmpeg burns into the video."""

import re

from .media import EditorError


def transcribe_words(audio_path, model_size="base", language=None):
    """Return a list of (start, end, word) using faster-whisper word timestamps."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise EditorError(
            "Auto captions need the 'faster-whisper' package. Run: pip install -r requirements.txt\n"
            "Or skip captions with --captions none, or supply your own with --srt file.srt"
        )
    model = WhisperModel(model_size, device="auto", compute_type="int8")
    segments, _ = model.transcribe(str(audio_path), language=language, word_timestamps=True, vad_filter=True)
    words = []
    for segment in segments:
        for w in segment.words or []:
            text = w.word.strip()
            if text:
                words.append((w.start, w.end, text))
    return words


def group_words(words, words_per_caption):
    """Merge words into short on-screen chunks, TikTok style."""
    chunks = []
    for i in range(0, len(words), words_per_caption):
        group = words[i : i + words_per_caption]
        chunks.append((group[0][0], group[-1][1], " ".join(w[2] for w in group)))
    return chunks


_SRT_TIME = re.compile(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)")


def read_srt(path):
    """Return a list of (start, end, text) from an .srt file."""
    with open(path, encoding="utf-8-sig") as f:
        blocks = re.split(r"\n\s*\n", f.read().replace("\r\n", "\n").strip())
    captions = []
    for block in blocks:
        lines = block.strip().split("\n")
        for i, line in enumerate(lines):
            m = _SRT_TIME.search(line)
            if m:
                h1, m1, s1, ms1, h2, m2, s2, ms2 = (int(x) for x in m.groups())
                start = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000
                end = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000
                text = " ".join(lines[i + 1 :]).strip()
                if text:
                    captions.append((start, end, text))
                break
    return captions


def _ass_time(seconds):
    cs = int(round(seconds * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _ass_color(hex_color):
    """'#RRGGBB' -> ASS '&H00BBGGRR'."""
    h = hex_color.lstrip("#")
    if len(h) != 6:
        raise EditorError(f"Colour '{hex_color}' should look like #FFFFFF")
    return f"&H00{h[4:6]}{h[2:4]}{h[0:2]}".upper()


def write_ass(captions, path, width, height, y, style):
    """Write captions centred horizontally at vertical position y (pixels)."""
    text_color = _ass_color(style["color"])
    outline_color = _ass_color(style["outline_color"])
    header = (
        "[Script Info]\nScriptType: v4.00+\n"
        f"PlayResX: {width}\nPlayResY: {height}\nWrapStyle: 0\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Caption,{style['font']},{style['size']},{text_color},{text_color},{outline_color},&H80000000,"
        f"-1,0,0,0,100,100,0,0,1,{style['outline']},2,5,60,60,0,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    lines = []
    for start, end, text in captions:
        if style["uppercase"]:
            text = text.upper()
        text = text.replace("{", "(").replace("}", ")").replace("\n", " ")
        lines.append(
            f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},Caption,,0,0,0,,"
            f"{{\\an5\\pos({width // 2},{y})}}{text}"
        )
    with open(path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(lines) + "\n")
