# Downloader from ABC - Installer Script
# Developed by Sayuru Gunathilaka
# Version: 1.0.0

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Installing Downloader from ABC v1.0.0..." -ForegroundColor Green
Write-Host "Developed by Sayuru Gunathilaka" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Define installation paths
$InstallDir = "$env:LOCALAPPDATA\Programs\Downloader from ABC"
$StartMenuDir = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs"
$DesktopDir = [System.Environment]::GetFolderPath("Desktop")

# Source binary path
$SourceExe = Join-Path $PSScriptRoot "dist\Downloader from ABC.exe"
if (-not (Test-Path $SourceExe)) {
    # Fallback to current script directory in case it's packaged differently
    $SourceExe = Join-Path $PSScriptRoot "Downloader from ABC.exe"
}

if (-not (Test-Path $SourceExe)) {
    Write-Error "Error: Source executable 'Downloader from ABC.exe' not found in dist or current directory. Please run 'python build.py' first."
    exit 1
}

# Stop any running processes to prevent file lock issues
$RunningProcesses = Get-Process -Name "Downloader from ABC" -ErrorAction SilentlyContinue
if ($RunningProcesses) {
    Write-Host "Stopping running instances of Downloader from ABC to prevent file locks..." -ForegroundColor Yellow
    $RunningProcesses | Stop-Process -Force
    Start-Sleep -s 1
}

# Create installation directory
if (-not (Test-Path $InstallDir)) {
    New-Item -Path $InstallDir -ItemType Directory | Out-Null
}

Write-Host "Copying files to $InstallDir..." -ForegroundColor Yellow
Copy-Item -Path $SourceExe -Destination (Join-Path $InstallDir "Downloader from ABC.exe") -Force

# Copy uninstall script
$UninstallScriptSource = Join-Path $PSScriptRoot "uninstall.ps1"
if (Test-Path $UninstallScriptSource) {
    Copy-Item -Path $UninstallScriptSource -Destination (Join-Path $InstallDir "uninstall.ps1") -Force
} else {
    Write-Warning "Warning: uninstall.ps1 not found in source directory. Uninstaller script will not be copied."
}

# Create Shortcuts
Write-Host "Creating shortcuts..." -ForegroundColor Yellow
$WshShell = New-Object -ComObject WScript.Shell

# Start Menu Shortcut
$StartMenuShortcutPath = Join-Path $StartMenuDir "Downloader from ABC.lnk"
$StartMenuShortcut = $WshShell.CreateShortcut($StartMenuShortcutPath)
$StartMenuShortcut.TargetPath = Join-Path $InstallDir "Downloader from ABC.exe"
$StartMenuShortcut.WorkingDirectory = $InstallDir
$StartMenuShortcut.IconLocation = "$(Join-Path $InstallDir 'Downloader from ABC.exe'),0"
$StartMenuShortcut.Description = "Downloader from ABC - Developed by Sayuru Gunathilaka"
$StartMenuShortcut.Save()

# Desktop Shortcut
$DesktopShortcutPath = Join-Path $DesktopDir "Downloader from ABC.lnk"
$DesktopShortcut = $WshShell.CreateShortcut($DesktopShortcutPath)
$DesktopShortcut.TargetPath = Join-Path $InstallDir "Downloader from ABC.exe"
$DesktopShortcut.WorkingDirectory = $InstallDir
$DesktopShortcut.IconLocation = "$(Join-Path $InstallDir 'Downloader from ABC.exe'),0"
$DesktopShortcut.Description = "Downloader from ABC - Developed by Sayuru Gunathilaka"
$DesktopShortcut.Save()

# Register Uninstaller in Windows (Current User context)
Write-Host "Registering uninstaller in Windows Add/Remove Programs..." -ForegroundColor Yellow
$RegPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\Downloader from ABC"

if (-not (Test-Path $RegPath)) {
    New-Item -Path $RegPath -Force | Out-Null
}

$UninstallString = "powershell.exe -ExecutionPolicy Bypass -Command `"Copy-Item -Path '$InstallDir\uninstall.ps1' -Destination '$env:TEMP\downloader_uninstall.ps1' -Force; powershell.exe -ExecutionPolicy Bypass -File '$env:TEMP\downloader_uninstall.ps1'`""

Set-ItemProperty -Path $RegPath -Name "DisplayName" -Value "Downloader from ABC"
Set-ItemProperty -Path $RegPath -Name "UninstallString" -Value $UninstallString
Set-ItemProperty -Path $RegPath -Name "DisplayIcon" -Value (Join-Path $InstallDir "Downloader from ABC.exe")
Set-ItemProperty -Path $RegPath -Name "DisplayVersion" -Value "1.0.0"
Set-ItemProperty -Path $RegPath -Name "Publisher" -Value "Developed by Sayuru Gunathilaka"
Set-ItemProperty -Path $RegPath -Name "EstimatedSize" -Value ([int]((Get-Item (Join-Path $InstallDir "Downloader from ABC.exe")).Length / 1KB)) -Type DWord

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Installation completed successfully!" -ForegroundColor Green
Write-Host "You can now run Downloader from ABC from your Start Menu or Desktop." -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
