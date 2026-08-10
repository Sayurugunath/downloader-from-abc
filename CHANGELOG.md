# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project uses [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-08-11

### Added
- **Windows Standalone Packaging:** Compiles a native, portable, self-contained Windows executable (`Downloader from ABC.exe`) using PyInstaller.
- **PowerShell Installer/Uninstaller:** Native PowerShell installation setup (`install.ps1`, `uninstall.ps1`) to manage desktop and start menu shortcuts, install program directories, and register with Windows Add/Remove Programs.
- **Application Launcher:** Dynamic backend listener starting on free ports automatically, opening browser dashboards, and cleanly managing uvicorn logs.
- **AppData Isolation:** Dynamic SQLite and temporary files management pointing to `%LOCALAPPDATA%` when run in packaged format, leaving system settings isolated.
- **Developer Attribution:** Attribution to developer Sayuru Gunathilaka.
- **Branding Assets:** Multi-resolution icons (`logo-icon.ico`) and clean asset structure.
- **CI Pipelines:** Automated GitHub Actions workflows for continuous integration validation and automated Windows releases compilation.

### Changed
- Refactored brand identity from DownLy to "Downloader from ABC".
- Simplified and improved visual dashboard theme with bold high-contrast red/black aesthetics matching the brand logo.
