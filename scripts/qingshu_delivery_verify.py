from pathlib import Path
import json,zipfile,hashlib,subprocess,sys,time,urllib.request,urllib.error
R=Path(__file__).resolve().parents[1];T='qingshu-shizong';U=R/'runs'/f'{T}-unpacked';RES=R/'runs'/f'{T}-resources-unpacked';d={}
for name,dest in [('prepared',U),('resources',RES)]:
 with zipfile.ZipFile(R/f'packs/{T}.{name}.zip') as z:
  assert z.testzip() is None;z.extractall(dest)
 if name=='prepared':
  m=json.loads((U/'BUNDLE-MANIFEST.json').read_text(encoding='utf-8'));assert all(hashlib.sha256((U/x['path']).read_bytes()).hexdigest()==x['sha256'] for x in m['files']);d['prepared_files_verified']=len(m['files'])
pub=Path('tasks')/T/'mirror';files=[p for p in (RES/pub).iterdir() if p.is_file()];assert len(files)==6
assert all(p.read_bytes()==(U/pub/p.name).read_bytes() for p in files);d['resources_byte_equal_files']=6
with (R/f'judge/{T}/verification/delivery-server.log').open('w') as log:
 proc=subprocess.Popen([sys.executable,str(U/'scripts/qingshu_serve.py'),'--root',str(RES/pub),'--port','8831'],stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 try:
  for _ in range(60):
   try:
    with urllib.request.urlopen('http://127.0.0.1:8831/forum.html',timeout=2) as f:body=f.read();ctype=f.headers['Content-Type']
    break
   except urllib.error.URLError:time.sleep(.1)
  assert body==(RES/pub/'forum.html').read_bytes() and 'charset=utf-8' in ctype
  d['forum_content_type']=ctype;d['served_resource_hash']=hashlib.sha256(body).hexdigest()
  for path in ['/judge/qingshu-shizong/judge.json','/configs/qingshu-shizong.json','/../judge/qingshu-shizong/judge.json','/BUNDLE-MANIFEST.json']:
   try:urllib.request.urlopen('http://127.0.0.1:8831'+path,timeout=2);raise AssertionError(path)
   except urllib.error.HTTPError as e:assert e.code==404
  d['private_paths_404']=True;d['pass']=True
 finally:proc.terminate();proc.wait(timeout=10)
(R/f'judge/{T}/verification/delivery-integrity.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');print(d)
