"""Uploading one video to Instagram Reels or Facebook Reels. Each returns the public link."""

import time

from .graph import PosterError

POLL_SECONDS = 10
MAX_WAIT_SECONDS = 15 * 60


def _wait_until(check, what, sleep=time.sleep):
    """Call check() every POLL_SECONDS until it returns True."""
    waited = 0
    while not check():
        if waited >= MAX_WAIT_SECONDS:
            raise PosterError(f"Gave up waiting for {what} after {MAX_WAIT_SECONDS // 60} minutes.")
        sleep(POLL_SECONDS)
        waited += POLL_SECONDS


def post_instagram(graph, ig_user_id, video, caption, share_to_feed=True, sleep=time.sleep):
    container = graph.post(
        f"{ig_user_id}/media", media_type="REELS", upload_type="resumable",
        caption=caption, share_to_feed="true" if share_to_feed else "false",
    )
    container_id = container["id"]
    upload_url = container.get("uri") or (
        f"https://rupload.facebook.com/ig-api-upload/{graph.version}/{container_id}"
    )
    graph.upload(upload_url, video)

    def processed():
        info = graph.get(container_id, fields="status_code,status")
        code = info.get("status_code")
        if code in ("ERROR", "EXPIRED"):
            raise PosterError(f"Instagram could not process the video: {info.get('status', code)}")
        return code in ("FINISHED", "PUBLISHED")

    _wait_until(processed, "Instagram to process the video", sleep)
    media = graph.post(f"{ig_user_id}/media_publish", creation_id=container_id)
    link = graph.get(media["id"], fields="permalink").get("permalink")
    if not link:
        raise PosterError(f"Posted to Instagram (media id {media['id']}) but Meta did not return a link.")
    return link


def post_facebook(graph, page_id, video, caption, sleep=time.sleep):
    start = graph.post(f"{page_id}/video_reels", upload_phase="start")
    video_id = start["video_id"]
    upload_url = start.get("upload_url") or f"https://rupload.facebook.com/video-upload/{graph.version}/{video_id}"
    graph.upload(upload_url, video)
    graph.post(
        f"{page_id}/video_reels", upload_phase="finish", video_id=video_id,
        video_state="PUBLISHED", description=caption,
    )

    def published():
        status = graph.get(video_id, fields="status").get("status", {})
        phases = [status.get(p, {}) for p in ("uploading_phase", "processing_phase", "publishing_phase")]
        if status.get("video_status") == "error" or any(p.get("status") == "error" for p in phases):
            raise PosterError(f"Facebook could not process the video: {status}")
        return status.get("publishing_phase", {}).get("status") == "complete"

    _wait_until(published, "Facebook to publish the reel", sleep)
    link = graph.get(video_id, fields="permalink_url").get("permalink_url")
    if not link:
        return f"https://www.facebook.com/reel/{video_id}"
    return "https://www.facebook.com" + link if link.startswith("/") else link
