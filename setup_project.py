"""Install or repair the local application: python setup_project.py."""

import os
import subprocess
import sys
import venv
from pathlib import Path


def ensure_environment(root):
    """Reuse the environment and bootstrap bundled pip if setup was interrupted."""
    python = (
        root / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    )
    if not python.exists():
        # Bootstrap explicitly below, including when an earlier setup left no pip.
        venv.EnvBuilder(with_pip=False, symlinks=os.name != "nt").create(root / ".venv")
    elif not (root / ".venv" / "pyvenv.cfg").exists():
        raise SystemExit(
            "Folder .venv tidak dikenali sebagai virtual environment; periksa/cadangkan folder itu sebelum instalasi."
        )
    result = subprocess.run(
        [str(python), "-m", "pip", "--version"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("Pip belum tersedia di .venv. Memulihkan dengan ensurepip...", flush=True)
        try:
            subprocess.run(
                [str(python), "-m", "ensurepip", "--upgrade"], cwd=root, check=True
            )
            subprocess.run(
                [str(python), "-m", "pip", "--version"], cwd=root, check=True
            )
        except subprocess.CalledProcessError as error:
            raise SystemExit(
                "Pemulihan pip gagal. Gunakan instalasi Python 3.12 lengkap dengan pip/ensurepip, "
                "lalu ulangi python setup_project.py. Data proyek tidak dihapus."
            ) from error
    return python


def main():
    if sys.version_info < (3, 10):
        raise SystemExit("Gunakan Python 3.12 (minimal 3.10).")
    root = Path(__file__).resolve().parent
    try:
        python = ensure_environment(root)
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
    except subprocess.CalledProcessError as error:
        raise SystemExit(
            "Instalasi belum selesai. Periksa error di atas, perbaiki penyebabnya, "
            "lalu ulangi python setup_project.py. Jalankan aplikasi setelah instalasi berhasil."
        ) from error
    except OSError as error:
        raise SystemExit(f"Environment tidak dapat dijalankan: {error}") from error
    print("\nInstalasi selesai. Jalankan: python run.py")
    print(
        "Model sentimen sekitar 500 MB diunduh saat NLP pertama kali; key diisi melalui browser."
    )


if __name__ == "__main__":
    main()
