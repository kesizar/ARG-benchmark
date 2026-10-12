from pathlib import Path
import re

root = Path(r"d:\HuaweiMoveData\Users\17669\Desktop\ARG-benchmark\mirror\involuntary-appetite")
missing = []
for path in root.rglob("*"):
    if path.suffix.lower() not in {".html", ".css", ".js"}:
        continue
    text = path.read_text(encoding="utf-8", errors="replace")
    for match in re.finditer(r"/step2/[^\s\"')<>]+", text):
        rel = match.group(0).split("?", 1)[0].split("#", 1)[0]
        if "${" in rel:
            continue
        target = root / rel.lstrip("/")
        if not target.exists():
            missing.append(f"{path.relative_to(root)} -> {rel}")
print("missing", len(missing))
for item in missing[:40]:
    print(item)
files = [p for p in root.rglob("*") if p.is_file()]
print("files", len(files), "bytes", sum(p.stat().st_size for p in files))
