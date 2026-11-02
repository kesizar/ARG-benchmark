"""Versioned formal cohorts, model registration and resumable official execution."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
import platform
from pathlib import Path
import re
import zipfile
from urllib.parse import urlsplit


def canonical_hash(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def seal(path: Path, document: dict) -> None:
    from harness.delivery import write_json, sha256
    if path.exists():
        raise ValueError(f"Frozen file already exists: {path}")
    write_json(path, document)
    path.with_suffix(path.suffix + ".sha256").write_text(f"{sha256(path)}  {path.name}\n", encoding="ascii")


def read_sealed(path: Path) -> dict:
    from harness.delivery import read_json, sha256
    expected = path.with_suffix(path.suffix + ".sha256").read_text(encoding="ascii").split()[0]
    if sha256(path) != expected:
        raise ValueError(f"Frozen file checksum changed: {path}")
    return read_json(path)


def freeze_cohort(root: Path, output: Path, cohort_id: str) -> dict:
    from harness.delivery import load_release, verify
    from harness.config import apply_defaults, apply_obs_mode
    from harness.judge import Judge
    from harness.protocol_budget import validate_budget
    release, catalogue = load_release(root)
    problems = verify(root, release, [], all_files=True)
    if problems:
        raise ValueError("\n".join(problems))
    tasks = []
    for item in catalogue["tasks"]:
        if item["errors"] or item["official_blockers"]:
            raise ValueError(f"Unresolved official configuration: {item['key']}")
        with zipfile.ZipFile(root / item["archive"]) as archive:
            config_bytes = archive.read(item["config"])
            cfg = apply_obs_mode(apply_defaults(json.loads(config_bytes.decode("utf-8-sig"))))
            judge_bytes = archive.read(cfg["judge_path"])
            judge = Judge(json.loads(judge_bytes.decode("utf-8-sig")), cfg["id"])
            if judge.protocol != "target_v1":
                raise ValueError(f"Non-target-v1 judge: {item['key']}")
            validate_budget(item["spec"], cfg)
            task = {"id": item["key"], "selector": item["key"], "task_id": cfg["id"],
                    "original_record_id": item["record_id"], "title": item.get("title"),
                    "archive": item["archive"], "archive_sha256": item["archive_sha256"],
                    "config": item["config"], "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
                    "judge": cfg["judge_path"], "judge_sha256": hashlib.sha256(judge_bytes).hexdigest(),
                    "obs_mode": cfg["obs_mode"], "history": cfg["history"], "limits": cfg["limits"],
                    "require_images": bool(cfg.get("require_images")), "runtime_layer": cfg["runtime_layer"],
                    "seed": cfg.get("seed"), "entry_url": cfg.get("entry_url"), "allow_hosts": cfg.get("allow_hosts", []),
                    "account_requirement": cfg.get("account_requirement"),
                    "registered_scope": item["source_status"], "scope": item.get("scope"),
                    "limitations": item.get("limitations"), "acceptance_reference": item.get("source_review"),
                    "progress_scored": item["spec"]["progress_scored"],
                    "good_ending_scored": item["spec"].get("good_ending_scored", False),
                    "terminal_failure_scored": item["spec"].get("terminal_failure_scored", False),
                    "capabilities": [], "descriptive_capabilities": item["spec"].get("capabilities"),
                    "reset": "fresh archive extraction and fresh browser context/environment per attempt"}
            for key in ("reference_steps", "reference_evidence", "max_answer_submits", "required_answer_submits",
                        "answer_budget_evidence", "max_steps_override", "step_budget_override_reason"):
                if key in item["spec"]:
                    task[key] = item["spec"][key]
            tasks.append(task)
    if len({t["id"] for t in tasks}) != len(tasks):
        raise ValueError("Evaluation IDs must be unique")
    document = {"schema": "arg-official-cohort-v1", "id": cohort_id,
                "created_at_utc": datetime.now(timezone.utc).isoformat(), "status": "frozen",
                "delivery": {"id": release["id"], "content_sha256": release["content_sha256"]},
                "obs_mode": "B", "repeats": 3, "required_capabilities": [], "tasks": tasks,
                "execution_order": "Frozen catalogue order; repetitions 1, 2, 3 for each task",
                "environment": {"python_baseline": release["python_baseline"], "browser": release["browser"],
                                "dependency_lock_sha256": release["files"]["requirements-delivery.lock"]},
                "metrics": {"primary": ["SR_macro", "Progress_macro"], "secondary": ["pass3_macro"],
                            "capability_aggregation": "disabled: labels have not been verified as gating capabilities",
                            "missing_progress": "missing; never silently zero", "task_weight": "equal"},
                "retry_policy": {"max_attempts_per_slot": 3, "retry": "transport/timeouts and HTTP 429/500/502/503/504 only",
                                 "valid_failure": "never rerun for a better score", "configuration_error": "stop model"},
                "scope_note": f"{len(tasks)} original records include scoped units; retain every registered scope and limitation. "
                              "Later added/repaired tasks require a new cohort version."}
    seal(output, document)
    return document


@contextmanager
def model_environment(settings: dict, require_key=False):
    provider = settings.get("provider")
    if provider not in {"openai", "anthropic"} or not settings.get("model"):
        raise ValueError("Each model needs provider=openai/anthropic and an actual model ID")
    endpoint = settings.get("base_url", "")
    url = urlsplit(endpoint)
    if url.username or url.password or url.query or url.fragment:
        raise ValueError("Do not put credentials or query parameters in base_url")
    if provider == "openai" and not endpoint.startswith(("https://", "http://127.0.0.1", "http://localhost")):
        raise ValueError("OpenAI-compatible models need an explicit API base_url")
    if provider == "anthropic" and endpoint not in ("", "https://api.anthropic.com/v1"):
        raise ValueError("The native Anthropic adapter uses https://api.anthropic.com/v1")
    key_name = settings.get("api_key_env", "")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key_name):
        raise ValueError("api_key_env must name an environment variable, not contain a key")
    secret = os.environ.get(key_name, "")
    if require_key and not secret:
        raise ValueError(f"Missing credential environment variable: {key_name}")
    names = ("LLM_PROVIDER", "OPENAI_MODEL", "ANTHROPIC_MODEL", "AGENT_MODEL", "OPENAI_BASE_URL", "AGENT_BASE_URL",
             "OPENAI_API_KEY", "AGENT_API_KEY", "ANTHROPIC_API_KEY", "LLM_MAX_OUTPUT_TOKENS", "LLM_TEMPERATURE",
             "LLM_REASONING_EFFORT", "ENABLE_THINKING", "PRESERVE_REASONING", "AGENT_HTTP_TRUST_ENV", "LLM_EXPERIMENT_PROFILE")
    old = {name: os.environ.get(name) for name in names}
    try:
        for name in names:
            os.environ.pop(name, None)
        os.environ.update({"LLM_PROVIDER": provider, "OPENAI_MODEL": settings["model"], "ANTHROPIC_MODEL": settings["model"],
                           "OPENAI_BASE_URL": endpoint, "LLM_MAX_OUTPUT_TOKENS": str(settings.get("max_output_tokens", 32768)),
                           "LLM_REASONING_EFFORT": str(settings.get("reasoning_effort") or ""),
                           "ENABLE_THINKING": str(bool(settings.get("enable_thinking", False))).lower(),
                           "PRESERVE_REASONING": str(bool(settings.get("preserve_reasoning", False))).lower(),
                           "AGENT_HTTP_TRUST_ENV": str(bool(settings.get("http_trust_env", True))).lower()})
        if secret:
            os.environ["ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"] = secret
        yield
    finally:
        for name, value in old.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def register_models(root: Path, plan_path: Path, registry_path: Path, output: Path) -> list[Path]:
    from harness.delivery import load_release, read_json
    from harness.config import apply_defaults, apply_obs_mode
    from harness.policy_llm import LLMPolicy
    from harness.protocol_report import report
    plan = read_sealed(plan_path)
    release, _ = load_release(root)
    if plan.get("schema") != "arg-official-cohort-v1" or plan.get("status") != "frozen":
        raise ValueError("Expected a frozen formal cohort")
    if plan["delivery"]["id"] != release["id"] or plan["delivery"]["content_sha256"] != release["content_sha256"]:
        raise ValueError("Cohort belongs to another delivery version")
    registry = read_json(registry_path)["models"]
    if not isinstance(registry, list) or any(not isinstance(m, dict) or type(m.get("enabled", True)) is not bool for m in registry):
        raise ValueError("models must be a list and enabled must be a JSON boolean")
    models = [m for m in registry if m.get("enabled", True)]
    if not models or len({m["id"] for m in models}) != len(models):
        raise ValueError("Enable at least one model and use distinct model IDs")
    prepared = []
    for model in models:
        allowed = {"id", "enabled", "display_name", "requested_model_id", "provider", "model", "base_url", "api_key_env",
                   "max_output_tokens", "reasoning_effort", "enable_thinking", "preserve_reasoning", "http_trust_env", "profile_id"}
        if set(model) - allowed:
            raise ValueError("Unsupported model fields; keys must only be supplied through api_key_env")
        if type(model.get("max_output_tokens", 32768)) is not int or model.get("max_output_tokens", 32768) <= 0:
            raise ValueError("max_output_tokens must be a positive integer")
        for field in ("enable_thinking", "preserve_reasoning", "http_trust_env"):
            if field in model and type(model[field]) is not bool:
                raise ValueError(f"{field} must be a boolean")
        model_id = model["id"]
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", model_id):
            raise ValueError("Model id must be a simple filename-safe identifier")
        hashes, profiles = {}, []
        with model_environment(model):
            for task in plan["tasks"]:
                with zipfile.ZipFile(root / task["archive"]) as archive:
                    cfg = apply_obs_mode(apply_defaults(json.loads(archive.read(task["config"]).decode("utf-8-sig"))))
                cfg["_run_kind"] = "official"
                policy = LLMPolicy(cfg, output)
                hashes[task["id"]] = policy.profile_sha256()
                profiles.append(policy.profile())
        base = {k: v for k, v in profiles[0].items() if k not in {"obs_mode", "history", "require_images"}}
        if any({k: v for k, v in p.items() if k not in {"obs_mode", "history", "require_images"}} != base for p in profiles):
            raise ValueError("Model request parameters vary across tasks")
        profile_id = model.get("profile_id") or f"{plan['id']}-{model_id}"
        manifest = {**plan, "id": f"{plan['id']}--{model_id}", "schema": "arg-official-experiment-v1",
                    "cohort_id": plan["id"], "cohort_sha256": canonical_hash(plan), "model_settings": model,
                    "models": [{"provider": model["provider"], "name": model["model"], "profile_id": profile_id,
                                "profile_sha256": canonical_hash(base), "parameter_profile": base,
                                "task_profile_sha256": hashes}]}
        report(manifest, [])
        target = output / model_id / "manifest.json"
        prepared.append((target, manifest))
    if any(path.exists() for path, _ in prepared):
        raise ValueError("Model manifest already exists; use a new output/version instead of overwriting")
    for path, manifest in prepared:
        seal(path, manifest)
    return [path for path, _ in prepared]


@contextmanager
def execution_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        handle.seek(0)
        handle.write(b"0")
        handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise ValueError("Another official execution is using this delivery copy") from exc
        try:
            yield
        finally:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def execute(root: Path, manifest_path: Path, retry_auth_error=False) -> int:
    from harness.delivery import load_release, select, verify, read_json, run_task, write_json
    from harness.env import load_env
    from harness.protocol_report import report
    from harness.summary import _exclusion_reason
    manifest = read_sealed(manifest_path)
    release, catalogue = load_release(root)
    if (manifest.get("schema") != "arg-official-experiment-v1" or manifest["delivery"]["id"] != release["id"]
            or manifest["delivery"].get("content_sha256") != release.get("content_sha256")):
        raise ValueError("Formal manifest does not match this delivery")
    report(manifest, [])
    selected = [select(catalogue, task["selector"]) for task in manifest["tasks"]]
    issues = verify(root, release, selected)
    if issues:
        raise ValueError("\n".join(issues))
    load_env(root)
    ledger_path = manifest_path.parent / "execution.json"
    ledger = {"manifest_id": manifest["id"], "manifest_sha256": canonical_hash(manifest),
              "environment": {"python": platform.python_version(), "platform": platform.platform()}, "slots": []}
    with execution_lock(root / "work" / ".official-execution.lock"), model_environment(manifest["model_settings"], require_key=True):
        os.environ["LLM_EXPERIMENT_PROFILE"] = manifest["models"][0]["profile_id"]
        for task, selected_task in zip(manifest["tasks"], selected):
            for repetition in range(1, manifest["repeats"] + 1):
                slot = {"evaluation_id": task["id"], "repetition": repetition, "status": "missing", "attempts": []}
                ledger["slots"].append(slot)
                for attempt in range(1, 4):
                    name = "official-" + canonical_hash([canonical_hash(manifest), task["id"], repetition, attempt])[:28]
                    session = root / "work" / name
                    if not session.exists():
                        args = argparse.Namespace(command="run", official=True, manifest=str(manifest_path), repetition=repetition,
                                                  attempt=attempt, session_name=name, policy="llm", show=False)
                        print(f"Official {task['id']} repetition={repetition} attempt={attempt}", flush=True)
                        run_task(root, release, selected_task, args)
                    receipts = session / "receipt.json"
                    receipt = read_json(receipts) if receipts.is_file() else {"status": "interrupted", "retryable": True}
                    summaries = list((session / "bundle" / "runs").glob("*/*/*/summary.json"))
                    row = read_json(summaries[0]) if len(summaries) == 1 else None
                    item = {"attempt": attempt, "session": str(session), "status": receipt["status"]}
                    slot["attempts"].append(item)
                    if row is not None and _exclusion_reason(row) is None:
                        checked = report(manifest, [row])
                        if checked["excluded"]:
                            raise ValueError(f"Recorded formal result identity mismatch: {session}")
                        slot["status"] = "valid"
                        item["summary"] = str(summaries[0])
                        break
                    retry_auth = retry_auth_error and receipt.get("http_status") in {401, 403}
                    if not retry_auth and not receipt.get("retryable", receipt.get("status") in {"starting", "interrupted"}):
                        ledger["status"] = "stopped_on_nonretryable_error"
                        write_json(ledger_path, ledger)
                        raise ValueError(f"Model stopped on configuration/runtime error; inspect {session}")
                write_json(ledger_path, ledger)
        ledger["status"] = "complete" if all(s["status"] == "valid" for s in ledger["slots"]) else "complete_with_missing_slots"
        write_json(ledger_path, ledger)
    return int(ledger["status"] != "complete")


def combined_report(root: Path, plan_path: Path, models_dir: Path, output: Path) -> None:
    from harness.delivery import read_json, write_json
    from harness.protocol_report import report
    plan = read_sealed(plan_path)
    manifests = sorted(models_dir.glob("*/manifest.json"))
    if not manifests:
        raise ValueError("No model manifests found")
    results = []
    for path in manifests:
        manifest = read_sealed(path)
        if manifest.get("cohort_sha256") != canonical_hash(plan):
            raise ValueError("Cannot combine models from different frozen cohorts")
        rows, incomplete = [], []
        for session in (root / "work").glob("official-*"):
            receipt_path = session / "receipt.json"
            if not receipt_path.is_file():
                continue
            receipt = read_json(receipt_path)
            if receipt.get("manifest_id") != manifest["id"]:
                continue
            summaries = list((session / "bundle" / "runs").glob("*/*/*/summary.json"))
            if len(summaries) == 1:
                rows.append(read_json(summaries[0]))
            else:
                incomplete.append(str(session))
        result = report(manifest, rows)
        result.update(incomplete_sessions=incomplete)
        results.append(result)
    write_json(output, {"cohort_id": plan["id"], "cohort_sha256": canonical_hash(plan), "tasks": len(plan["tasks"]),
                        "repeats": plan["repeats"], "experiments": results})


def main(root: Path, argv=None) -> int:
    parser = argparse.ArgumentParser(description="正式实验题单冻结、模型登记、执行与汇总")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("freeze")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--id", required=True)
    p = sub.add_parser("prepare-models")
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--models", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p = sub.add_parser("run")
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--retry-auth-error", action="store_true", help="After correcting credentials, use a remaining attempt for recorded 401/403 errors")
    p = sub.add_parser("report")
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--models-dir", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "freeze":
        plan = freeze_cohort(root, args.out.resolve(), args.id)
        print(f"Frozen formal cohort: {plan['id']} / {len(plan['tasks'])} tasks / {plan['repeats']} repetitions")
    elif args.command == "prepare-models":
        for path in register_models(root, args.plan.resolve(), args.models.resolve(), args.out.resolve()):
            print(path)
    elif args.command == "run":
        return execute(root, args.manifest.resolve(), args.retry_auth_error)
    else:
        combined_report(root, args.plan.resolve(), args.models_dir.resolve(), args.out.resolve())
        print(args.out.resolve())
    return 0
