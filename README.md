# Stream Shorts

Automated, permission-aware short-video production pipeline.

## MVP workflow
1. Submit a source URL (Twitch/YouTube) or upload a local video.
2. Worker downloads/ingests the source, transcribes audio, scores candidate moments.
3. Creates approximately 45–75 second vertical clips (9:16) with subtitles.
4. Clips enter a review queue. **Publishing is not enabled in this MVP**; connect and verify platform OAuth/API credentials before enabling automatic publishing.

## Defaults
- Sources: Twitch, YouTube, local uploads
- Candidate type: interesting moments (heuristics in MVP)
- Target: 3 clips/day
- Review required before publishing
- One account per platform
- Only content owned by you or licensed/authorized for reuse

## Run locally
```bash
cp .env.example .env
docker compose up --build
```
Open http://localhost:8000

## Notes
- FFmpeg and yt-dlp are used for media processing.
- Whisper transcription runs locally; set `WHISPER_MODEL` to control model size.
- This is an early MVP: scoring is heuristic, not semantic highlight detection yet.
- For long-running production, use persistent storage and a dedicated worker. Do not expose the admin API without a strong token.
