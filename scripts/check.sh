#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Uses the active Python environment. No API key or real-data calls required.
python -m unittest discover -s tests -v
python -m genshin_research audit
