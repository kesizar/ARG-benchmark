"""Generate target-v1 results from a frozen manifest and isolated runs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from harness.protocol_report import report  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--runs", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8-sig"))
    summaries = []
    unreadable = []
    for directory in sorted(Path(args.runs).glob("*/*/*")):
        if directory.is_dir() and not (directory / "summary.json").is_file():
            record = {"path": str(directory), "reason": "missing_summary"}
            try:
                state = json.loads((directory / "run_state.json").read_text(encoding="utf-8"))
                record["last_run_state"] = {key: state.get(key) for key in
                                            ("status", "task_id", "run_kind", "obs_mode", "pid", "started_at", "error_type", "protocol_identity")}
            except (OSError, UnicodeError, ValueError, AttributeError):
                pass
            unreadable.append(record)
    for path in sorted(Path(args.runs).glob("*/*/*/summary.json")):
        try:
            item = json.loads(path.read_text(encoding="utf-8-sig"))
            if not isinstance(item, dict):
                raise ValueError("summary 不是对象")
            summaries.append(item)
        except (OSError, UnicodeError, ValueError) as exc:
            unreadable.append({"path": str(path), "reason": str(exc)})
    result = report(manifest, summaries)
    result["unreadable"] = unreadable
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
