import time
from app.config import settings
from app.db import connect
from app.video import download_source, duration_seconds, transcribe, make_clip
from app.scoring import score_segments

def process_one(job):
    job_id, url = job
    work = settings.data_dir / "processing" / str(job_id)
    try:
        source = download_source(url, work)
        duration = duration_seconds(source)
        if duration > settings.max_source_seconds:
            raise ValueError(f"Source is too long ({duration:.0f}s). Limit is {settings.max_source_seconds}s")
        segments = transcribe(source, settings.whisper_model)
        picks = score_segments(segments, settings.clip_min_seconds, settings.clip_max_seconds)
        clips_dir = settings.data_dir / "clips"
        clips_dir.mkdir(parents=True, exist_ok=True)
        for n, (_, start, end, text) in enumerate(picks, start=1):
            clip_path = clips_dir / f"job{job_id}_clip{n}.mp4"
            make_clip(source, start, end, clip_path, segments)
            with connect() as c:
                c.execute("INSERT INTO clips(job_id,title,start_seconds,end_seconds,file_path,transcript,status) VALUES(?,?,?,?,?,?, 'review')",
                    (job_id, f"Highlight {n}", start, end, str(clip_path), text))
        with connect() as c:
            c.execute("UPDATE jobs SET status='review', error=? WHERE id=?", (f"Candidate clips: {len(picks)}", job_id))
    except Exception as e:
        with connect() as c:
            c.execute("UPDATE jobs SET status='failed', error=? WHERE id=?", (str(e)[:2000], job_id))

def worker_loop():
    while True:
        with connect() as c:
            job = c.execute("SELECT id,source_url FROM jobs WHERE status='queued' ORDER BY id LIMIT 1").fetchone()
            if job:
                c.execute("UPDATE jobs SET status='processing' WHERE id=?", (job["id"],))
        if job:
            process_one((job["id"], job["source_url"]))
        else:
            time.sleep(5)
