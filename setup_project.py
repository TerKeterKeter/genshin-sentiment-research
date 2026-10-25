"""Install the local browser application. Run once: python setup_project.py."""

import os
import subprocess
import sys
import venv
from pathlib import Path


def main():
    if sys.version_info < (3, 10):
        raise SystemExit("Gunakan Python 3.12 (minimal 3.10).")
    root = Path(__file__).resolve().parent
    python = (
        root / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    )
    if not python.exists():
        venv.EnvBuilder(with_pip=True, symlinks=os.name != "nt").create(root / ".venv")
    elif not (root / ".venv" / "pyvenv.cfg").exists():
        raise SystemExit(
            "Folder .venv tidak dikenali sebagai virtual environment; periksa/cadangkan folder itu sebelum instalasi."
        )
    commands = [
        [
            str(python),
            "-m",
            "pip",
            "install",
            "torch==2.7.0",
            "--index-url",
            "https://download.pytorch.org/whl/cpu",
        ],
        [str(python), "-m", "pip", "install", "-r", "requirements.txt"],
        [str(python), "-m", "pip", "check"],
    ]
    for command in commands:
        subprocess.run(command, cwd=root, check=True)
    print("\nInstalasi selesai. Jalankan: python run.py")
    print(
        "Model sentimen sekitar 500 MB diunduh saat NLP pertama kali; key diisi melalui browser."
    )


if __name__ == "__main__":
    main()
