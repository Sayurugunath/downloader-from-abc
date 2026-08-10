# Downloader from ABC - Uninstaller Script
# Developed by Sayuru Gunathilaka
# Version: 1.0.0

$ErrorActionPreference = "Continue"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Uninstalling Downloader from ABC v1.0.0..." -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan

# Define paths
$InstallDir = "$env:LOCALAPPDATA\Programs\Downloader from ABC"
$StartMenuDir = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs"
$DesktopDir = [System.Environment]::GetFolderPath("Desktop")

# Stop any running processes to prevent file lock issues
$RunningProcesses = Get-Process -Name "Downloader from ABC" -ErrorAction SilentlyContinue
if ($RunningProcesses) {
    Write-Host "Stopping running instances of Downloader from ABC to prevent file locks..." -ForegroundColor Yellow
    $RunningProcesses | Stop-Process -Force
    Start-Sleep -s 1
}

# Remove shortcuts
Write-Host "Removing shortcuts..." -ForegroundColor Yellow
$StartMenuShortcut = Join-Path $StartMenuDir "Downloader from ABC.lnk"
if (Test-Path $StartMenuShortcut) {
    Remove-Item -Path $StartMenuShortcut -Force
}

$DesktopShortcut = Join-Path $DesktopDir "Downloader from ABC.lnk"
if (Test-Path $DesktopShortcut) {
    Remove-Item -Path $DesktopShortcut -Force
}

# Remove Registry entry
Write-Host "Removing Windows Registry entries..." -ForegroundColor Yellow
$RegPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\Downloader from ABC"
if (Test-Path $RegPath) {
    Remove-Item -Path $RegPath -Recurse -Force
}

# Clean installation directory
Write-Host "Removing program files..." -ForegroundColor Yellow
if (Test-Path $InstallDir) {
    Remove-Item -Path $InstallDir -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Uninstall completed successfully!" -ForegroundColor Green
Write-Host "Remaining temporary logs or folders will be deleted shortly." -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
