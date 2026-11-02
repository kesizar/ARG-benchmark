import pathlib,zipfile,json,hashlib
root=pathlib.Path('tasks/huisheng-weizhi/mirror'); dst=pathlib.Path('packs/huisheng-weizhi.resources.zip')
with zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(root.rglob('*')):
  if f.is_file():z.write(f,f.relative_to(root).as_posix())
print(dst, dst.stat().st_size)
