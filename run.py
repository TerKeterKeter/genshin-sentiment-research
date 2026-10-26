"""Start the application after checking its virtual environment dependencies."""

import json
import os
import subprocess
import sys
from pathlib import Path

MODULES = [
    "flask",
    "requests",
    "numpy",
    "scipy",
    "sklearn",
    "matplotlib",
    "langdetect",
    "transformers",
    "torch",
]


def main(argv=None):
    root = Path(__file__).resolve().parent
    python = (
        root / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    )
    if not python.exists():
        print("Jalankan python setup_project.py terlebih dahulu.", file=sys.stderr)
        return 1
    probe_code = (
        "import importlib.util,json; "
        f"print(json.dumps([name for name in {MODULES!r} if importlib.util.find_spec(name) is None]))"
    )
    try:
        probe = subprocess.run(
            [str(python), "-c", probe_code], cwd=root, capture_output=True, text=True
        )
        if probe.returncode != 0:
            print(
                "Environment belum dapat diperiksa. Ulangi python setup_project.py.",
                file=sys.stderr,
            )
            return 1
        missing = json.loads(probe.stdout)
        if missing:
            print(
                "Instalasi belum lengkap. Modul belum tersedia: "
                + ", ".join(missing)
                + ". Jalankan python setup_project.py sampai muncul Instalasi selesai.",
                file=sys.stderr,
            )
            return 1
        return subprocess.call(
            [
                str(python),
                "-m",
                "genshin_research",
                "serve",
                *(sys.argv[1:] if argv is None else argv),
            ],
            cwd=root,
        )
    except (OSError, ValueError) as error:
        print(
            f"Environment tidak dapat dijalankan: {error}. Ulangi python setup_project.py.",
            file=sys.stderr,
        )
        return 1
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
