"""Preserve the original page and fetch each original image resource."""
from pathlib import Path
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "ARG-packs/verify-416/bodies/601.html"
ORIGIN = "https://mike798-cloud.github.io/wuluocun-1/"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    public = ROOT / "tasks/wuluo-cun/mirror"
    public.mkdir(parents=True, exist_ok=True)
    raw = SOURCE.read_bytes()
    html = raw.decode("utf-8")
    original = ROOT / "judge/wuluo-cun/source/entry.original.html"
    original.parent.mkdir(parents=True, exist_ok=True)
    original.write_bytes(raw)
    # Quote an HTML event attribute correctly; preserve the original action.
    assert html.count("a.onclick") == 1
    html = html.replace("a.onclick", "a.onclick.replace(/\\x22/g, '&quot;')")
    names = sorted(set(re.findall(r"[\w-]+\.(?:jpg|png|webp)", html)))
    assets = []
    for name in names:
        dest = public / name
        if not dest.is_file():
            done = subprocess.run(["curl.exe", "--fail", "--location", "--silent", "--show-error", "--connect-timeout", "10", "--max-time", "30", "--output", str(dest), ORIGIN + name], capture_output=True, text=True)
            if done.returncode:
                raise RuntimeError(f"Asset download failed: {name}: {done.stderr[:200]}")
        data = dest.read_bytes()
        assert data.startswith((b"\xff\xd8\xff", b"\x89PNG", b"RIFF")), f"Not an image: {name}"
        assets.append({"source_url": ORIGIN + name, "local_file": name, "bytes": len(data), "sha256": sha(data)})
    (public / "index.html").write_text(html, encoding="utf-8", newline="\n")
    provenance = {"record_id": "base664:0601", "title": "雾落村·槐香引", "source_url": ORIGIN, "source_snapshot": str(SOURCE), "source_sha256": sha(raw), "prepared_html_sha256": sha((public / "index.html").read_bytes()), "changes": [{"source_line": 495, "change": "Escape double quotes in generated HTML onclick attributes", "reason": "Original nested quotes break the take-thimble button", "game_rule_change": False}], "assets": assets, "rights": "Local evaluation copy of a public game; redistribution permission has not been established"}
    (ROOT / "tasks/wuluo-cun/provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"images": len(assets), "bytes": sum(x["bytes"] for x in assets), "compatibility_fixes": 1}))


if __name__ == "__main__":
    main()
