"""Reconcile the original row-level scope with historical local materials.

This is an inventory, not an assertion that a game works or is fully judged.
Run from the repository root; inputs are explicit so no old agent scripts run.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import json
import re
import unicodedata
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlsplit, urlunsplit


def read_csv(path):
    text = path.read_text(encoding="utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))


def name_key(value):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", value or "")).casefold()


def url_key(value):
    try:
        u = urlsplit((value or "").strip())
        return urlunsplit((u.scheme.lower(), u.netloc.lower(), unquote(u.path).rstrip("/"), u.query, u.fragment))
    except ValueError:
        return value


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(base_csv, added_csv, materials, output):
    output.mkdir(parents=True, exist_ok=True)
    sources = []
    records = []
    for group, path in [("base664", base_csv), ("added84", added_csv)]:
        raw = path.read_bytes()
        copied = output / "sources" / (group + ".csv")
        copied.parent.mkdir(exist_ok=True)
        copied.write_bytes(raw)
        rows = read_csv(path)
        sources.append({"group": group, "original_path": str(path), "snapshot": str(copied), "sha256": digest(path), "rows": len(rows)})
        for line, row in enumerate(rows, 2):
            records.append({"record_id": f"{group}:{line:04d}", "source_group": group, "source_line": line, "original": row})

    reports = []
    for group in ["416", "84"]:
        folder = materials / ("verify-" + group)
        for row in read_csv(folder / "report.csv"):
            reports.append((group, row, folder))

    configs = []
    for path in sorted(Path("configs").glob("*.json")):
        try:
            cfg = json.loads(path.read_text(encoding="utf-8"))
            if "id" not in cfg or "judge_path" not in cfg:
                continue
            configs.append((path, cfg))
        except (ValueError, KeyError):
            continue
    listed = json.loads(Path("configs/verify_from_source.json").read_text(encoding="utf-8"))["tasks"]
    listed_ids = {Path(x).stem for x in listed}
    registry = []
    for folder in [materials / "incoming", materials / "pilot-11"]:
        for path in sorted(folder.glob("*.zip")):
            entry = {"path": str(path), "bytes": path.stat().st_size}
            try:
                with zipfile.ZipFile(path) as archive:
                    members = archive.infolist()
                    entry.update({"zip_index_readable": True, "members": len(members), "uncompressed_bytes": sum(m.file_size for m in members)})
            except (OSError, zipfile.BadZipFile) as exc:
                entry.update({"zip_index_readable": False, "error": str(exc)})
            registry.append(entry)
    repository_materials = []
    for task in sorted(Path("tasks").iterdir()):
        if task.is_dir():
            repository_materials.append({"task_id": task.name, "path": str(task), "immediate_entries": sorted(p.name for p in task.iterdir()), "status": "presence_only_not_revalidated"})
    for rec in records:
        row = rec["original"]
        nk, uk = name_key(row["作品名"]), url_key(row.get("官方入口"))
        rec["materials"] = []
        report_urls = set()
        for group, old, folder in reports:
            # Never join on hostname or unstable historical row number.
            reasons = []
            if name_key(old.get("name")) == nk:
                reasons.append("normalized_title")
            if uk and url_key(old.get("final_url")) == uk:
                reasons.append("full_url")
            if not reasons:
                continue
            report_urls.add(url_key(old.get("final_url")))
            body = folder / "bodies" / (old["line"] + ".html")
            scripts = materials / "mirrors-lite/scripts" / group / old["line"]
            next_page = Path(r"D:\Temp\gatesF\next") / f"{group}_{old['line']}"
            files = sorted(str(p) for p in scripts.glob("*") if p.is_file()) if scripts.exists() else []
            rec["materials"].append({"historical_set": group, "historical_line": old["line"], "match_basis": reasons, "reported_name": old.get("name"), "reported_final_url": old.get("final_url"), "historical_decision": old.get("decision"), "historical_error": old.get("error"), "body_path": str(body) if body.is_file() else None, "body_bytes": body.stat().st_size if body.is_file() else None, "body_sha256": digest(body) if body.is_file() else None, "script_files": files, "next_page_directory": str(next_page) if next_page.is_dir() else None})
        rec["config_candidates"] = []
        for path, cfg in configs:
            reasons = []
            if name_key(cfg.get("model_visible", {}).get("title")) == nk:
                reasons.append("normalized_title")
            cu = url_key(cfg.get("entry_url"))
            if uk and cu == uk:
                reasons.append("full_url")
            elif cu and cu in report_urls:
                reasons.append("historical_redirect_url")
            if not reasons:
                continue
            jp = Path(cfg["judge_path"])
            error = None
            try:
                j = json.loads(jp.read_text(encoding="utf-8"))
                shape = {"checkpoints": len(j.get("checkpoints", [])), "routes": len(j.get("routes", []))}
            except (OSError, ValueError) as exc:
                error = str(exc)
                shape = None
            rec["config_candidates"].append({"id": cfg["id"], "path": str(path), "match_basis": reasons, "title": cfg.get("model_visible", {}).get("title"), "entry_url": cfg.get("entry_url"), "legacy_listed": cfg["id"] in listed_ids, "judge_path": str(jp), "judge_parse_error": error, "judge_shape": shape, "local_serve_enabled": bool(cfg.get("local_serve", {}).get("enabled"))})
        rec["inventory_status"] = "body_present_not_play_verified" if any(m["body_path"] for m in rec["materials"]) else "historical_attempt_no_body" if rec["materials"] else "no_matching_entry_in_two_probe_reports"
        rec["preparation_status"] = "not_revalidated"

    titles = collections.defaultdict(list)
    for rec in records:
        titles[name_key(rec["original"]["作品名"])].append(rec["record_id"])
    duplicates = [{"title": next(r["original"]["作品名"] for r in records if r["record_id"] == ids[0]), "record_ids": ids} for ids in titles.values() if len(ids) > 1]
    names_a = {name_key(r["original"]["作品名"]) for r in records if r["source_group"] == "base664"}
    names_b = {name_key(r["original"]["作品名"]) for r in records if r["source_group"] == "added84"}
    summary = {"scope_unit": "original CSV rows; titles are not unique game IDs", "rows": len(records), "sources": sources, "cross_source_title_overlap": sorted(names_a & names_b), "duplicate_title_groups": duplicates, "inventory_counts": dict(collections.Counter(r["inventory_status"] for r in records)), "rows_with_config_candidate": sum(bool(r["config_candidates"]) for r in records), "rows_with_multiple_config_candidates": sum(len(r["config_candidates"]) > 1 for r in records), "rows_with_legacy_list_candidate": sum(any(c["legacy_listed"] for c in r["config_candidates"]) for r in records), "legacy_list_entries": len(listed), "legacy_bare_paths": [s for s in listed if not s.endswith(".json")], "categories": dict(collections.Counter(r["original"]["类别"] for r in records)), "limitations": ["No live availability check of all 748 rows", "Body presence does not imply complete assets or runnable game", "Title and URL joins produce candidates, not approved game identity", "Only verify-416 and verify-84 probe reports are indexed; unmatched rows may have material elsewhere", "No historical completion label is accepted as full-flow validation"]}
    (output / "catalogue.json").write_text(json.dumps({"schema_version": 1, "records": records}, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "material-registry.json").write_text(json.dumps({"archives": registry, "repository_tasks": repository_materials, "limitations": ["ZIP central directory inspected; content extraction, CRC validation and playability not tested", "Large repository source directories not recursively traversed"]},ensure_ascii=False,indent=2),encoding="utf-8")
    (output / "inventory-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--added", type=Path, required=True)
    parser.add_argument("--materials", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/preparation"))
    args = parser.parse_args()
    audit(args.base, args.added, args.materials, args.output)
