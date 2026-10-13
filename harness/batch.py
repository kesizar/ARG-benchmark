"""Run task configs one after another."""

from __future__ import annotations

from pathlib import Path

from harness.loop import run


async def run_configs(configs: list[str], *, policy: str, obs_mode: str | None, headless: bool, repo_root: Path) -> int:
    failed = 0
    for config in configs:
        path = Path(config)
        if not path.is_absolute():
            path = repo_root / path
        print(f"== {path}", flush=True)
        try:
            summary = await run(path, policy=policy, obs_mode=obs_mode, headless=headless, repo_root=repo_root)
        except Exception as exc:  # noqa: BLE001
            print(f"失败 {config}: {exc}")
            failed += 1
            continue
        if summary.get("ended_reason") == "error":
            failed += 1
    return failed
