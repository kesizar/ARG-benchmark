#!/usr/bin/env python3
"""Create a conservative, reproducible comparison of community listings to the 748 records."""

import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/discovery/english-community/source-listings-2026-10-27.json"
BASE = ROOT / "data/preparation/catalogue.json"
OUTPUT = ROOT / "data/discovery/english-community/comparison-2026-10-27.json"


def normalize(value):
    value = unicodedata.normalize("NFKC", str(value)).casefold().strip()
    value = re.sub(r"\s*[（(][^()（）]*[）)]\s*$", "", value)
    return re.sub(r"[^\w]+", "", value, flags=re.UNICODE)


def main():
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    base = json.loads(BASE.read_text(encoding="utf-8"))["records"]
    base_names = defaultdict(list)
    for record in base:
        original = record.get("original", {})
        if not original:
            continue
        title = next(iter(original.values()))
        key = normalize(title)
        if key:
            base_names[key].append({"record_id": record["record_id"], "title": title})

    groups = defaultdict(list)
    entries = []
    for entry in source["records"]:
        key = normalize(entry["title"])
        match = base_names.get(key, []) if key else []
        out = dict(entry)
        out["normalized_title"] = key
        out["baseline_title_matches"] = match
        out["baseline_comparison"] = "possible_exact_normalized_title" if match else "no_exact_title_match"
        out["identity_and_alias_review"] = "pending"
        out["game_entry_and_playability"] = "not_checked"
        entries.append(out)
        if key:
            groups[key].append({"source": entry["source"], "source_line": entry["source_line"], "title": entry["title"]})

    cross_source = [
        {"normalized_title": key, "entries": group}
        for key, group in groups.items()
        if len({entry["source"] for entry in group}) > 1
    ]
    result = {
        "schema_version": 1,
        "as_of": source["collection_date"],
        "comparison_method": "Conservative normalized title equality against the first original field; not URL, aliases, author, translation or version matching. Matches and nonmatches require review.",
        "limitations": ["Source rows are not independently verified games.", "Cross-source normalized names may refer to distinct works.", "Different names or translations can denote the same work.", "Riddler statuses describe its catalog and must not be interpreted as original-game release or availability."],
        "source_row_counts": dict(Counter(entry["source"] for entry in entries)),
        "source_rows": len(entries),
        "rows_with_baseline_title_match": sum(bool(entry["baseline_title_matches"]) for entry in entries),
        "rows_without_baseline_title_match": sum(not entry["baseline_title_matches"] for entry in entries),
        "distinct_normalized_title_keys": len(groups),
        "cross_source_title_groups": len(cross_source),
        "baseline_matched_rows": [entry for entry in entries if entry["baseline_title_matches"]],
        "cross_source_possible_duplicates": cross_source,
        "entries": entries,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("source_row_counts", "source_rows", "rows_with_baseline_title_match", "rows_without_baseline_title_match", "distinct_normalized_title_keys", "cross_source_title_groups")}, ensure_ascii=True))


if __name__ == "__main__":
    main()
