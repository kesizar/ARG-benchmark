import pathlib,zipfile,json,hashlib
r=pathlib.Path('.');d=r/'tasks/guiyihui-meimei/mirror'; files=sorted(x for x in d.rglob('*') if x.is_file()); out=r/'packs/guiyihui-meimei.resources.zip'
manifest={'task_id':'guiyihui-meimei','files':[{'path':x.relative_to(d).as_posix(),'sha256':hashlib.sha256(x.read_bytes()).hexdigest(),'bytes':x.stat().st_size} for x in files]}
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 for x in files:z.write(x,x.relative_to(d).as_posix())
 z.writestr('RESOURCE-MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
print(out,len(files))
