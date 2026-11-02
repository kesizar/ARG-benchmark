from pathlib import Path
import json,subprocess,sys,time,urllib.request
R=Path(__file__).resolve().parents[1];O=R/'runs/guangying-she';PY=sys.executable;rows=[]
plans=[('resources',8813),('prepared',8811)]
if '--prepared-retry' in sys.argv:
 rows=[r for r in json.loads((O/'deployment.json').read_text(encoding='utf8')) if not r.get('error')];plans=[('prepared',8813)]
for kind,port in plans:
 root=O/f'unpacked-{kind}';mirror=root/'tasks/guangying-she/mirror';url=f'http://127.0.0.1:{port}/index.html'
 proc=subprocess.Popen([PY,'-m','http.server',str(port),'--bind','0.0.0.0','--directory',str(mirror)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 row={'kind':kind,'root':str(root),'port':port,'url':url,'server_only_root':str(mirror)}
 try:
  for i in range(8):
   try:
    with urllib.request.urlopen(url,timeout=2) as x:row['http_status']=x.status
    break
   except Exception as e:time.sleep(.3)
  else:raise RuntimeError('Local port unavailable')
  evaluator=root if kind=='prepared' else R
  run=subprocess.run([PY,str(evaluator/'judge/guangying-she/verify_sample.py'),url,str(O/f'deploy-{kind}.json')],cwd=str(root),capture_output=True,timeout=120)
  (O/f'deploy-{kind}.log').write_bytes(run.stdout+run.stderr);row['ui_exit']=run.returncode;assert run.returncode==0
  if kind=='prepared':
   v=subprocess.run([PY,'scripts/validate_config.py','configs/guangying-she.json'],cwd=str(root),capture_output=True);row['extracted_config_validation_exit']=v.returncode;row['validation_output']=v.stdout.decode(errors='replace');assert v.returncode==0
  try:
   with urllib.request.urlopen(f'http://127.0.0.1:{port}/judge/guangying-she/judge.json',timeout=2) as x:raise AssertionError('Judge exposed')
  except urllib.error.HTTPError as e:assert e.code==404;row['evaluator_not_served']=True
 except Exception as e:row['error']=str(e);raise
 finally:
  proc.terminate();proc.wait(timeout=5);rows.append(row);(O/'deployment.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
print('Both independent unpacked packages passed UI and isolation checks.')
