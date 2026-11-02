"""Display the nonsecret profile fingerprint used by the formal protocol."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from harness.config import load_config  # noqa: E402
from harness.env import load_env  # noqa: E402
from harness.policy_llm import LLMPolicy  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--obs-mode", choices=["A", "B", "C"], default=None)
    args = parser.parse_args()
    load_env(ROOT)
    cfg = load_config(ROOT / args.config, args.obs_mode)
    cfg["_run_kind"] = "official"
    policy = LLMPolicy(cfg, ROOT)
    print(json.dumps({"profile": policy.profile(), "profile_sha256": policy.profile_sha256()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
