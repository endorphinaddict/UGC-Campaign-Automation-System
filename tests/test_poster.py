"""Run with: python -m unittest discover tests"""

import io
import json
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from ugc_poster import graph as graph_mod
from ugc_poster.graph import AuthError, Graph, PosterError
from ugc_poster.runner import run
from ugc_poster.setup_wizard import run_setup

SETTINGS = {"page_id": "PAGE", "instagram_user_id": "IG", "access_token": "TOKEN"}


class FakeGraph:
    """Pretends to be Meta. fail_on: set of platform names whose upload should fail."""

    version = "v23.0"

    def __init__(self, fail_on=()):
        self.fail_on = set(fail_on)
        self.calls = []
        self.ig_polls = 0

    def post(self, path, **params):
        self.calls.append(("post", path, params))
        if path == "IG/media":
            return {"id": "C1", "uri": "https://rupload.facebook.com/ig-api-upload/v23.0/C1"}
        if path == "IG/media_publish":
            return {"id": "M1"}
        if path == "PAGE/video_reels" and params["upload_phase"] == "start":
            return {"video_id": "V1", "upload_url": "https://rupload.facebook.com/video-upload/v23.0/V1"}
        return {"success": True}

    def upload(self, url, file_path):
        self.calls.append(("upload", url, file_path))
        if ("ig-api" in url and "instagram" in self.fail_on) or ("video-upload" in url and "facebook" in self.fail_on):
            raise PosterError("upload broke")
        return {"success": True}

    def get(self, path, **params):
        self.calls.append(("get", path, params))
        if path == "C1":
            self.ig_polls += 1  # "processing" first, then finished
            return {"status_code": "IN_PROGRESS" if self.ig_polls == 1 else "FINISHED"}
        if path == "M1":
            return {"permalink": "https://www.instagram.com/reel/abc/"}
        if params.get("fields") == "status":
            return {"status": {"video_status": "ready", "publishing_phase": {"status": "complete"}}}
        if params.get("fields") == "permalink_url":
            return {"permalink_url": "/reel/V1/"}
        raise AssertionError(path)


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        (self.root / "ready").mkdir()
        (self.root / "ready" / "clip1.mp4").write_bytes(b"video")
        (self.root / "ready" / "clip1.txt").write_text("custom caption #melty", encoding="utf-8")
        (self.root / "default_caption.txt").write_text("default caption", encoding="utf-8")

    def go(self, graph, **kw):
        with redirect_stdout(io.StringIO()) as out:
            failures = run(self.root, SETTINGS, sleep=lambda s: None, graph=graph, **kw)
        return failures, out.getvalue()

    def links(self):
        files = list((self.root / "links").glob("links_*.txt"))
        return [line for f in files for line in f.read_text().splitlines()]

    def test_posts_everywhere_and_writes_links(self):
        g = FakeGraph()
        failures, _ = self.go(g)
        self.assertEqual(failures, 0)
        self.assertEqual(self.links(), ["https://www.instagram.com/reel/abc/", "https://www.facebook.com/reel/V1/"])
        # Caption from the matching .txt file was used on both platforms.
        posts = {c[1]: c[2] for c in g.calls if c[0] == "post"}
        self.assertEqual(posts["IG/media"]["caption"], "custom caption #melty")
        self.assertEqual(posts["IG/media"]["media_type"], "REELS")
        finish = [c[2] for c in g.calls if c[1] == "PAGE/video_reels" and c[2]["upload_phase"] == "finish"][0]
        self.assertEqual(finish["description"], "custom caption #melty")
        # The video and its caption moved to posted/, with a log entry per platform.
        self.assertFalse((self.root / "ready" / "clip1.mp4").exists())
        self.assertTrue((self.root / "posted" / "clip1.mp4").exists())
        self.assertTrue((self.root / "posted" / "clip1.txt").exists())
        self.assertEqual(len((self.root / "posted" / "posting_log.csv").read_text().splitlines()), 3)

    def test_partial_failure_retries_only_the_missing_platform(self):
        failures, _ = self.go(FakeGraph(fail_on={"facebook"}))
        self.assertEqual(failures, 1)
        self.assertTrue((self.root / "ready" / "clip1.mp4").exists())  # stays for a retry

        g = FakeGraph()
        failures, out = self.go(g)
        self.assertEqual(failures, 0)
        self.assertIn("instagram: already posted", out)
        self.assertFalse(any(c[1] == "IG/media" for c in g.calls))  # Instagram not posted twice
        self.assertTrue((self.root / "posted" / "clip1.mp4").exists())

    def test_default_caption_and_name_clash_in_posted(self):
        (self.root / "ready" / "clip1.txt").unlink()
        (self.root / "posted").mkdir()
        (self.root / "posted" / "clip1.mp4").write_bytes(b"older video")
        g = FakeGraph()
        self.go(g)
        posts = {c[1]: c[2] for c in g.calls if c[0] == "post"}
        self.assertEqual(posts["IG/media"]["caption"], "default caption")
        self.assertTrue((self.root / "posted" / "clip1 (2).mp4").exists())

    def test_dry_run_posts_nothing(self):
        g = FakeGraph()
        _, out = self.go(g, dry_run=True)
        self.assertEqual(g.calls, [])
        self.assertIn("clip1.mp4 -> instagram, facebook", out)

    def test_only_and_limit(self):
        (self.root / "ready" / "clip2.mp4").write_bytes(b"video")
        g = FakeGraph()
        self.go(g, only="facebook", limit=1)
        self.assertFalse(any(c[1].startswith("IG/") for c in g.calls))
        self.assertEqual(sum(1 for c in g.calls if c[0] == "upload"), 1)

    def test_expired_token_stops_the_run(self):
        g = FakeGraph()
        g.upload = mock.Mock(side_effect=AuthError("expired"))
        with self.assertRaises(AuthError), redirect_stdout(io.StringIO()):
            run(self.root, SETTINGS, sleep=lambda s: None, graph=g)


class GraphTests(unittest.TestCase):
    def http_error(self, body):
        return urllib.error.HTTPError("u", 400, "bad", {}, io.BytesIO(json.dumps(body).encode()))

    def test_error_messages(self):
        with mock.patch.object(graph_mod.urllib.request, "urlopen",
                               side_effect=self.http_error({"error": {"message": "bad caption", "code": 100}})):
            with self.assertRaisesRegex(PosterError, "bad caption"):
                Graph("T").post("IG/media", caption="x")
        with mock.patch.object(graph_mod.urllib.request, "urlopen",
                               side_effect=self.http_error({"error": {"message": "expired", "code": 190}})):
            with self.assertRaises(AuthError):
                Graph("T").get("me")

    def test_upload_sends_meta_headers(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"12345")
        resp = mock.MagicMock()
        resp.__enter__.return_value.read.return_value = b'{"success": true}'
        with mock.patch.object(graph_mod.urllib.request, "urlopen", return_value=resp) as urlopen:
            Graph("T").upload("https://rupload.facebook.com/x", f.name)
        req = urlopen.call_args[0][0]
        self.assertEqual(req.get_header("Authorization"), "OAuth T")
        self.assertEqual(req.get_header("File_size"), "5")
        self.assertEqual(req.get_header("Offset"), "0")


class SetupTests(unittest.TestCase):
    def test_setup_saves_page_token_and_instagram(self):
        class SetupGraph:
            def __init__(self, token):
                self.token = token

            def get(self, path, **params):
                if path == "oauth/access_token":
                    assert params["fb_exchange_token"] == "SHORT"
                    return {"access_token": "LONG"}
                assert self.token == "LONG"
                return {"data": [
                    {"id": "P1", "name": "Other Page", "access_token": "PT1"},
                    {"id": "P2", "name": "Melty Clips", "access_token": "PT2",
                     "instagram_business_account": {"id": "IG2", "username": "meltyclips"}},
                ]}

        answers = iter(["123", "secret", "SHORT", "2"])
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "settings.json"
            with redirect_stdout(io.StringIO()):
                run_setup(path, ask=lambda prompt: next(answers), graph_cls=SetupGraph)
            saved = json.loads(path.read_text())
        self.assertEqual(saved["page_id"], "P2")
        self.assertEqual(saved["access_token"], "PT2")
        self.assertEqual(saved["instagram_user_id"], "IG2")
        self.assertNotIn("secret", json.dumps(saved))  # the app secret is never stored


if __name__ == "__main__":
    unittest.main()
