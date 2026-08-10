import os
import sys
import subprocess
from pathlib import Path

def generate_ico():
    print("Generating multi-resolution .ico icon from logo-icon.png...")
    try:
        from PIL import Image
    except ImportError:
        print("Error: Pillow is required to convert PNG to ICO. Please run 'pip install Pillow'")
        sys.exit(1)
        
    png_path = Path("frontend/assets/logo-icon.png")
    ico_path = Path("frontend/assets/logo-icon.ico")
    
    if not png_path.exists():
        print(f"Error: Source image {png_path} not found.")
        sys.exit(1)
        
    img = Image.open(png_path)
    
    # Save as multi-resolution ICO (16x16, 32x32, 48x48, 64x64, 128x128, 256x256)
    img.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"Icon generated successfully at: {ico_path.resolve()}")

def run_pyinstaller():
    print("Compiling Downloader from ABC with PyInstaller...")
    
    # Clean old build/dist files
    for path in [Path("build"), Path("dist")]:
        if path.exists():
            print(f"Cleaning old directory: {path}")
            
    # Determine the pyinstaller executable in the current python environment
    pyinstaller_bin = "pyinstaller"
    py_bin_dir = Path(sys.executable).parent
    pyinstaller_local = py_bin_dir / "pyinstaller"
    pyinstaller_local_exe = py_bin_dir / "pyinstaller.exe"
    
    if pyinstaller_local_exe.exists():
        pyinstaller_bin = str(pyinstaller_local_exe)
    elif pyinstaller_local.exists():
        pyinstaller_bin = str(pyinstaller_local)
        
    ffmpeg_exe = Path("backend/bin/ffmpeg.exe")
    ffprobe_exe = Path("backend/bin/ffprobe.exe")
    if not ffmpeg_exe.exists() or not ffprobe_exe.exists():
        print("Error: FFmpeg binaries not found in backend/bin/. Please ensure ffmpeg.exe and ffprobe.exe are placed there before building.")
        sys.exit(1)

    # PyInstaller command line
    # Windows uses ; as path separator for add-data and add-binary
    cmd = [
        pyinstaller_bin,
        "--noconfirm",
        "--onefile",
        "--add-data", "frontend;frontend",
        "--add-binary", "backend/bin/ffmpeg.exe;bin",
        "--add-binary", "backend/bin/ffprobe.exe;bin",
        "--icon", "frontend/assets/logo-icon.ico",
        "--name", "Downloader from ABC",
        "backend/launcher.py"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n" + "="*60)
        print("BUILD SUCCESSFUL!")
        print(f"Executable output: {Path('dist/Downloader from ABC.exe').resolve()}")
        print("="*60 + "\n")
    else:
        print(f"\nBuild failed with exit code: {result.returncode}")
        sys.exit(result.returncode)

def main():
    # Ensure working directory is the project root
    os.chdir(Path(__file__).resolve().parent)
    
    generate_ico()
    run_pyinstaller()

if __name__ == "__main__":
    main()
