#!/usr/bin/env python3
import subprocess, sys, os, venv
from pathlib import Path

VENV_DIR = Path(".venv")
REQUIREMENTS = Path("requirements.txt")
MAIN_SCRIPT = "core/api/main.py"

def sh(cmd, cwd=None):
    print(f"$ {cmd}")
    subprocess.check_call(cmd, shell=True, cwd=cwd or os.getcwd())

def main():
    if not REQUIREMENTS.exists():
        print("requirements.txt not found")
        sys.exit(1)

    if not VENV_DIR.exists():
        print("Creating virtual environment...")
        venv.create(VENV_DIR, with_pip=True)

    python = VENV_DIR / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    pip = VENV_DIR / ("Scripts/pip.exe" if os.name == "nt" else "bin/pip")

    if not python.exists():
        print("Virtual environment broken — recreate")
        sh(f"rm -rf {VENV_DIR}")
        venv.create(VENV_DIR, with_pip=True)

    print("Installing dependencies...")
    sh(f"{pip} install -q -r {REQUIREMENTS}")

    print("Killing any process on port 8889...")
    subprocess.run("lsof -ti :8889 | xargs kill -9 2>/dev/null", shell=True)

    print(f"Starting Codely on http://localhost:8889")
    os.chdir(Path(__file__).parent)
    os.execvp(str(python), [str(python), MAIN_SCRIPT])

if __name__ == "__main__":
    main()
