"""Export a self-contained, checksum-pinned copy of current code and selected ZIPs."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.delivery import inside, inspect_archive, read_json, sha256, write_json


def build(root: Path, out: Path, index_path: Path, selected: list[str] | None = None, validation_path: Path | None = None, guide: Path | None = None) -> dict:
    out = out.resolve()
    if out.exists():
        raise ValueError("Output already exists; use a new release directory")
    snapshot = index_path.read_bytes()
    index = json.loads(snapshot.decode("utf-8-sig"))
    entries = [p for p in index["packages"] if p.get("status") in {"provisional", "scoped_provisional"}]
    if selected:
        unknown = set(selected) - {p["original_record_id"] for p in entries}
        if unknown:
            raise ValueError(f"Unknown/nonaccepted records: {sorted(unknown)}")
        entries = [p for p in entries if p["original_record_id"] in selected]
    out.mkdir(parents=True)
    # Record an incomplete build so an interrupted copy cannot appear to be ready.
    write_json(out / "BUILD-INCOMPLETE.json", {"started_at": datetime.now(timezone.utc).isoformat()})
    files = ["benchmark.py", "run.ps1", "setup.ps1", "requirements-delivery.lock", "delivery.env.example",
             "docs/delivery.md", "configs/schema/task.schema.json"]
    for name in ("docs/official_run.md", "official.env.example"):
        if (root / name).is_file():
            files.append(name)
    files.extend(p.relative_to(root).as_posix() for p in sorted((root / "harness").glob("*.py")) if not p.name.startswith("test_"))
    files.extend(p for p in ["scripts/report_protocol.py", "scripts/show_model_profile.py",
                            "scripts/prepare_protocol_manifest.py", "scripts/aggregate_runs.py", "exclude/sites.txt"] if (root / p).is_file())
    for name in files:
        destination = inside(out, name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(inside(root, name), destination)
    shutil.copyfile(guide or root / "docs/delivery.md", out / "START-HERE.md")
    (out / "source-index.json").write_bytes(snapshot)
    validation = {}
    if validation_path:
        validation = {row["key"]: row for row in read_json(validation_path)}
        shutil.copyfile(validation_path, out / "startup-validation.json")
    archives, tasks = {}, []
    schema = read_json(root / "configs/schema/task.schema.json")
    for number, entry in enumerate(entries, 1):
        source = inside(root, entry["package"])
        destination = inside(out, f"packages/{number:04d}-{source.name}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        digest = sha256(destination)
        if entry.get("sha256") and entry["sha256"] != digest:
            raise ValueError(f"Source index checksum is stale for {entry['package']}; reconcile it before release")
        relative = destination.relative_to(out).as_posix()
        archives[relative] = digest
        try:
            inspected = inspect_archive(destination, schema)
        except (ValueError, OSError, KeyError) as exc:
            inspected = [{"task_id": None, "config": None, "errors": [f"Archive precheck failed: {exc}"],
                          "official_blockers": [], "warnings": []}]
        for task in inspected:
            record_id = entry["original_record_id"]
            key = record_id if len(inspected) == 1 else f"{record_id}::{task['task_id']}"
            tasks.append({**task, "key": key, "record_id": record_id, "title": entry.get("title", ""),
                          "archive": relative, "archive_sha256": digest, "source_package": entry["package"],
                          "source_status": entry["status"], "scope": entry.get("scope"),
                          "limitations": entry.get("limitations"), "source_review": entry.get("acceptance")})
            if key in validation:
                check = validation[key]
                if check.get("package_sha256") != digest:
                    raise ValueError(f"Startup validation refers to another ZIP version: {key}")
                tasks[-1]["startup_validation"] = {k: check.get(k) for k in
                    ("status", "scope", "runtime_layer", "ended_reason", "screenshots", "notes")}
        print(f"[{number}/{len(entries)}] {entry['original_record_id']}", flush=True)
    keys = [t["key"] for t in tasks]
    if len(keys) != len(set(keys)):
        raise ValueError("Task keys collide; reconcile multi-unit identities before release")
    catalogue = {"source_index_sha256": hashlib.sha256(snapshot).hexdigest(),
                 "source_generated_at": index.get("generated_at_utc"), "tasks": tasks,
                 "excluded_records": [p for p in index["packages"] if p.get("status") == "excluded"],
                 "note": "Engineering prechecks only; no API or full-game scientific acceptance is claimed."}
    write_json(out / "catalogue.json", catalogue)
    tracked = ["START-HERE.md", "source-index.json", "catalogue.json", *files]
    if validation_path:
        tracked.append("startup-validation.json")
    file_hashes = {name: sha256(inside(out, name)) for name in tracked}
    version_digest = hashlib.sha256(json.dumps({"files": file_hashes, "archives": archives}, sort_keys=True).encode()).hexdigest()
    git = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=False)
    release = {"id": f"arg-benchmark-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{version_digest[:12]}",
               "created_at_utc": datetime.now(timezone.utc).isoformat(), "content_sha256": version_digest,
               "source_git_head": git.stdout.strip(), "source_note": "Working-tree files copied; git HEAD alone does not identify this release.",
               "python_baseline": "CPython 3.11", "browser": "Playwright Chromium; run setup.ps1 to install",
               "package_count": len(entries), "task_count": len(tasks),
               "shared_harness_precheck_passed": sum(not t["errors"] for t in tasks),
               "official_config_precheck_passed": sum(not t["errors"] and not t["official_blockers"] for t in tasks),
               "startup_checked_count": sum("startup_validation" in t for t in tasks),
               "startup_passed_count": sum(t.get("startup_validation", {}).get("status") == "pass" for t in tasks),
               "source_status_counts": dict(Counter(p["status"] for p in entries)),
               "files": file_hashes, "archives": archives}
    write_json(out / "RELEASE.json", release)
    (out / "RELEASE.json.sha256").write_text(f"{sha256(out / 'RELEASE.json')}  RELEASE.json\n", encoding="ascii")
    (out / "BUILD-INCOMPLETE.json").unlink()
    return release


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--index", type=Path, default=ROOT / "packs/master-resource-index.json")
    parser.add_argument("--record", action="append", help="Export only selected original record IDs; default all provisionally accepted")
    parser.add_argument("--validation", type=Path, help="Version-matched startup validation summary to include")
    parser.add_argument("--guide", type=Path, help="Primary instructions for this delivery")
    args = parser.parse_args()
    result = build(ROOT, args.out, args.index, args.record, args.validation, args.guide)
    print(json.dumps({k: v for k, v in result.items() if k not in {"files", "archives"}}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
