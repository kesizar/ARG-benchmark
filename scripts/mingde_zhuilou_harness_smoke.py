from pathlib import Path
import zipfile,json,subprocess,sys
R=Path(__file__).resolve().parents[1];t=R/'runs/mingde-zhuilou/independent-harness';t.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(R/'packs/mingde-zhuilou.prepared.zip') as z:z.extractall(t)
cfg=t/'configs/mingde-zhuilou.json';s=cfg.read_text(encoding='utf-8');cfg.write_text(s.replace('8831','8833'),encoding='utf-8')
r=subprocess.run([sys.executable,'scripts/run_one.py','--config','configs/mingde-zhuilou.json','--policy','script'],cwd=t,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=100)
(R/'runs/mingde-zhuilou/independent-harness.log').write_text(r.stdout+'\n'+r.stderr,encoding='utf-8')
rows=list(t.glob('runs/**/summary.json'));assert r.returncode==0,(r.returncode,r.stderr[-1000:]);assert rows
summary=json.loads(max(rows,key=lambda p:p.stat().st_mtime).read_text(encoding='utf-8'));assert summary.get('ended_reason')!='error'
(R/'runs/mingde-zhuilou/independent-harness.json').write_text(json.dumps({'passed':True,'source':'Unpacked prepared scripts/run_one.py + its own harness; only port changed 8831->8833 in extracted config.','cwd':str(t),'exit_code':r.returncode,'summary':summary},ensure_ascii=False,indent=2),encoding='utf-8');print('PASS independent packaged harness',summary.get('ended_reason'))
