import subprocess, json
from pathlib import Path

def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError((p.stderr or p.stdout)[-3000:])
    return p.stdout

def download_source(url: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    if url.startswith("file://"):
        import urllib.parse
        local = Path(urllib.parse.urlparse(url).path)
        if not local.exists():
            raise FileNotFoundError(local)
        return local
    template = str(out_dir / "source.%(ext)s")
    run(["yt-dlp", "--no-playlist", "--restrict-filenames", "-f", "bestvideo+bestaudio/best", "--merge-output-format", "mp4", "-o", template, url])
    files = list(out_dir.glob("source.*"))
    if not files:
        raise RuntimeError("yt-dlp finished but no source file was created")
    return files[0]

def duration_seconds(path: Path) -> float:
    raw = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)])
    return float(json.loads(raw)["format"]["duration"])

def transcribe(path: Path, model_name: str):
    from faster_whisper import WhisperModel
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(path), vad_filter=True)
    return [{"start": s.start, "end": s.end, "text": s.text.strip()} for s in segments]

def make_clip(source: Path, start: float, end: float, output: Path, transcript_segments):
    output.parent.mkdir(parents=True, exist_ok=True)
    text = " ".join(s["text"] for s in transcript_segments if s["end"] >= start and s["start"] <= end)
    # Keep caption short enough for FFmpeg's drawtext filter; subtitle files are the next iteration.
    text = text[:180].replace("\\", "").replace(":", "\\:").replace("'", "")
    vf = "scale=-2:1920,crop=1080:1920,setsar=1"
    if text:
        vf += f",drawtext=text='{text}':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:fontcolor=white:fontsize=46:borderw=3:bordercolor=black:x=(w-text_w)/2:y=h*0.78"
    run(["ffmpeg", "-y", "-ss", str(start), "-i", str(source), "-t", str(end-start),
         "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
         "-c:a", "aac", "-movflags", "+faststart", str(output)])
