"""Local audit preparation. No credentials, network requests or research results."""

from pathlib import Path

TEMPLATES = ["events.csv", "discovery_coverage.csv"]


def prepare_audit(destination="data", templates="templates"):
    destination = Path(destination).resolve()
    root = Path("data").resolve()
    if destination != root and root not in destination.parents:
        raise ValueError("Audit working files must stay within ./data (ignored by Git)")
    destination.mkdir(parents=True, exist_ok=True)
    result = {"created": [], "preserved": []}
    for filename in TEMPLATES:
        target = destination / filename
        if target.exists():
            result["preserved"].append(str(target))
            continue
        # Exclusive creation also protects against accidental concurrent overwrites.
        contents = (Path(templates) / filename).read_text(encoding="utf-8")
        with target.open("x", encoding="utf-8", newline="") as stream:
            stream.write(contents)
        result["created"].append(str(target))
    return result
