"""Start the local server declared by a task config until interrupted."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from harness.config import load_config  # noqa: E402
from harness.serve_local import LocalServer, check_server  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="按任务配置启动本地服务")
    parser.add_argument("--config", default="")
    parser.add_argument("--task", default="involuntary-appetite")
    parser.add_argument("--check", action="store_true", help="启动、确认就绪、再停止")
    args = parser.parse_args()
    path = Path(args.config) if args.config else ROOT / "configs" / f"{args.task}.json"
    cfg = load_config(path)
    if args.check:
        check_server(cfg, ROOT)
        print("ok")
        return
    server = LocalServer()
    server.start(cfg, ROOT)
    ready = (cfg.get("local_serve") or {}).get("ready_url") or cfg.get("entry_url")
    print(ready or "本地服务已处理", flush=True)
    try:
        while True:
            if server.owned and server.proc and server.proc.poll() is not None:
                raise SystemExit(f"本地服务已退出，代码 {server.proc.returncode}")
            time.sleep(1)
    except KeyboardInterrupt:
        print("正在停止", flush=True)
    finally:
        server.stop()


if __name__ == "__main__":
    main()
