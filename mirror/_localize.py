"""Point the downloaded exhibition at local files and drop the analytics tag."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "involuntary-appetite"
TEXT = {".html", ".css", ".js", ".svg"}
BASE_RE = re.compile(r"<!--lg-game-cdn-base-->.*?<!--/lg-game-cdn-base-->", re.S)
ANALYTICS_RE = re.compile(r"<!--lg-game-analytics-->.*?<!--/lg-game-analytics-->\s*", re.S)
URL_CTOR_RE = re.compile(
    r'new URL\(([^,]+), "https://lineargame\.top/games/step2/"\)'
)
PREFIX = "https://lineargame.top/games/step2"


def main() -> None:
    changed = 0
    for path in ROOT.rglob("*"):
        if path.suffix.lower() not in TEXT:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        updated = BASE_RE.sub("", text)
        updated = ANALYTICS_RE.sub("", updated)
        updated = URL_CTOR_RE.sub(r'new URL(\1, location.origin + "/step2/")', updated)
        updated = updated.replace(PREFIX, "/step2")
        if updated != text:
            path.write_text(updated, encoding="utf-8", newline="\n")
            changed += 1
    print(f"rewrote {changed} files")


if __name__ == "__main__":
    main()
