from pathlib import Path
import zipfile,json,shutil,hashlib,sys,platform
root=Path.cwd();packs=root/'packs';res=packs/'xinshiji.resources.partial.zip';ev=packs/'xinshiji.evaluation.partial.zip'
with zipfile.ZipFile(res,'w',zipfile.ZIP_DEFLATED)as z:
 for f in (root/'tasks/xinshiji/mirror').rglob('*'):
  if f.is_file():z.write(f,f.relative_to(root/'tasks/xinshiji/mirror'))
with zipfile.ZipFile(packs/'xinshiji.prepared.zip')as src,zipfile.ZipFile(ev,'w',zipfile.ZIP_DEFLATED)as z:
 for name in src.namelist():
  if name=='BUNDLE-MANIFEST.json':
   data=json.loads(src.read(name));data['readiness']='PARTIAL RECOVERY; NOT PREPARED. Missing background and optional branch UI checks.';z.writestr(name,json.dumps(data,indent=2))
  else:z.writestr(name,src.read(name))
 for name in ['scripts/xinshiji_ui.py','judge/xinshiji/recovery/remote-browser.json','judge/xinshiji/recovery/network-probe.json','judge/xinshiji/recovery/browser-crawl.json']:
  z.write(root/name,name)
 z.writestr('RECOVERY-ONLY.txt','NOT PREPARED. See tasks/xinshiji/README.md. Resource missing background; optional branch UI pending.\nLocal validation: python scripts/xinshiji_ui.py tasks/xinshiji/mirror 8823\n')
for f in [packs/'xinshiji.prepared.zip',packs/'xinshiji.prepared.manifest.json']:f.unlink()
base=root/'runs/xinshiji-independent';base.mkdir(parents=True,exist_ok=True)
for name,archive in [('resources',res),('evaluation',ev)]:
 dest=base/name
 if dest.exists():raise RuntimeError('Refuse overwrite '+str(dest))
 dest.mkdir();zipfile.ZipFile(archive).extractall(dest)
report={'archives':[{'path':str(f.relative_to(root)),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}for f in [res,ev]],'python':sys.version,'platform':platform.platform(),'cross_os_tested':False,'resource_webroot':str(base/'resources'),'evaluation_webroot':str(base/'evaluation/tasks/xinshiji/mirror'),'status':'await UI independent deployment'}
(root/'judge/xinshiji/recovery/packages.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))
