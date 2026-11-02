"""Resumeable independent startup checks for repaired packages; never calls an LLM."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.delivery import extract, read_json, write_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repairs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--key", action="append")
    args = parser.parse_args()
    args.repairs = args.repairs.resolve()
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    results = []
    for review_path in sorted(args.repairs.glob("*.zip.review.json")):
        review = read_json(review_path)
        key = review["original_record_id"]
        if args.key and key not in args.key:
            continue
        folder = args.out / key.replace(":", "-").replace("/", "-")
        previous = folder / "result.json"
        if previous.is_file():
            old = read_json(previous)
            if old.get("status") == "pass" and old.get("package_sha256") == review["sha256"]:
                results.append(old)
                continue
        attempt = folder / str(time.time_ns())
        bundle = attempt / "bundle"
        extract(ROOT / review["package"], bundle)
        inspection = review["inspection"][0]
        cfg = read_json(bundle / inspection["config"])
        cfg["policy_script"] = [{"op": "give_up"}]
        cfg["actions_enabled"] = list(dict.fromkeys([*cfg.get("actions_enabled", []), "give_up"]))
        write_json(bundle / "handoff-smoke.json", cfg)
        result = {"key": key, "package_sha256": review["sha256"], "scope": "scripted startup, no model, no full-game acceptance",
                  "status": "error", "attempt": str(attempt), "runtime_layer": cfg.get("runtime_layer")}
        print(f"START {key}", flush=True)
        try:
            server = cfg.get("local_serve") or {}
            url = urlparse(server.get("ready_url") or "")
            if server.get("enabled") and url.hostname and url.port:
                try:
                    sock = socket.create_connection((url.hostname, url.port), timeout=0.5)
                except OSError:
                    pass
                else:
                    sock.close()
                    raise ValueError(f"Port already used: {url.port}")
            env = os.environ.copy()
            env["BENCHMARK_BROWSER_CHANNEL"] = "chromium"
            env["PYTHONIOENCODING"] = "utf-8"
            for key_name in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "AGENT_API_KEY"):
                env.pop(key_name, None)
            completed = subprocess.run([sys.executable, str(ROOT / "scripts/run_external_bundle.py"),
                                        "--bundle-root", str(bundle), "--config", "handoff-smoke.json",
                                        "--policy", "script", "--run-kind", "test"],
                                       cwd=attempt, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=150)
            (attempt / "startup.log").write_bytes(completed.stdout)
            result["exit_code"] = completed.returncode
            summaries = list((bundle / "runs").glob("*/*/*/summary.json"))
            if summaries:
                summary = read_json(summaries[-1])
                result.update(summary=str(summaries[-1]), ended_reason=summary.get("ended_reason"),
                              judge_error=summary.get("judge_error"), target_success=summary.get("target_success"),
                              screenshots=len(list(summaries[-1].parent.glob("*.png"))))
                images_ok = cfg.get("obs_mode") == "A" or result["screenshots"] > 0
                if completed.returncode == 0 and summary.get("ended_reason") != "error" and not summary.get("judge_error") and images_ok:
                    result["status"] = "pass"
            if result["status"] != "pass":
                result["error_tail"] = completed.stdout.decode("utf-8", errors="replace")[-2200:]
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            result["error"] = str(exc)
        write_json(previous, result)
        results.append(result)
        write_json(args.out / "summary.json", results)
        print(f"{result['status'].upper()} {key} {result.get('ended_reason', result.get('error', ''))}", flush=True)
    write_json(args.out / "summary.json", results)
    print(f"PASS {sum(r['status'] == 'pass' for r in results)}/{len(results)}", flush=True)
    return int(any(r["status"] != "pass" for r in results))


if __name__ == "__main__":
    raise SystemExit(main())
