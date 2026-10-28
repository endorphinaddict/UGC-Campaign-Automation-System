"""Builds the split-screen video: top clip over bottom clip, music, burned-in captions."""

import os
import shutil
import tempfile
from pathlib import Path

from . import captions as cap
from .media import EditorError, probe, require_tools, run_ffmpeg

WIDTH, HEIGHT, FPS = 1080, 1920, 30


def _video_chain(index, w, h, fit, label):
    """Scale one input to exactly w x h, either cropping to fill or fitting over a blurred copy."""
    src = f"[{index}:v]"
    if fit == "crop":
        return (
            f"{src}scale={w}:{h}:force_original_aspect_ratio=increase,"
            f"crop={w}:{h},setsar=1,fps={FPS}[{label}]"
        )
    return (
        f"{src}split[{label}bg][{label}fg];"
        f"[{label}bg]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},boxblur=20:2[{label}b];"
        f"[{label}fg]scale={w}:{h}:force_original_aspect_ratio=decrease[{label}f];"
        f"[{label}b][{label}f]overlay=(W-w)/2:(H-h)/2,setsar=1,fps={FPS}[{label}]"
    )


def _voice_chain(sources, volumes):
    """Mix the chosen clips' own audio into [voice]. Returns '' if there is none."""
    if not sources:
        return ""
    parts = [
        f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,volume={volumes[i]}[v{i}]" for i in sources
    ]
    labels = "".join(f"[v{i}]" for i in sources)
    parts.append(f"{labels}amix=inputs={len(sources)}:duration=longest:normalize=0[voice]")
    return ";".join(parts)


def make_video(opts):
    require_tools()
    top, bottom = Path(opts.top).resolve(), Path(opts.bottom).resolve()
    for p in (top, bottom):
        if not p.is_file():
            raise EditorError(f"File not found: {p}")
    music = Path(opts.music).resolve() if opts.music else None
    if music and not music.is_file():
        raise EditorError(f"Music file not found: {music}")
    srt = Path(opts.srt).resolve() if opts.srt else None
    if srt and not srt.is_file():
        raise EditorError(f"Caption file not found: {srt}")
    out = Path(opts.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    top_len, top_audio = probe(top)
    bottom_len, bottom_audio = probe(bottom)
    duration = {"shortest": min(top_len, bottom_len), "top": top_len, "bottom": bottom_len}[opts.length]
    if opts.max_seconds:
        duration = min(duration, opts.max_seconds)
    if duration <= 0:
        raise EditorError("Could not work out the video length.")

    # Which clips' own sound to keep. Clips without an audio track are skipped.
    wanted = {"top": [0], "bottom": [1], "both": [0, 1], "none": []}[opts.audio]
    has_audio = {0: top_audio, 1: bottom_audio}
    voice_sources = [i for i in wanted if has_audio[i]]
    volumes = {0: opts.top_volume, 1: opts.bottom_volume}

    top_h = int(round(HEIGHT * opts.split / 2)) * 2
    bottom_h = HEIGHT - top_h

    work = Path(tempfile.mkdtemp(prefix="ugc_editor_"))
    try:
        # 1. Captions -> captions.ass in the work folder.
        caption_list = []
        if srt:
            caption_list = cap.read_srt(srt)
        elif opts.captions == "auto":
            if not voice_sources:
                print("No speech audio selected, so skipping auto captions.")
            else:
                print("Transcribing speech for captions (first run downloads the speech model)...")
                speech = work / "speech.wav"
                inputs = ["-i", str(top), "-i", str(bottom)]
                run_ffmpeg(
                    [*inputs, "-filter_complex", _voice_chain(voice_sources, volumes),
                     "-map", "[voice]", "-t", f"{duration:.3f}", "-ac", "1", "-ar", "16000", str(speech)]
                )
                words = cap.transcribe_words(speech, opts.whisper_model, opts.language)
                caption_list = cap.group_words(words, opts.words_per_caption)
                if not caption_list:
                    print("No speech was detected, so the video will have no captions.")

        caption_y = {"middle": top_h, "top": int(HEIGHT * 0.15), "bottom": int(HEIGHT * 0.80)}[opts.caption_position]
        if caption_list:
            style = {
                "font": opts.font, "size": opts.font_size, "color": opts.caption_color,
                "outline_color": opts.outline_color, "outline": opts.outline, "uppercase": not opts.no_uppercase,
            }
            cap.write_ass(caption_list, work / "captions.ass", WIDTH, HEIGHT, caption_y, style)

        # 2. Build the final video.
        inputs = ["-i", str(top), "-i", str(bottom)]
        if music:
            inputs += ["-stream_loop", "-1", "-i", str(music)]

        filters = [
            _video_chain(0, WIDTH, top_h, opts.fit, "top"),
            _video_chain(1, WIDTH, bottom_h, opts.fit, "bot"),
        ]
        # The ass filter is given a bare file name and ffmpeg runs inside the work folder,
        # which avoids Windows drive-letter escaping problems.
        filters.append("[top][bot]vstack=inputs=2" + (",ass=captions.ass" if caption_list else "") + "[v]")

        audio_label = None
        voice = _voice_chain(voice_sources, volumes)
        if voice:
            filters.append(voice)
            audio_label = "[voice]"
        if music:
            fade_start = max(duration - 1.5, 0)
            filters.append(
                f"[2:a]aresample=48000,aformat=channel_layouts=stereo,volume={opts.music_volume},"
                f"atrim=0:{duration:.3f},afade=t=out:st={fade_start:.3f}:d=1.5[music]"
            )
            if audio_label:
                filters.append("[voice][music]amix=inputs=2:duration=first:normalize=0[mix]")
                audio_label = "[mix]"
            else:
                audio_label = "[music]"

        args = [*inputs, "-filter_complex", ";".join(filters), "-map", "[v]"]
        if audio_label:
            args += ["-map", audio_label, "-c:a", "aac", "-b:a", "192k"]
        args += [
            "-t", f"{duration:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", str(opts.quality),
            "-pix_fmt", "yuv420p", "-r", str(FPS), "-movflags", "+faststart", str(out),
        ]
        print(f"Rendering {duration:.1f}s video...")
        run_ffmpeg(args, cwd=work)
    finally:
        if opts.keep_temp:
            print(f"Temporary files kept in {work}")
        else:
            shutil.rmtree(work, ignore_errors=True)
    print(f"Done: {out}")
    return out
