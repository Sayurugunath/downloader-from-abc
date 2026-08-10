import sys
import os
import yt_dlp
from pathlib import Path

IS_FROZEN = getattr(sys, "frozen", False)

if IS_FROZEN:
    DOWNLOAD_DIR = Path(os.environ.get("USERPROFILE", Path.home())) / "Downloads"
    FFMPEG_DIR = Path(sys._MEIPASS) / "bin"
else:
    DOWNLOAD_DIR = Path(__file__).resolve().parent.parent / "downloads"
    FFMPEG_DIR = Path(__file__).resolve().parent / "bin"

DOWNLOAD_DIR.mkdir(exist_ok=True)


def get_video_info(url: str):
    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "cookiesfrombrowser": ("firefox",),
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)

    formats = []

    for fmt in info.get("formats", []):
        formats.append({
            "format_id": fmt.get("format_id"),
            "ext": fmt.get("ext"),
            "resolution": fmt.get("resolution"),
            "fps": fmt.get("fps"),
            "filesize": fmt.get("filesize"),
            "vcodec": fmt.get("vcodec"),
            "acodec": fmt.get("acodec"),
        })

    return {
        "title": info.get("title"),
        "thumbnail": info.get("thumbnail"),
        "duration": info.get("duration"),
        "uploader": info.get("uploader"),
        "formats": formats,
    }


def download_video(url: str, format_id=None):
    options = {
        "format": format_id or "best",
        "outtmpl": str(DOWNLOAD_DIR / "%(title)s.%(ext)s"),
        "noplaylist": True,
        "cookiesfrombrowser": ("firefox",),
        "merge_output_format": "mp4",
    }

    # Add dynamic ffmpeg location if available
    ffmpeg_exe = FFMPEG_DIR / "ffmpeg.exe"
    if ffmpeg_exe.exists():
        options["ffmpeg_location"] = str(FFMPEG_DIR)

    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([url])