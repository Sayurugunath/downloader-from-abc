import threading
import uuid
import time
import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import yt_dlp


# ==========================================
# APP
# ==========================================

app = FastAPI(
    title="Downloader from ABC API",
    version="1.0.0",
)


# ==========================================
# PATHS
# ==========================================

import sys
import os

IS_FROZEN = getattr(sys, "frozen", False)

if IS_FROZEN:
    # PyInstaller temporary extraction directory
    BASE_DIR = Path(sys._MEIPASS) / "backend"
    FRONTEND_DIR = Path(sys._MEIPASS) / "frontend"
    FFMPEG_DIR = Path(sys._MEIPASS) / "bin"
    
    # Packaged production directories in user profile/AppData
    APP_DATA_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "Downloader from ABC"
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    DATABASE_FILE = APP_DATA_DIR / "downloads.db"
    
    # We download directly to the User's Windows Downloads directory
    DOWNLOAD_DIR = Path(os.environ.get("USERPROFILE", Path.home())) / "Downloads"
else:
    BASE_DIR = Path(__file__).resolve().parent
    FRONTEND_DIR = BASE_DIR.parent / "frontend"
    DOWNLOAD_DIR = BASE_DIR / "downloads"
    DATABASE_FILE = BASE_DIR / "downloads.db"
    FFMPEG_DIR = BASE_DIR / "bin"

DOWNLOAD_DIR.mkdir(exist_ok=True)


# ==========================================
# DATABASE
# ==========================================

def get_db():
    db = sqlite3.connect(
        DATABASE_FILE,
        check_same_thread=False,
        timeout=30.0,
    )
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA journal_mode=WAL")
    except sqlite3.OperationalError:
        pass
    return db


def init_database():
    db = get_db()

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS downloads (
            job_id TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            format_id TEXT,
            title TEXT,
            thumbnail TEXT,
            status TEXT,
            progress REAL DEFAULT 0,
            downloaded INTEGER DEFAULT 0,
            total INTEGER,
            speed REAL,
            eta INTEGER,
            filename TEXT,
            path TEXT,
            error TEXT,
            created_at REAL,
            updated_at REAL
        )
        """
    )

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )

    db.execute(
        """
        INSERT OR IGNORE INTO app_settings (key, value)
        VALUES ('auto_cleanup', 'true')
        """
    )

    db.commit()
    db.close()


init_database()


# ==========================================
# FLAGS
# ==========================================

cancel_flags = {}
pause_flags = {}
last_db_updates = {}


# ==========================================
# MODELS
# ==========================================

class VideoRequest(BaseModel):
    url: str


class DownloadRequest(BaseModel):
    url: str
    format_id: str | None = None
    title: str | None = None
    thumbnail: str | None = None


class ServerSettingsRequest(BaseModel):
    auto_cleanup: bool


# ==========================================
# DATABASE HELPERS
# ==========================================

def update_job(job_id, **fields):
    if not fields:
        return

    fields["updated_at"] = time.time()

    assignments = ", ".join(
        f"{key} = ?" for key in fields
    )

    values = list(fields.values())
    values.append(job_id)

    db = get_db()

    db.execute(
        f"""
        UPDATE downloads
        SET {assignments}
        WHERE job_id = ?
        """,
        values,
    )

    db.commit()
    db.close()


def get_job(job_id):
    db = get_db()

    row = db.execute(
        """
        SELECT *
        FROM downloads
        WHERE job_id = ?
        """,
        (job_id,),
    ).fetchone()

    db.close()

    return dict(row) if row else None


def get_all_jobs():
    db = get_db()

    rows = db.execute(
        """
        SELECT *
        FROM downloads
        ORDER BY created_at DESC
        """
    ).fetchall()

    db.close()

    return [dict(row) for row in rows]


def automatic_cleanup_enabled():
    db = get_db()
    row = db.execute(
        "SELECT value FROM app_settings WHERE key = 'auto_cleanup'"
    ).fetchone()
    db.close()
    return not row or row["value"] == "true"


@app.get("/api/settings")
def get_server_settings():
    return {"auto_cleanup": automatic_cleanup_enabled()}


@app.put("/api/settings")
def update_server_settings(request: ServerSettingsRequest):
    db = get_db()
    db.execute(
        """
        INSERT INTO app_settings (key, value) VALUES ('auto_cleanup', ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        ("true" if request.auto_cleanup else "false",),
    )
    db.commit()
    db.close()
    return {"auto_cleanup": request.auto_cleanup}


# ==========================================
# ANALYZE
# ==========================================

@app.post("/api/analyze")
def analyze_video(request: VideoRequest):
    try:
        # Import here so the server keeps the same project structure.
        from downloader import get_video_info
        from formats import clean_formats

        info = get_video_info(request.url)

        cleaned = clean_formats(
            info["formats"]
        )

        return {
            "success": True,
            "data": {
                "title": info["title"],
                "thumbnail": info["thumbnail"],
                "duration": info["duration"],
                "uploader": info["uploader"],
                "qualities": cleaned["qualities"],
                "audio": cleaned["audio"],
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


# ==========================================
# DOWNLOAD WORKER
# ==========================================

def run_download(
    job_id,
    url,
    format_id,
):
    cancel_flags[job_id] = False
    pause_flags[job_id] = False

    update_job(
        job_id,
        status="downloading",
    )

    def progress_hook(data):
        status = data.get("status")

        # ----------------------------------
        # CANCEL
        # ----------------------------------

        if cancel_flags.get(
            job_id,
            False,
        ):
            raise yt_dlp.utils.DownloadCancelled(
                "Download cancelled"
            )

        # ----------------------------------
        # PAUSE
        # ----------------------------------

        if pause_flags.get(
            job_id,
            False,
        ):
            raise yt_dlp.utils.DownloadCancelled(
                "Download paused"
            )

        # ----------------------------------
        # PROGRESS
        # ----------------------------------

        if status == "downloading":
            now = time.time()
            last_update = last_db_updates.get(job_id, 0.0)
            
            if now - last_update >= 0.5:
                total = (
                    data.get("total_bytes")
                    or data.get("total_bytes_estimate")
                )
                downloaded = data.get("downloaded_bytes", 0)
                progress = 0.0
                if total:
                    progress = (downloaded / total) * 100
                
                update_job(
                    job_id,
                    progress=round(progress, 1),
                    downloaded=downloaded,
                    total=total,
                    speed=data.get("speed"),
                    eta=data.get("eta"),
                )
                last_db_updates[job_id] = now

        elif status == "finished":
            update_job(
                job_id,
                progress=100,
                status="processing",
            )

    # ======================================
    # OUTPUT
    # ======================================

    output_template = str(
        DOWNLOAD_DIR
        / f"{job_id}_%(title)s.%(ext)s"
    )

    options = {
        "format": format_id or "best",
        "outtmpl": output_template,
        "noplaylist": True,

        # Use Firefox cookies on this machine.
        "cookiesfrombrowser": (
            "firefox",
        ),

        "merge_output_format": "mp4",

        "progress_hooks": [
            progress_hook,
        ],

        # Keep partial files for resume.
        "continuedl": True,
        "nopart": False,
    }

    # Add dynamic ffmpeg location if available
    ffmpeg_exe = FFMPEG_DIR / "ffmpeg.exe"
    if ffmpeg_exe.exists():
        options["ffmpeg_location"] = str(FFMPEG_DIR)

    try:
        with yt_dlp.YoutubeDL(
            options
        ) as ydl:

            info = ydl.extract_info(
                url,
                download=True,
            )

        # ==================================
        # PAUSED
        # ==================================

        if pause_flags.get(
            job_id,
            False,
        ):
            update_job(
                job_id,
                status="paused",
            )
            return

        # ==================================
        # CANCELLED
        # ==================================

        if cancel_flags.get(
            job_id,
            False,
        ):
            update_job(
                job_id,
                status="cancelled",
            )

            if automatic_cleanup_enabled():
                cleanup_job_files(job_id)

            return

        # ==================================
        # FIND FILE
        # ==================================

        requested_downloads = list(
            DOWNLOAD_DIR.glob(
                f"{job_id}_*"
            )
        )

        if not requested_downloads:
            raise RuntimeError(
                "Downloaded file could not be found."
            )

        final_file = requested_downloads[0]

        # ==================================
        # CLEAN NAME
        # ==================================

        clean_name = final_file.name.replace(
            f"{job_id}_",
            "",
            1,
        )

        clean_file = (
            DOWNLOAD_DIR / clean_name
        )

        if final_file != clean_file:

            if clean_file.exists():
                clean_file.unlink()

            final_file.rename(
                clean_file
            )

        # ==================================
        # COMPLETED
        # ==================================

        file_size = clean_file.stat().st_size

        update_job(
            job_id,
            status="completed",
            progress=100,
            downloaded=file_size,
            total=file_size,
            filename=clean_file.name,
            path=str(clean_file),
            title=(
                info.get("title")
                or clean_file.stem
            ),
            speed=None,
            eta=None,
        )

    except yt_dlp.utils.DownloadCancelled:

        if pause_flags.get(
            job_id,
            False,
        ):
            update_job(
                job_id,
                status="paused",
            )

        else:
            update_job(
                job_id,
                status="cancelled",
            )

            if automatic_cleanup_enabled():
                cleanup_job_files(job_id)

    except Exception as e:

        if pause_flags.get(
            job_id,
            False,
        ):
            update_job(
                job_id,
                status="paused",
            )

        elif cancel_flags.get(
            job_id,
            False,
        ):
            update_job(
                job_id,
                status="cancelled",
            )

            if automatic_cleanup_enabled():
                cleanup_job_files(job_id)

        else:
            error_msg = str(e)
            if "cookie" in error_msg.lower() and "lock" in error_msg.lower():
                error_msg = "Firefox cookie database is locked (please close Firefox and try again)."
            elif "firefox" in error_msg.lower() and ("not found" in error_msg.lower() or "could not find" in error_msg.lower()):
                error_msg = "Could not locate your Firefox installation. Please install Firefox or ensure a profile is set up."
            elif "ffmpeg" in error_msg.lower():
                error_msg = "FFmpeg binary is missing or failed to post-process. Please check your installation."
                
            update_job(
                job_id,
                status="error",
                error=error_msg,
            )

    finally:
        cancel_flags.pop(
            job_id,
            None,
        )

        pause_flags.pop(
            job_id,
            None,
        )


# ==========================================
# CLEAN JOB FILES
# ==========================================

def cleanup_job_files(job_id):
    for file in DOWNLOAD_DIR.glob(
        f"{job_id}_*"
    ):
        try:
            if file.is_file():
                file.unlink()
            elif file.is_dir():
                import shutil
                shutil.rmtree(file)
        except OSError:
            pass


# ==========================================
# START DOWNLOAD
# ==========================================

@app.post("/api/download")
def start_download(
    request: DownloadRequest,
):
    job_id = str(
        uuid.uuid4()
    )

    now = time.time()

    db = get_db()

    db.execute(
        """
        INSERT INTO downloads (
            job_id,
            url,
            format_id,
            title,
            thumbnail,
            status,
            progress,
            downloaded,
            total,
            speed,
            eta,
            filename,
            path,
            error,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            job_id,
            request.url,
            request.format_id,
            request.title
            or "Preparing download...",
            request.thumbnail,
            "queued",
            0,
            0,
            None,
            None,
            None,
            None,
            None,
            None,
            now,
            now,
        ),
    )

    db.commit()
    db.close()

    thread = threading.Thread(
        target=run_download,
        args=(
            job_id,
            request.url,
            request.format_id,
        ),
        daemon=True,
    )

    thread.start()

    return {
        "success": True,
        "job_id": job_id,
    }


# ==========================================
# ALL DOWNLOADS
# ==========================================

@app.get("/api/downloads")
def download_history():
    return {
        "success": True,
        "downloads": get_all_jobs(),
    }


# ==========================================
# PROGRESS
# ==========================================

@app.get(
    "/api/progress/{job_id}"
)
def download_progress(
    job_id: str,
):
    job = get_job(
        job_id
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Download job not found",
        )

    return job


# ==========================================
# PAUSE
# ==========================================

@app.post(
    "/api/pause/{job_id}"
)
def pause_download(
    job_id: str,
):
    job = get_job(
        job_id
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Download job not found",
        )

    if job["status"] != "downloading":
        raise HTTPException(
            status_code=400,
            detail="Download is not active.",
        )

    pause_flags[job_id] = True

    return {
        "success": True,
    }


# ==========================================
# RESUME
# ==========================================

@app.post(
    "/api/resume/{job_id}"
)
def resume_download(
    job_id: str,
):
    job = get_job(
        job_id
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Download job not found",
        )

    if job["status"] != "paused":
        raise HTTPException(
            status_code=400,
            detail="Download is not paused.",
        )

    thread = threading.Thread(
        target=run_download,
        args=(
            job_id,
            job["url"],
            job["format_id"],
        ),
        daemon=True,
    )

    thread.start()

    return {
        "success": True,
    }


# ==========================================
# CANCEL
# ==========================================

@app.post(
    "/api/cancel/{job_id}"
)
def cancel_download(
    job_id: str,
):
    job = get_job(
        job_id
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Download job not found",
        )

    if job["status"] not in (
        "queued",
        "downloading",
        "processing",
        "paused",
    ):
        raise HTTPException(
            status_code=400,
            detail="Download cannot be cancelled.",
        )

    cancel_flags[job_id] = True
    pause_flags[job_id] = False

    update_job(
        job_id,
        status="cancelled",
    )

    return {
        "success": True,
    }


# ==========================================
# RETRY
# ==========================================

@app.post(
    "/api/retry/{job_id}"
)
def retry_download(
    job_id: str,
):
    job = get_job(
        job_id
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Download job not found",
        )

    if job["status"] not in (
        "error",
        "cancelled",
    ):
        raise HTTPException(
            status_code=400,
            detail="Only failed or cancelled downloads can be retried.",
        )

    if automatic_cleanup_enabled():
        cleanup_job_files(job_id)

    update_job(
        job_id,
        status="queued",
        progress=0,
        downloaded=0,
        total=None,
        speed=None,
        eta=None,
        filename=None,
        path=None,
        error=None,
    )

    thread = threading.Thread(
        target=run_download,
        args=(
            job_id,
            job["url"],
            job["format_id"],
        ),
        daemon=True,
    )

    thread.start()

    return {
        "success": True,
        "job_id": job_id,
    }


# ==========================================
# CLEAR HISTORY
# ==========================================

@app.delete("/api/downloads")
def clear_history():
    db = get_db()

    rows = db.execute(
        """
        SELECT job_id, path
        FROM downloads
        WHERE status IN (
            'completed',
            'cancelled',
            'error'
        )
        """
    ).fetchall()

    for row in rows:
        path = row["path"]

        if path:
            try:
                file = Path(path)

                if file.exists():
                    file.unlink()

            except OSError:
                pass

        cleanup_job_files(
            row["job_id"]
        )

    db.execute(
        """
        DELETE FROM downloads
        WHERE status IN (
            'completed',
            'cancelled',
            'error'
        )
        """
    )

    db.commit()
    db.close()

    return {
        "success": True,
    }


# ==========================================
# FILE
# ==========================================

@app.get(
    "/api/file/{job_id}"
)
def download_file(
    job_id: str,
):
    job = get_job(
        job_id
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Download job not found",
        )

    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail="Download is not complete",
        )

    file_path = Path(
        job["path"]
    )

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="File no longer exists",
        )

    return FileResponse(
        file_path,
        filename=job["filename"],
        media_type="application/octet-stream",
    )


# ==========================================
# AUTOMATIC CLEANUP
# ==========================================

def cleanup_old_downloads():
    while True:
        try:
            time.sleep(
                6 * 60 * 60
            )

            if not automatic_cleanup_enabled():
                continue

            cutoff = (
                time.time()
                - (
                    7
                    * 24
                    * 60
                    * 60
                )
            )

            db = get_db()

            rows = db.execute(
                """
                SELECT job_id, path
                FROM downloads
                WHERE status = 'completed'
                AND updated_at < ?
                """,
                (cutoff,),
            ).fetchall()

            for row in rows:

                if row["path"]:
                    try:
                        file = Path(
                            row["path"]
                        )

                        if file.exists():
                            file.unlink()

                    except OSError:
                        pass

                cleanup_job_files(
                    row["job_id"]
                )

            db.execute(
                """
                DELETE FROM downloads
                WHERE status = 'completed'
                AND updated_at < ?
                """,
                (cutoff,),
            )

            db.commit()
            db.close()

        except Exception:
            pass


cleanup_thread = threading.Thread(
    target=cleanup_old_downloads,
    daemon=True,
)

cleanup_thread.start()


# ==========================================
# FRONTEND
# MUST BE MOUNTED LAST
# ==========================================

app.mount(
    "/",
    StaticFiles(
        directory=FRONTEND_DIR,
        html=True,
    ),
    name="frontend",
)
