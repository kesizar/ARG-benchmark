"""Frozen delivery inventory, safe extraction and a common evaluator CLI.

An engineering compatibility check is not scientific acceptance. Source ZIPs
are never patched; all runs use this release's shared harness.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import os
import re
import shutil
import socket
import stat
import sys
import uuid
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inside(root: Path, relative: str) -> Path:
    """Reject absolute paths, traversal, ADS and Windows paths on every OS."""
    name = str(relative).replace("\\", "/")
    parts = PurePosixPath(name).parts
    if not name or name.startswith("/") or ":" in name or ".." in parts:
        raise ValueError(f"Unsafe relative path: {relative}")
    target = (root / name).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes delivery: {relative}")
    return target


def archive_names(archive: zipfile.ZipFile) -> set[str]:
    names = set()
    for item in archive.infolist():
        name = item.filename
        # ZIP members do not yet exist on disk. Validate their lexical paths
        # here; extract() separately checks each actual destination.
        if (not name or name.startswith("/") or ":" in name or ".." in PurePosixPath(name).parts
                or "\\" in name or stat.S_ISLNK(item.external_attr >> 16)):
            raise ValueError(f"Unsupported ZIP link/path: {name}")
        if not item.is_dir():
            if name in names:
                raise ValueError(f"Duplicate ZIP member: {name}")
            names.add(name)
    return names


def extract(archive_path: Path, destination: Path) -> None:
    # Destination must be new, so previous runs cannot inject state or links.
    destination.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(archive_path) as archive:
        names = archive_names(archive)
        for name in sorted(names):
            target = inside(destination, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(name) as source, target.open("xb") as output:
                shutil.copyfileobj(source, output)


def inspect_archive(path: Path, schema: dict) -> list[dict]:
    """Inspect declared task entries, not incidental support/test configs."""
    from jsonschema import Draft202012Validator
    from harness.config import apply_defaults, apply_obs_mode, entry_allowed
    from harness.judge import Judge
    from harness.protocol_budget import validate_budget
    from harness.validate import runtime_problems

    validator = Draft202012Validator(schema)
    with zipfile.ZipFile(path) as archive:
        names = archive_names(archive)
        if any(PurePosixPath(n).name == ".env" for n in names):
            raise ValueError("ZIP contains a .env; remove credentials before delivery")
        specs = []
        for name in sorted(names):
            if PurePosixPath(name).name == "protocol-task-spec.json":
                document = json.loads(archive.read(name).decode("utf-8-sig"))
                for task in document.get("tasks", []):
                    config = str(task.get("config", "")).replace("\\", "/")
                    if config not in names:
                        config = str(PurePosixPath(name).parent / config)
                    specs.append((config, task))
        if not specs:
            for name in sorted(names):
                if name.endswith(".json") and (name.startswith("configs/") or "/" not in name):
                    try:
                        cfg = json.loads(archive.read(name).decode("utf-8-sig"))
                        if isinstance(cfg, dict) and "category" in cfg and "model_visible" in cfg:
                            specs.append((name, {}))
                    except (UnicodeError, ValueError):
                        continue
        if not specs:
            return [{"task_id": None, "config": None, "errors": ["No shared-harness task config found"],
                     "official_blockers": [], "warnings": []}]
        result, seen = [], set()
        for config, spec in specs:
            if config in seen:
                continue
            seen.add(config)
            errors, official, warnings = [], [], []
            row = {"config": config, "task_id": spec.get("id"), "spec": spec,
                   "errors": errors, "official_blockers": official, "warnings": warnings}
            result.append(row)
            try:
                inside(Path.cwd(), config)
                cfg = json.loads(archive.read(config).decode("utf-8-sig"))
                row["task_id"] = cfg.get("id")
                errors.extend(f"Config {e.json_path}: {e.message}" for e in validator.iter_errors(cfg))
                cfg = apply_obs_mode(apply_defaults(cfg))
                row["runtime_layer"] = cfg["runtime_layer"]
                row["obs_mode"] = cfg["obs_mode"]
                errors.extend(runtime_problems(cfg))
                if not entry_allowed(cfg):
                    errors.append("entry_url is outside allow_hosts")
                judge_path = str(cfg.get("judge_path") or "")
                inside(Path.cwd(), judge_path)
                judge_cfg = json.loads(archive.read(judge_path).decode("utf-8-sig"))
                judge = Judge(judge_cfg, cfg["id"])
                if judge.protocol != "target_v1":
                    official.append("Judge is not target_v1")
                if cfg["obs_mode"] in {"B", "C"} and not cfg.get("require_images"):
                    official.append("B/C official mode requires require_images=true")
                try:
                    validate_budget(spec, cfg)
                except (ValueError, TypeError, KeyError) as exc:
                    official.append(str(exc))
                for field, member in (("config_sha256", config), ("judge_sha256", judge_path)):
                    if spec.get(field) and hashlib.sha256(archive.read(member)).hexdigest() != spec[field]:
                        official.append(f"Task spec {field} does not match ZIP bytes")
                server = cfg.get("local_serve") or {}
                if server.get("enabled"):
                    command = server.get("command") or []
                    cwd = str(server.get("cwd") or ".")
                    inside(Path.cwd(), cwd)
                    if not command:
                        errors.append("Missing local server command")
                    for arg in command:
                        if re.match(r"^(?:[A-Za-z]:[\\/]|/(?:Users|home|opt)/)", str(arg)):
                            errors.append("Server command contains a machine-specific absolute path")
                    if len(command) > 1 and str(command[1]).endswith(".py"):
                        script = str(PurePosixPath(cwd) / str(command[1]))
                        if script not in names:
                            errors.append(f"Missing server script: {script}")
                if cfg["category"] == "text_adventure" and not cfg.get("grid") and not cfg.get("scenario"):
                    errors.append("Text adventure requires a separately verified interpreter")
                if cfg["runtime_layer"] == "L3":
                    warnings.append("Live website/account/reset conditions must be checked before running")
                row["account_requirement"] = cfg.get("account_requirement", "unknown")
            except (KeyError, ValueError, TypeError, AttributeError) as exc:
                errors.append(f"Cannot load shared-harness entry: {exc}")
        return result


def load_release(root: Path) -> tuple[dict, dict]:
    if (root / "BUILD-INCOMPLETE.json").exists():
        raise ValueError("Delivery build is incomplete")
    expected = (root / "RELEASE.json.sha256").read_text(encoding="ascii").split()[0]
    if sha256(root / "RELEASE.json") != expected:
        raise ValueError("RELEASE.json checksum changed")
    release = read_json(root / "RELEASE.json")
    if sha256(root / "catalogue.json") != release["files"]["catalogue.json"]:
        raise ValueError("catalogue.json checksum changed; restore the original release")
    return release, read_json(root / "catalogue.json")


def select(catalogue: dict, key: str) -> dict:
    matches = [t for t in catalogue["tasks"] if key in (t["key"], t.get("task_id"), t["record_id"])]
    if len(matches) != 1:
        raise ValueError(f"Task selector {key!r} matches {len(matches)} entries; use an exact key from list")
    return matches[0]


def verify(root: Path, release: dict, tasks: list[dict], all_files=False) -> list[str]:
    failures = []
    expected = dict(release["files"])
    for task in tasks:
        expected[task["archive"]] = task["archive_sha256"]
    if all_files:
        expected.update(release["archives"])
    for name, digest in expected.items():
        path = inside(root, name)
        if not path.is_file() or sha256(path) != digest:
            failures.append(f"Missing or changed: {name}")
    return failures


def environment(root: Path, api=False, browser=False) -> dict:
    checks = {"python": {"ok": sys.version_info >= (3, 11), "actual": sys.version.split()[0]}}
    for line in (root / "requirements-delivery.lock").read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        name, expected = line.split("==")
        try:
            actual = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            actual = "not installed"
        checks[name] = {"ok": actual == expected, "actual": actual, "expected": expected}
    if api:
        from harness.env import load_env
        load_env(root)
        provider = os.environ.get("LLM_PROVIDER", "openai").strip().lower()
        if provider == "anthropic":
            fields = ("ANTHROPIC_API_KEY", "ANTHROPIC_MODEL")
        elif provider == "openai":
            fields = ("OPENAI_API_KEY", "OPENAI_MODEL")
        else:
            fields = ()
            checks["provider"] = {"ok": False, "actual": "Use openai or anthropic"}
        for name in fields:
            checks[name] = {"ok": bool(os.environ.get(name, "").strip()), "actual": "set" if os.environ.get(name, "").strip() else "missing"}
        checks["api_note"] = {"ok": True, "actual": "Configuration only; no API request was sent"}
    if browser:
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as playwright:
                instance = playwright.chromium.launch(headless=True)
                checks["chromium"] = {"ok": True, "actual": instance.version}
                instance.close()
        except Exception as exc:
            checks["chromium"] = {"ok": False, "actual": f"{type(exc).__name__}: install Chromium with python -m playwright install chromium"}
    return checks


def run_task(root: Path, release: dict, task: dict, args) -> int:
    problems = list(task["errors"])
    official = args.command == "run" and args.official
    if official:
        problems.extend(task["official_blockers"])
        if not args.manifest or args.repetition is None or args.policy != "llm":
            problems.append("Official runs require --policy llm --manifest PATH --repetition N")
    problems.extend(verify(root, release, [task]))
    policy = "script" if args.command == "smoke" else args.policy
    checks = environment(root, api=policy == "llm")
    problems.extend(f"Environment: {k} ({v['actual']})" for k, v in checks.items() if not v["ok"])
    if problems:
        raise ValueError("\n".join(problems))
    from harness.env import load_env
    from harness.loop import run
    load_env(root)  # One .env at the delivery root for every extracted task.
    os.environ["BENCHMARK_BROWSER_CHANNEL"] = "chromium"
    manifest = read_json(Path(args.manifest).resolve()) if official else None
    if official and not os.environ.get("LLM_EXPERIMENT_PROFILE", "").strip():
        raise ValueError("Set LLM_EXPERIMENT_PROFILE to the frozen model profile ID")
    session_name = getattr(args, "session_name", None) or uuid.uuid4().hex
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", session_name):
        raise ValueError("Invalid session identifier")
    session = root / "work" / session_name
    bundle = session / "bundle"
    extract(inside(root, task["archive"]), bundle)
    config = inside(bundle, task["config"])
    cfg = read_json(config)
    server = cfg.get("local_serve") or {}
    if server.get("enabled"):
        parsed = urlparse(server.get("ready_url") or cfg.get("entry_url", ""))
        if parsed.hostname and parsed.port:
            try:
                connection = socket.create_connection((parsed.hostname, parsed.port), timeout=0.5)
            except OSError:
                pass
            else:
                connection.close()
                raise ValueError(f"Game port {parsed.port} is already in use; stop the previous game before running")
    if args.command == "smoke":
        cfg["policy_script"] = [{"op": "give_up"}]
        cfg["actions_enabled"] = list(dict.fromkeys([*cfg.get("actions_enabled", []), "give_up"]))
        config = bundle / "delivery-smoke.json"
        write_json(config, cfg)
    receipt = {"release_id": release["id"], "task_key": task["key"], "archive_sha256": task["archive_sha256"],
               "kind": "smoke" if args.command == "smoke" else ("official" if official else "test"),
               "policy": policy, "status": "starting", "bundle": str(bundle),
               "manifest_id": manifest.get("id") if manifest else None}
    receipt_path = session / "receipt.json"
    write_json(receipt_path, receipt)
    print(f"Session: {session}", flush=True)
    try:
        summary = asyncio.run(run(config, policy=policy, repo_root=bundle, run_kind="official" if official else "test",
                                  headless=not args.show, manifest=manifest,
                                  repetition=args.repetition if official else None,
                                  attempt=getattr(args, "attempt", 1)))
        receipt.update(status="completed", ended_reason=summary.get("ended_reason"))
        status = 1 if summary.get("ended_reason") == "error" or summary.get("judge_error") else 0
    except (Exception, SystemExit) as exc:
        # Preserve evidence without printing request headers, keys or response bodies.
        from harness.loop import _model_link_down
        receipt.update(status="error", error_type=type(exc).__name__, retryable=_model_link_down(exc),
                       http_status=getattr(getattr(exc, "response", None), "status_code", None))
        print(f"Run failed: {type(exc).__name__}; inspect local run_state.json and server.log", file=sys.stderr)
        status = 1
    finally:
        write_json(receipt_path, receipt)
    print(f"Receipt: {receipt_path}")
    return status


def batch_tasks(catalogue: dict, args) -> tuple[list[dict], int]:
    if args.official:
        if args.policy != "llm":
            raise ValueError("Official batch requires --policy llm")
        if not args.manifest or args.all_local:
            raise ValueError("Official batch requires --manifest and uses exactly that task list")
        manifest = read_json(Path(args.manifest).resolve())
        tasks = [select(catalogue, item.get("selector", item["id"])) for item in manifest.get("tasks", [])]
        if args.task and {select(catalogue, key)["key"] for key in args.task} != {t["key"] for t in tasks}:
            raise ValueError("Official batch task selection must equal the frozen manifest")
        repeats = manifest.get("repeats", 3)
        if args.repeats is not None and args.repeats != repeats:
            raise ValueError("Repeats must equal the frozen manifest")
    else:
        if args.all_local and args.task:
            raise ValueError("Choose --all-local or explicit --task entries")
        tasks = ([t for t in catalogue["tasks"] if not t["errors"] and t.get("runtime_layer") == "L1"]
                 if args.all_local else [select(catalogue, key) for key in (args.task or [])])
        repeats = args.repeats if args.repeats is not None else 1
    if not tasks or type(repeats) is not int or repeats < 1:
        raise ValueError("Select at least one task and a positive repeat count")
    if len({t["key"] for t in tasks}) != len(tasks):
        raise ValueError("Duplicate tasks in batch")
    blocked = [t["key"] for t in tasks if t["errors"] or (args.official and t["official_blockers"])]
    if blocked:
        raise ValueError(f"Batch contains blocked entries: {', '.join(blocked)}; see list --all")
    return tasks, repeats


def report_runs(root: Path, manifest_path: Path, output: Path) -> dict:
    from harness.protocol_report import report
    manifest = read_json(manifest_path)
    summaries, unreadable = [], []
    for session in sorted((root / "work").glob("*")):
        directories = list((session / "bundle" / "runs").glob("*/*/*"))
        if not directories and (session / "receipt.json").exists():
            unreadable.append({"path": str(session), "reason": "session_has_no_summary"})
        for directory in directories:
            path = directory / "summary.json"
            try:
                summaries.append(read_json(path))
            except (ValueError, OSError) as exc:
                unreadable.append({"path": str(path), "reason": type(exc).__name__})
    result = report(manifest, summaries)
    result["unreadable"] = unreadable
    write_json(output, result)
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="ARG benchmark delivery: list, check, smoke, run")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="command", required=True)
    listing = sub.add_parser("list", help="List frozen tasks and compatibility status")
    listing.add_argument("--all", action="store_true", help="Include blocked entries")
    listing.add_argument("--json", action="store_true")
    doctor = sub.add_parser("doctor", help="Check pinned packages; --api does not spend API credit")
    doctor.add_argument("--api", action="store_true")
    doctor.add_argument("--browser", action="store_true")
    doctor.add_argument("--task")
    doctor.add_argument("--json", action="store_true")
    checking = sub.add_parser("verify", help="Verify release and ZIP checksums")
    checking.add_argument("--task")
    checking.add_argument("--all", action="store_true")
    for command in ("smoke", "run"):
        p = sub.add_parser(command, help="Offline one-action smoke" if command == "smoke" else "Run one independent episode")
        p.add_argument("--task", required=True)
        p.add_argument("--show", action="store_true")
        if command == "run":
            p.add_argument("--policy", choices=("llm", "script"), default="llm")
            p.add_argument("--official", action="store_true")
            p.add_argument("--manifest")
            p.add_argument("--repetition", type=int)
    batch = sub.add_parser("batch", help="Serial batch; official task list comes from its manifest")
    batch.add_argument("--task", action="append")
    batch.add_argument("--all-local", action="store_true", help="All L1 entries that pass engineering checks")
    batch.add_argument("--repeats", type=int)
    batch.add_argument("--policy", choices=("llm", "script"), default="llm")
    batch.add_argument("--official", action="store_true")
    batch.add_argument("--manifest")
    batch.add_argument("--show", action="store_true")
    batch.add_argument("--dry-run", action="store_true", help="Print the plan without contacting a model")
    reporting = sub.add_parser("report", help="Aggregate work/ sessions using a frozen experiment manifest")
    reporting.add_argument("--manifest", type=Path, required=True)
    reporting.add_argument("--out", type=Path, required=True)
    formal = sub.add_parser("experiment", help="Formal cohort, model registration, execution and reporting")
    formal.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        release, catalogue = load_release(root)
        if args.command == "experiment":
            from harness.experiment import main as experiment_main
            return experiment_main(root, args.args)
        if args.command == "report":
            failures = verify(root, release, [])
            if failures:
                raise ValueError("\n".join(failures))
            report_runs(root, args.manifest.resolve(), args.out.resolve())
            print(f"Report: {args.out.resolve()}")
            return 0
        if args.command == "list":
            rows = catalogue["tasks"] if args.all else [t for t in catalogue["tasks"] if not t["errors"]]
            if args.json:
                print(json.dumps(rows, ensure_ascii=False, indent=2))
            else:
                print(f"Release {release['id']} | {len(rows)} entries (engineering status, not scientific acceptance)")
                for t in rows:
                    status = "BLOCKED" if t["errors"] else ("TEST ONLY" if t["official_blockers"] else "PRECHECK OK")
                    print(f"{t['key']}\t{status}\t{t.get('title', '')}")
                    for issue in t["errors"] + t["official_blockers"]:
                        print(f"  {issue}")
            return 0
        if args.command == "batch":
            tasks, repeats = batch_tasks(catalogue, args)
            print(f"Batch: {len(tasks)} tasks x {repeats} repeats; policy={args.policy}; official={args.official}")
            if args.dry_run:
                for entry in tasks:
                    print(entry["key"])
                return 0
            # Check every selected ZIP before the first model request.
            failures = verify(root, release, tasks)
            checks = environment(root, api=args.policy == "llm")
            failures.extend(f"Environment: {k}" for k, value in checks.items() if not value["ok"])
            if failures:
                raise ValueError("\n".join(failures))
            failed = 0
            for entry in tasks:
                for repetition in range(1, repeats + 1):
                    single = argparse.Namespace(**{**vars(args), "command": "run", "repetition": repetition})
                    try:
                        failed += bool(run_task(root, release, entry, single))
                    except (ValueError, OSError) as exc:
                        print(f"Failed {entry['key']}: {exc}", file=sys.stderr)
                        failed += 1
            print(f"Batch complete: {failed} failed attempts. Inspect receipts; exit code is not a score.")
            return int(bool(failed))
        task = select(catalogue, args.task) if getattr(args, "task", None) else None
        if args.command == "verify":
            failures = verify(root, release, [task] if task else [], args.all)
            print("\n".join(failures) if failures else "Checksums OK")
            return bool(failures)
        if args.command == "doctor":
            checks = environment(root, args.api, args.browser)
            for failure in verify(root, release, [task] if task else []):
                checks[failure] = {"ok": False, "actual": "checksum mismatch"}
            if task:
                checks["task"] = {"ok": not task["errors"], "actual": task["errors"] or "Shared-harness precheck passed"}
                checks["official_note"] = {"ok": True, "actual": task["official_blockers"] or "Still requires a frozen experiment manifest and API validation"}
            if args.json:
                print(json.dumps(checks, ensure_ascii=False, indent=2))
            else:
                for name, value in checks.items():
                    print(f"{'OK' if value['ok'] else 'FAIL'} {name}: {value['actual']}")
            return int(any(not value["ok"] for value in checks.values()))
        return run_task(root, release, task, args)
    except (ValueError, OSError, KeyError, zipfile.BadZipFile) as exc:
        print(f"Cannot continue: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
