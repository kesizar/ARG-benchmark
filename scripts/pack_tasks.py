"""Zip task materials and write a hash manifest. Judges and configs stay out of the archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


def _serve_root(cfg: dict) -> str | None:
    command = ((cfg.get("local_serve") or {}).get("command")) or []
    if "--root" not in command:
        return None
    index = command.index("--root")
    if index + 1 >= len(command):
        return None
    return command[index + 1]


def _material_root(cfg: dict, repo: Path) -> Path:
    if cfg.get("category") == "text_adventure":
        story = ((cfg.get("if") or {}).get("story_file")) or ""
        path = repo / story
        if not path.is_file():
            raise SystemExit(f"{cfg.get('id')}: 找不到故事文件 {story}")
        return path
    relative = _serve_root(cfg)
    if not relative:
        raise SystemExit(f"{cfg.get('id')}: 配置里没有本地镜像根目录")
    path = repo / relative
    if not path.is_dir():
        raise SystemExit(f"{cfg.get('id')}: 找不到镜像目录 {relative}")
    return path


def _zip_path(source: Path, dest: Path, repo: Path) -> None:
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        if source.is_file():
            archive.write(source, source.relative_to(repo).as_posix())
            return
        for item in sorted(source.rglob("*")):
            if item.is_file():
                archive.write(item, item.relative_to(repo).as_posix())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="资源包目录，放在仓库外")
    parser.add_argument("--manifest", required=True, help="写入仓库的清单路径")
    parser.add_argument("--config", action="append", required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    tasks = []
    for relative in args.config:
        cfg = json.loads((repo / relative).read_text(encoding="utf-8"))
        source = _material_root(cfg, repo)
        archive_path = out / f"{cfg['id']}.zip"
        _zip_path(source, archive_path, repo)
        digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
        tasks.append({
            "id": cfg["id"],
            "config": relative.replace("\\", "/"),
            "archive": archive_path.name,
            "sha256": digest,
            "bytes": archive_path.stat().st_size,
            "material": source.relative_to(repo).as_posix(),
        })
        print(f"{cfg['id']} {archive_path.stat().st_size} {digest}")
    manifest = {
        "id": "pilot-11",
        "excluded": ["involuntary-appetite"],
        "note": "包内只有镜像或故事文件。裁判和配置留在仓库。非自愿摄入的镜像仍只在本机，不在这批包里。",
        "pack_dir": str(out),
        "tasks": tasks,
    }
    manifest_path = Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"manifest {manifest_path}")


if __name__ == "__main__":
    main()
