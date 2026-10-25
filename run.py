"""Start the local browser application with the project's virtual environment."""

import os
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    python = (
        root / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    )
    if not python.exists():
        raise SystemExit("Jalankan python setup_project.py terlebih dahulu.")
    raise SystemExit(
        subprocess.call(
            [str(python), "-m", "genshin_research", "serve", *sys.argv[1:]], cwd=root
        )
    )
