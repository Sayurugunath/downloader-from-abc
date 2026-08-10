# Downloader from ABC

<p align="center">
  <img src="frontend/assets/logo.png" alt="Downloader from ABC Logo" width="160" style="border-radius: 32px; box-shadow: 0 10px 30px rgba(0,0,0,0.15);">
</p>

Downloader from ABC is a local web application for analyzing supported media URLs and managing downloads through a simple browser interface. It uses FastAPI to serve the frontend and API, and `yt-dlp` to inspect and download media.

Developed by Sayuru Gunathilaka
Version: v1.0.0

> [!IMPORTANT]
> Downloader from ABC is intended for content you are authorized to download. You are responsible for complying with the terms, rights, and laws that apply to the source content.

---

## Features

- **Media Analyzer:** Paste any supported media URL to analyze and display available video qualities and audio formats.
- **Queue Manager:** Track active and completed downloads in real-time. Start, pause, resume, cancel, and retry jobs.
- **Progress Tracking:** Real-time visibility of progress percentages, downloaded size, transfer speed, and ETA.
- **Settings Customization:** Customize default quality preferences, remember last selected format, toggle browser notifications, hide/show speed and ETA, and select dark/light themes.
- **Automatic Cleanup:** Automated cleanup scheduler for temporary files and old download history logs (configurable from the settings menu).

---

## Screenshots

We provide screenshots illustrating the application's clean, high-contrast visual design, layout, and functionality:

### Main Dashboard
![Main Dashboard](https://raw.githubusercontent.com/sayuru1/downloader-from-abc/main/docs/screenshots/main-ui.png)

### Format Selection
![Format Selection](https://raw.githubusercontent.com/sayuru1/downloader-from-abc/main/docs/screenshots/format-selection.png)

### Active Downloads
![Active Downloads](https://raw.githubusercontent.com/sayuru1/downloader-from-abc/main/docs/screenshots/downloading.png)

### Settings Configuration
![Settings Configuration](https://raw.githubusercontent.com/sayuru1/downloader-from-abc/main/docs/screenshots/settings.png)

---

## Windows Application Setup (For Users)

Downloader from ABC is packaged as a standalone Windows application. You do **not** need to install Python, configure virtual environments, or run terminal command lines manually.

### How to Install
1. Download the release package (`Downloader-from-ABC-v1.0.0.zip`) and extract it to a folder.
2. Open the extracted folder, right-click `install.ps1`, and select **Run with PowerShell** (or run `.\install.ps1` from a PowerShell window).
3. The installer will copy the program files to your local programs folder and create **Desktop** and **Start Menu** shortcuts.
4. You can uninstall the application at any time through the Windows **Add or Remove Programs** Control Panel.

### How to Launch
* Double-click the **Downloader from ABC** shortcut on your Desktop or search for it in your Start Menu.
* The application starts its backend server automatically in the background and opens the dashboard in your default web browser on localhost.

---

## Firefox Cookies and Privacy

Downloader from ABC integrates `yt-dlp`'s native browser cookie engine. It reads cookies from your local Firefox profile configuration only when accessing resources that require active authentication (e.g., age-restricted or private media you are authorized to access).

- **Privacy Isolation:** Active cookie databases and credentials never leave your machine. They are **not** stored, persistent, packaged, uploaded, or exposed by this application.
- **Local Access only:** The backend binds strictly to `127.0.0.1` (localhost). It does not receive requests from outside networks, ensuring your browser session remains secure.

> [!CAUTION]
> **Localhost Binding Security:**
> Downloader from ABC is configured to run on localhost (`127.0.0.1`). Do not bind it to `0.0.0.0` or expose the API port to untrusted networks. Exposing the API without authorization layers allows untrusted actors to trigger downloads and access stored local files.

---

## FFmpeg Integration

For downloading high-definition video files (e.g. 1080p, 4K, 8K), `yt-dlp` requires **FFmpeg** to merge separate video and audio streams.

* **Bundled Release:** The official packaged Windows release of **Downloader from ABC** fully bundles pre-compiled FFmpeg binaries. There is **zero manual setup** required for the end user.
* **Source Builds / Devs:** If you are running the project from source code, ensure `ffmpeg.exe` and `ffprobe.exe` are placed in the `backend/bin/` directory or configured in your system `PATH`.

---

## Developer Setup

If you want to run or build Downloader from ABC from source, follow these steps:

### Prerequisites
- Python 3.10 or newer (tested on Python 3.13)
- Node.js (optional, used for development javascript syntax validation)

### 1. Installation
Clone the repository:
```bash
git clone https://github.com/Sayuru-Gunathilaka/Downloader-from-ABC.git
cd Downloader-from-ABC
```

Set up a virtual environment and install dependencies:
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 2. Run in Development Mode
```bash
cd backend
uvicorn server:app --reload --host 127.0.0.1 --port 8000
```
Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your web browser.

### 3. Build the Windows Executable
To compile the standalone `.exe` file using PyInstaller:
```bash
python build.py
```
The compiled output is saved under `dist/Downloader from ABC.exe`.

---

## Troubleshooting

- **FFmpeg errors or missing merged audio:** If building from source, ensure `ffmpeg.exe` is in `backend/bin/` or in your system `PATH`. For packaged executable users, verify the bundled binaries are intact.
- **Cookie/browser database locked:** Close Firefox if its active profile database is locked, as this prevents `yt-dlp` from reading cookie sessions.
- **Port 8000 already in use:** The launcher dynamically searches for a free port starting from 8000. If running in development mode, configure a different port using uvicorn: `--port 8080`.
- **Analysis fails:** Ensure your network is active and update `yt-dlp` to its latest release to bypass media platform API changes (`pip install --upgrade yt-dlp`).

---

## License

Downloader from ABC is released under the [MIT License](LICENSE).
Copyright © 2026 Sayuru Gunathilaka
