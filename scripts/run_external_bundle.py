"""Run an independently extracted evaluator bundle with this workspace's harness.

The bundle's game, configuration and judge stay in the extraction directory;
the harness and this launcher are read from the workspace containing this file.
The launcher does not alter or repackage the source bundle.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE_ROOT))

from harness.loop import run  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    parser = argparse.ArgumentParser(description='使用工作区 harness 运行独立解包的评测包')
    parser.add_argument('--bundle-root', required=True, help='独立解包目录')
    parser.add_argument('--config', required=True, help='解包目录中的任务配置相对路径')
    parser.add_argument('--policy', choices=['script', 'llm'], default='script')
    parser.add_argument('--obs-mode', choices=['A', 'B', 'C'])
    parser.add_argument('--show', action='store_true')
    parser.add_argument('--run-kind', choices=['test', 'official'], default='test')
    parser.add_argument('--manifest', help='冻结清单路径；official 必须提供')
    parser.add_argument('--repetition', type=int, help='official 重复局编号')
    parser.add_argument('--attempt', type=int, default=1)
    args = parser.parse_args(argv)

    bundle_root = Path(args.bundle_root).resolve()
    if not bundle_root.is_dir():
        parser.error('bundle-root 必须是已有的解包目录')
    config = (bundle_root / args.config).resolve()
    if not config.is_relative_to(bundle_root) or not config.is_file():
        parser.error('config 必须是解包目录内的已有文件')
    if args.run_kind == 'official' and (not args.manifest or args.repetition is None):
        parser.error('正式运行须提供 --manifest 和 --repetition')
    manifest = json.loads(Path(args.manifest).resolve().read_text(encoding='utf-8-sig')) if args.manifest else None
    try:
        summary = asyncio.run(run(config, policy=args.policy, obs_mode=args.obs_mode,
                                  headless=not args.show, repo_root=bundle_root,
                                  run_kind=args.run_kind, manifest=manifest,
                                  repetition=args.repetition, attempt=args.attempt))
    except SystemExit as exc:
        if exc.code not in (0, None):
            print(exc)
            return 1
        return 0
    return 1 if summary.get('ended_reason') == 'error' else 0


if __name__ == '__main__':
    raise SystemExit(main())
