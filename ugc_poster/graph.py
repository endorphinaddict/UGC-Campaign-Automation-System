"""Minimal client for Meta's Graph API, using only the Python standard library."""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

GRAPH_HOST = "https://graph.facebook.com"
DEFAULT_VERSION = "v23.0"


class PosterError(Exception):
    """A problem the user can read and act on."""


class AuthError(PosterError):
    """The access token is invalid or expired; nothing else will work until setup is re-run."""


class Graph:
    def __init__(self, token, version=DEFAULT_VERSION):
        self.token = token
        self.version = version

    def _url(self, path):
        return f"{GRAPH_HOST}/{self.version}/{path.lstrip('/')}"

    def get(self, path, **params):
        if self.token:
            params.setdefault("access_token", self.token)
        url = self._url(path) + "?" + urllib.parse.urlencode(params)
        return self._send(urllib.request.Request(url, method="GET"))

    def post(self, path, **params):
        if self.token:
            params.setdefault("access_token", self.token)
        body = urllib.parse.urlencode(params).encode()
        return self._send(urllib.request.Request(self._url(path), data=body, method="POST"))

    def upload(self, upload_url, file_path):
        """Send a whole video file to one of Meta's resumable upload URLs."""
        size = os.path.getsize(file_path)
        with open(file_path, "rb") as f:
            req = urllib.request.Request(upload_url, data=f, method="POST", headers={
                "Authorization": f"OAuth {self.token}",
                "offset": "0",
                "file_size": str(size),
                "Content-Length": str(size),
                "Content-Type": "application/octet-stream",
            })
            return self._send(req, timeout=900)

    def _send(self, req, timeout=60):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            raise _graph_error(e.read().decode(errors="replace"), e.code) from None
        except urllib.error.URLError as e:
            raise PosterError(f"Could not reach Meta ({e.reason}). Check your internet connection.") from None


def _graph_error(body, status):
    try:
        err = json.loads(body).get("error", {})
    except ValueError:
        return PosterError(f"Meta returned HTTP {status}: {body[:300]}")
    message = err.get("error_user_msg") or err.get("message") or body[:300]
    if err.get("code") == 190:
        return AuthError(f"Your access key no longer works ({message}). Run setup.bat again.")
    return PosterError(f"Meta said: {message}")
