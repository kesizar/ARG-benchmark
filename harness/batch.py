"""Run task configs one after another."""

from __future__ import annotations

from pathlib import Path

from harness.loop import _model_link_down, run


async def run_configs(configs: list[str], *, policy: str, obs_mode: str | None, headless: bool, repo_root: Path, run_kind: str = "test", repeats: int = 1, manifest: dict | None = None) -> int:
    if type(repeats) is not int or repeats < 1:
        raise ValueError("重复次数必须为正整数")
    failed = 0
    for config in configs:
        path = Path(config)
        if not path.is_absolute():
            path = repo_root / path
        print(f"== {path}", flush=True)
        for repetition in range(repeats):
            for attempt in range(3 if run_kind == "official" else 1):
                try:
                    summary = await run(path, policy=policy, obs_mode=obs_mode, headless=headless, repo_root=repo_root, run_kind=run_kind,
                                        manifest=manifest, repetition=repetition + 1, attempt=attempt + 1)
                except Exception as exc:  # noqa: BLE001
                    if run_kind == "official" and _model_link_down(exc) and attempt < 2:
                        print(f"基础设施异常，整局重跑 {config} 第 {repetition + 1} 局: {exc}", flush=True)
                        continue
                    print(f"失败 {config} 第 {repetition + 1} 局: {exc}", flush=True)
                    failed += 1
                    break
                if summary.get("ended_reason") == "error":
                    failed += 1
                break
    return failed
