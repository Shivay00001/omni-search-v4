import os
import subprocess
import sys

def bundle():
    print("--- Omni Search Backend Bundler ---")
    
    # Check for PyInstaller
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Build Command
    print("Building executable (this may take a minute)...")
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--console",
        "--name", "omni_backend",
        "--hidden-import", "g4f",
        "--hidden-import", "fastapi",
        "--hidden-import", "uvicorn",
        "--hidden-import", "duckduckgo_search",
        "main.py"
    ]
    
    try:
        subprocess.check_call(cmd)
        print("\nSUCCESS! Backend bundled into 'dist/omni_backend.exe'")
        print("You can now run the backend without a Python environment.")
    except Exception as e:
        print(f"\nERROR: Bundling failed. {e}")

if __name__ == "__main__":
    bundle()
