from pathlib import Path
from threading import Thread
from fastapi import FastAPI, HTTPException, Header, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, HttpUrl
from app.config import settings
from app.db import connect, init_db

app = FastAPI(title=settings.app_name)

class SourceRequest(BaseModel):
    url: HttpUrl

def auth(token: str | None):
    if not settings.admin_token or settings.admin_token == "change-me":
        raise HTTPException(503, "Set a secure ADMIN_TOKEN before using the API")
    if token != settings.admin_token:
        raise HTTPException(401, "Unauthorized")

@app.on_event("startup")
def startup():
    init_db()
    from app.worker import worker_loop
    Thread(target=worker_loop, daemon=True, name="media-worker").start()

@app.get("/", response_class=HTMLResponse)
def dashboard():
    with connect() as c:
        jobs = c.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT 50").fetchall()
        clips = c.execute("SELECT * FROM clips ORDER BY id DESC LIMIT 100").fetchall()
    html = "<h1>Stream Shorts — Review queue</h1><p>Clips require review before publishing. Submit a source using the API.</p><h2>Jobs</h2><table border='1' cellpadding='8'><tr><th>ID</th><th>Source</th><th>Status</th><th>Details</th></tr>"
    for j in jobs:
        html += f"<tr><td>{j['id']}</td><td>{j['source_url']}</td><td>{j['status']}</td><td>{j['error'] or ''}</td></tr>"
    html += "</table><h2>Clips</h2><table border='1' cellpadding='8'><tr><th>ID</th><th>Job</th><th>Title</th><th>Timecode</th><th>Status</th><th>Preview</th></tr>"
    for cl in clips:
        html += f"<tr><td>{cl['id']}</td><td>{cl['job_id']}</td><td>{cl['title']}</td><td>{cl['start_seconds']:.0f}–{cl['end_seconds']:.0f}s</td><td>{cl['status']}</td><td><a href='/clips/{cl['id']}'>video</a></td></tr>"
    html += "</table>"
    return html

@app.post("/api/sources")
def submit_source(payload: SourceRequest, x_admin_token: str = Header(default="")):
    auth(x_admin_token)
    with connect() as c:
        cur = c.execute("INSERT INTO jobs(source_url,status) VALUES(?, 'queued')", (str(payload.url),))
        return {"job_id": cur.lastrowid, "status": "queued"}

@app.post("/api/upload")
async def upload(file: UploadFile = File(...), x_admin_token: str = Header(default="")):
    auth(x_admin_token)
    allowed = {".mp4", ".mkv", ".mov", ".webm"}
    suffix = Path(file.filename or "video.mp4").suffix.lower()
    if suffix not in allowed:
        raise HTTPException(400, "Unsupported video file")
    inbox = settings.data_dir / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename or "video.mp4").name
    target = inbox / safe_name
    with target.open("wb") as out:
        while chunk := await file.read(1024 * 1024):
            out.write(chunk)
    with connect() as c:
        cur = c.execute("INSERT INTO jobs(source_url,status) VALUES(?, 'queued')", (target.as_uri(),))
        return {"job_id": cur.lastrowid, "status": "queued"}

@app.get("/clips/{clip_id}")
def clip_file(clip_id: int):
    with connect() as c:
        row = c.execute("SELECT file_path FROM clips WHERE id=?", (clip_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Clip not found")
    path = Path(row["file_path"])
    if not path.exists():
        raise HTTPException(404, "Clip file missing")
    return FileResponse(path, media_type="video/mp4", filename=path.name)
