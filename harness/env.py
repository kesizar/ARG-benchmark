"""Load repository .env without overriding variables already set in the process."""

from __future__ import annotations

import os
from pathlib import Path


def load_env(repo_root: Path) -> None:
    path = Path(repo_root) / ".env"
    if not path.is_file():
        return
    try:
        from dotenv import load_dotenv

        load_dotenv(path, override=False)
        return
    except ImportError:
        pass
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
