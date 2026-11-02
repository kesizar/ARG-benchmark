"""Repair the frozen r1 selection without changing any original ZIP or game asset."""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.delivery import inspect_archive, read_json, sha256, write_json


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def repair_config(cfg: dict, spec: dict) -> list[dict]:
    changes = []

    def set_value(obj, field, value, why):
        if obj.get(field) != value:
            changes.append({"field": field, "before": obj.get(field), "after": value, "reason": why})
            obj[field] = value

    aliases = {"video_reasoning": "web_puzzle", "puzzle": "web_puzzle", "web_arg": "arg", "ARG": "arg"}
    if cfg.get("category") in aliases:
        cfg["source_category"] = cfg["category"]
        set_value(cfg, "category", aliases[cfg["category"]], "Schema category alias only; same browser runtime and game")
    if cfg.get("obs_mode", "B") in {"B", "C"}:
        set_value(cfg, "require_images", True, "B/C already supplies screenshots; forbid silent text-only API fallback")
    limits = cfg["limits"]
    if limits.get("max_answer_submits", 10) != 10:
        if "submit_answer" in cfg.get("actions_enabled", []):
            raise ValueError("Enabled submit_answer needs task-specific evidence; refusing generic budget repair")
        before = limits["max_answer_submits"]
        set_value(limits, "max_answer_submits", 10,
                  "The harness submit_answer action is disabled. UI submissions use click/type and retain native game limits.")
        set_value(spec, "max_answer_submits", 10, "Match the unused harness budget; no game-side submission rule changes")
        cfg.setdefault("notes_for_report", []).append(
            f"Handoff repair: unused harness submit_answer cap {before} -> 10; submit_answer remains disabled. "
            "Native UI retries, one-shot failures and game submission limits are unchanged.")
    if limits["max_steps"] == 400 and spec.get("reference_steps") == 200 and "max_steps_override" not in spec:
        set_value(spec, "max_steps_override", 400, "Preserve existing authored 400-step cap; no budget increase")
        set_value(spec, "step_budget_override_reason",
                  "Retain this package's existing 400-step cap for its 200-step uncalibrated human estimate. "
                  "This records the existing per-task exception under the user-authorized override policy; "
                  "it is not a new measured trajectory or additional budget.", "Make existing exception explicit")
    set_value(spec, "id", cfg["id"], "Use the actual configuration task ID for formal manifest matching")
    return changes


def update_manifest(document, replacements: dict[str, bytes], add_note=False):
    rows = document.get("files") if isinstance(document, dict) else None
    if not isinstance(rows, list):
        return document
    paths = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = row.get("path")
        paths.add(name)
        if name in replacements:
            value = replacements[name]
            row.update(sha256=hashlib.sha256(value).hexdigest(), bytes=len(value))
    if add_note and "HANDOFF-REPAIR.json" not in paths:
        value = replacements["HANDOFF-REPAIR.json"]
        rows.append({"path": "HANDOFF-REPAIR.json", "sha256": hashlib.sha256(value).hexdigest(), "bytes": len(value)})
    return document


def refresh_manifests(archive: zipfile.ZipFile, replacements: dict[str, bytes]) -> None:
    """Resolve manifest dependencies from the inside out."""
    for name in ("PROTOCOL-OVERLAY-MANIFEST.json", "BUNDLE-MANIFEST.json"):
        if name in archive.namelist():
            document = json.loads(archive.read(name).decode("utf-8-sig"))
            replacements[name] = encoded(update_manifest(document, replacements, add_note=name == "BUNDLE-MANIFEST.json"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    release, out = args.release.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    catalogue = read_json(release / "catalogue.json")
    index = read_json(release / "source-index.json")
    records = {p["original_record_id"]: p for p in index["packages"] if p.get("status") != "excluded"}
    schema = read_json(ROOT / "configs/schema/task.schema.json")
    reviews = []
    runtime = ("judge.py", "browser_harness.py", "grid_harness.py", "loop.py", "summary.py")
    for entry in catalogue["tasks"]:
        original = release / entry["archive"]
        record = records[entry["record_id"]]
        record.update(package=original.relative_to(ROOT).as_posix(), sha256=entry["archive_sha256"], bytes=original.stat().st_size)
        if not (entry["errors"] or entry["official_blockers"]):
            continue
        if sha256(original) != entry["archive_sha256"]:
            raise ValueError(f"Frozen ZIP changed: {entry['key']}")
        with zipfile.ZipFile(original) as source:
            names = set(source.namelist())
            spec_name = "protocol-task-spec.json"
            document = json.loads(source.read(spec_name).decode("utf-8-sig"))
            spec = next(t for t in document["tasks"] if t.get("config") == entry["config"])
            cfg = json.loads(source.read(entry["config"]).decode("utf-8-sig"))
            changes = repair_config(cfg, spec)
            config_bytes = encoded(cfg)
            spec["config_sha256"] = hashlib.sha256(config_bytes).hexdigest()
            spec["judge_sha256"] = hashlib.sha256(source.read(cfg["judge_path"])).hexdigest()
            replacements = {entry["config"]: config_bytes, spec_name: encoded(document)}
            for name in runtime:
                for prefix in ("_protocol_runtime/harness/", "harness/"):
                    member = prefix + name
                    if member in names:
                        replacements[member] = (ROOT / "harness" / name).read_bytes()
            note = {"original_record_id": entry["record_id"], "source_release": read_json(release / "RELEASE.json")["id"],
                    "source_zip_sha256": entry["archive_sha256"], "changes": changes,
                    "runtime": "Shared support for existing hook_condition/strict reads and grid reset",
                    "scope": "No game asset, judge definition, answer, or in-game retry rule changed; no model API called."}
            replacements["HANDOFF-REPAIR.json"] = encoded(note)
            refresh_manifests(source, replacements)
            filename = entry["record_id"].replace(":", "-").replace("/", "-") + ".zip"
            target = out / filename
            unchanged = {}
            with zipfile.ZipFile(target, "w") as dest:
                for info in source.infolist():
                    if info.is_dir():
                        dest.writestr(copy.copy(info), b"")
                        continue
                    data = replacements.get(info.filename)
                    if data is None:
                        data = source.read(info.filename)
                        unchanged[info.filename] = hashlib.sha256(data).hexdigest()
                    dest.writestr(copy.copy(info), data)
                for name, data in replacements.items():
                    if name not in names:
                        dest.writestr(name, data, compress_type=zipfile.ZIP_DEFLATED)
        with zipfile.ZipFile(target) as check:
            for name, digest in unchanged.items():
                if hashlib.sha256(check.read(name)).hexdigest() != digest:
                    raise ValueError(f"Unchanged member mutated: {entry['key']} / {name}")
        inspected = inspect_archive(target, schema)
        review = {**note, "package": target.relative_to(ROOT).as_posix(), "sha256": sha256(target),
                  "unchanged_members_verified": len(unchanged), "inspection": inspected}
        review_path = out / (filename + ".review.json")
        write_json(review_path, review)
        record.update(package=target.relative_to(ROOT).as_posix(), sha256=review["sha256"], bytes=target.stat().st_size,
                      source_review=review_path.relative_to(ROOT).as_posix(), acceptance=review_path.relative_to(ROOT).as_posix())
        reviews.append(review)
        print(f"{entry['key']}: errors={sum(len(t['errors']) for t in inspected)}, official={sum(len(t['official_blockers']) for t in inspected)}", flush=True)
    index.update(generated_at_utc=datetime.now(timezone.utc).isoformat(),
                 scope="Same frozen r1 selection with versioned handoff compatibility repairs; scientific acceptance limits retained")
    write_json(out / "index.json", index)
    write_json(out / "repair-summary.json", {"packages": len(reviews), "reviews": reviews})


if __name__ == "__main__":
    main()
