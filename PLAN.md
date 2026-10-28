# Plan

Campaign: **melty.gg**, submitted through MediaMaxxing for view-based payment. Single user, Windows PC.

## Phase 1: Video editor (done)

- [x] Stack two clips vertically (top: copied clip, bottom: self-filmed), 1080×1920
- [x] Crop-to-fill or fit-over-blur for each half, adjustable split
- [x] Background music with volume control and fade-out
- [x] Auto captions from speech (faster-whisper), or an existing .srt file
- [ ] Later ideas: batch-edit a whole folder, saved presets per campaign, text hook at the start

## Phase 2: Posting

Post finished videos to each platform, one at a time as access is approved.

- [ ] Decide which platforms (TikTok, Instagram Reels, YouTube Shorts, ...)
- [ ] YouTube Shorts: YouTube Data API (Google Cloud project + OAuth)
- [ ] Instagram Reels: Instagram Graph API (needs a Business/Creator account linked to a Facebook Page)
- [ ] TikTok: Content Posting API (needs TikTok app review), or another approved route
- [ ] Captions/hashtags per post

## Phase 3: Submission and trends

- [ ] Submit each live post link to the MediaMaxxing campaign. First check whether MediaMaxxing has an
      API or official integration. Automating its web form may break its terms and risk payouts.
- [ ] Trend research and a "what performs well" dashboard

## Later

- [ ] View tracker across platforms (postponed)
- [ ] Decide where the system runs day to day (your PC or a small cloud server)
