"""Run with: python -m unittest discover tests"""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ugc_editor import captions as cap
from ugc_editor.__main__ import main

HAVE_FFMPEG = shutil.which("ffmpeg") and shutil.which("ffprobe")


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args], check=True)


def streams(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout
    return json.loads(out)


class CaptionTests(unittest.TestCase):
    def test_group_words(self):
        words = [(0, 1, "a"), (1, 2, "b"), (2, 3, "c"), (3, 4, "d")]
        self.assertEqual(cap.group_words(words, 3), [(0, 3, "a b c"), (3, 4, "d")])

    def test_read_srt_windows_line_endings(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.srt"
            p.write_bytes(b"1\r\n00:00:01,500 --> 00:00:03,000\r\nhello\r\nthere\r\n\r\n2\r\n00:01:00,000 --> 00:01:01,250\r\nbye\r\n")
            self.assertEqual(cap.read_srt(p), [(1.5, 3.0, "hello there"), (60.0, 61.25, "bye")])

    def test_write_ass(self):
        style = {"font": "Arial", "size": 80, "color": "#FF8800", "outline_color": "#000000",
                 "outline": 6, "uppercase": True}
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.ass"
            cap.write_ass([(0, 1.25, "hi {there}")], p, 1080, 1920, 960, style)
            text = p.read_text(encoding="utf-8")
        self.assertIn("&H000088FF", text)  # colours are stored blue-green-red
        self.assertIn("Dialogue: 0,0:00:00.00,0:00:01.25,Caption,,0,0,0,,{\\an5\\pos(540,960)}HI (THERE)", text)


@unittest.skipUnless(HAVE_FFMPEG, "ffmpeg not installed")
class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = Path(tempfile.mkdtemp())
        d = cls.dir
        ffmpeg("-f", "lavfi", "-i", "testsrc2=size=1280x720:rate=30:duration=4",
               "-f", "lavfi", "-i", "sine=f=440:d=4", "-shortest", str(d / "top.mp4"))
        ffmpeg("-f", "lavfi", "-i", "smptebars=size=720x1280:rate=24:duration=3",
               "-f", "lavfi", "-i", "sine=f=660:d=3", "-shortest", str(d / "bottom.mp4"))
        ffmpeg("-f", "lavfi", "-i", "testsrc=size=640x480:rate=30:duration=2", str(d / "silent.mp4"))
        ffmpeg("-f", "lavfi", "-i", "sine=f=220:d=1", str(d / "music.mp3"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dir, ignore_errors=True)

    def check(self, out, duration, audio=True):
        info = streams(out)
        video = [s for s in info["streams"] if s["codec_type"] == "video"][0]
        self.assertEqual((video["width"], video["height"]), (1080, 1920))
        self.assertAlmostEqual(float(info["format"]["duration"]), duration, delta=0.15)
        self.assertEqual(any(s["codec_type"] == "audio" for s in info["streams"]), audio)

    def test_music_and_srt_captions(self):
        srt = self.dir / "c.srt"
        srt.write_text("1\n00:00:00,500 --> 00:00:02,000\nwait for it\n", encoding="utf-8")
        out = self.dir / "out 1" / "a.mp4"  # space in folder name on purpose
        d = self.dir
        self.assertEqual(main(["--top", str(d / "top.mp4"), "--bottom", str(d / "bottom.mp4"),
                               "--music", str(d / "music.mp3"), "--srt", str(srt), "--out", str(out)]), 0)
        self.check(out, 3.0)

    def test_blur_fit_with_silent_clip_and_no_audio(self):
        d = self.dir
        out = d / "b.mp4"
        self.assertEqual(main(["--top", str(d / "silent.mp4"), "--bottom", str(d / "bottom.mp4"), "--fit", "blur",
                               "--split", "0.6", "--audio", "top", "--captions", "none", "--out", str(out)]), 0)
        self.check(out, 2.0, audio=False)

    def test_auto_captions_use_transcription(self):
        d = self.dir
        out = d / "c.mp4"
        fake_words = [(0.2, 0.5, "this"), (0.5, 0.8, "is"), (0.8, 1.2, "crazy")]
        with mock.patch.object(cap, "transcribe_words", return_value=fake_words) as t:
            self.assertEqual(main(["--top", str(d / "top.mp4"), "--bottom", str(d / "bottom.mp4"),
                                   "--length", "top", "--max-seconds", "2.5", "--out", str(out)]), 0)
        t.assert_called_once()
        self.check(out, 2.5)

    def test_missing_file_is_a_friendly_error(self):
        self.assertEqual(main(["--top", "nope.mp4", "--bottom", "nope2.mp4", "--captions", "none"]), 1)


if __name__ == "__main__":
    unittest.main()
