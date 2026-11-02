from pathlib import Path
import json,hashlib,zipfile,subprocess,sys,time,urllib.request,os
R=Path(__file__).resolve().parents[1];T=R/'tasks/kongguan';A=R/'judge/kongguan/acceptance';D=R/'runs/kongguan/delivery';D.mkdir(parents=True,exist_ok=True)
def main():
 resource=R/'packs/kongguan.resources.zip'
 with zipfile.ZipFile(resource,'w',zipfile.ZIP_DEFLATED) as z:
  for f in (T/'mirror').rglob('*'):
   if f.is_file():z.write(f,f.relative_to(T/'mirror').as_posix())
 subprocess.run([sys.executable,str(R/'scripts/build_prepared_bundle.py'),'--task','kongguan'],check=True)
 result=[]
 for kind,port in [('resources',8822),('prepared',8823)]:
  archive=R/f'packs/kongguan.{kind}.zip';dest=D/(kind+'-'+str(int(time.time())));dest.mkdir()
  with zipfile.ZipFile(archive) as z:
   for n in z.namelist():assert (dest/n).resolve().is_relative_to(dest.resolve())
   z.extractall(dest)
  web=dest if kind=='resources' else dest/'tasks/kongguan/mirror';server=subprocess.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1','--directory',str(web)],cwd=dest,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=0x08000000)
  try:
   for _ in range(100):
    try:
     with urllib.request.urlopen(f'http://127.0.0.1:{port}/index.html',timeout=1) as q:assert q.status==200
     break
    except Exception:time.sleep(.1)
   evaluator=R if kind=='resources' else dest;out=A/f'independent-{kind}.json';q=subprocess.run([sys.executable,str(evaluator/'judge/kongguan/verify_sample.py'),'--port',str(port),'--output',str(out)],cwd=dest,capture_output=True,text=True,encoding='utf8',errors='replace',env=dict(os.environ,PYTHONIOENCODING='utf-8'));(A/f'independent-{kind}.log').write_text(q.stdout+q.stderr,encoding='utf8');assert q.returncode==0,q.stderr[-2000:]
   manifest=json.loads((T/'provenance.json').read_text(encoding='utf8'))['files'];assert all(hashlib.sha256((web/x['path']).read_bytes()).hexdigest()==x['sha256'] for x in manifest)
   if kind=='prepared':
    m=json.loads((dest/'BUNDLE-MANIFEST.json').read_text(encoding='utf8'));assert all(hashlib.sha256((dest/x['path']).read_bytes()).hexdigest()==x['sha256'] for x in m['files'])
   result.append({'kind':kind,'port':port,'extraction':str(dest),'archive':archive.relative_to(R).as_posix(),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'asset_hashes_match':True,'files':len(manifest),'independent_cwd':True,'evaluator_root':str(evaluator),'probe':out.relative_to(R).as_posix(),'prerequisites':'Windows Python3.11 / installed Microsoft Edge; dependencies recorded in prepared manifest; not cross-OS'})
  finally:server.terminate();server.wait(timeout=10)
 (A/'independent-delivery.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print('independent packages verified',len(result))
if __name__=='__main__':main()
