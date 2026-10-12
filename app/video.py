"""Build a narrated MP4 slideshow (ffmpeg) from slide titles + an audio overview MP3."""
import os
import subprocess

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
W, H = 1280, 720
PALETTE = ["0x1b1b1f", "0x12263a", "0x2b1a30", "0x1a2b22", "0x2b2412", "0x201a2b"]


def _probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 60.0


def _esc(s):
    return s.replace("\\", "\\\\").replace("'", "\\'").replace(":", "\\:").replace("%", "\\%")


def make_slideshow(nb_id, slides, audio_mp3):
    data = os.getenv("DATA_DIR", "/data")
    out_dir = os.path.join(data, "video", nb_id)
    os.makedirs(out_dir, exist_ok=True)
    dur = _probe(audio_mp3)
    n = max(1, len(slides))
    per = max(2.5, round(dur / n, 2))
    clips = []
    for i, s in enumerate(slides):
        png = os.path.join(out_dir, f"s{i}.png")
        color = PALETTE[i % len(PALETTE)]
        text = _esc((s.get("title") or f"Slide {i+1}")[:68])
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
             "-i", f"color=c={color}:s={W}x{H}:d=1",
             "-vf", f"drawtext=fontfile={FONT}:text='{text}':fontcolor=white:fontsize=52:x=(w-text_w)/2:y=(h-text_h)/2",
             "-frames:v", "1", png], check=True)
        clip = os.path.join(out_dir, f"c{i}.mp4")
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", png, "-t", str(per),
             "-vf", "format=yuv420p", "-c:v", "libx264", "-pix_fmt", "yuv420p", clip], check=True)
        clips.append(clip)
    concat = os.path.join(out_dir, "list.txt")
    with open(concat, "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")
    out = os.path.join(out_dir, "video-overview.mp4")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", concat,
         "-i", audio_mp3, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-shortest", "-movflags", "+faststart", out], check=True)
    return out