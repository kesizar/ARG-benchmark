from pathlib import Path
import json,hashlib,zipfile
D=Path('runs/bailu-guangguang');rows=[]
for suffix,port in [('game',8812),('prepared',8813)]:
 p=Path(f'packs/bailu-guangguang.{suffix}.zip');dest=D/('unpacked-'+suffix)
 with zipfile.ZipFile(p) as z:
  checks=[{'path':n,'equal':z.read(n)==(dest/n).read_bytes()} for n in z.namelist() if not n.endswith('/')];assert all(x['equal'] for x in checks)
 ui=json.loads((D/f'ui-{port}.json').read_text(encoding='utf8'));last=next(x for x in ui if x.get('label')=='final');reset=next(x for x in ui if x.get('label')=='reset');assert last['result']['checkpoints_reached']==6 and last['result']['ending_reached'];assert not any(reset['hooks'].values())
 rows.append({'package':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'port':port,'new_context':True,'unpacked_files_equal':checks,'ui':f'runs/bailu-guangguang/ui-{port}.json','formal_puzzle_points':6,'ending_tier':'normal','external_requests':ui[-1]['external_requests'],'page_errors':ui[-1]['page_errors'],'reset_clears':True})
shared=[]
with zipfile.ZipFile('packs/bailu-guangguang.prepared.zip') as z:
 for n in z.namelist():
  if n.startswith(('harness/','judge/','configs/')):shared.append({'path':n,'source_equals_pack':Path(n).read_bytes()==z.read(n)})
assert all(x['source_equals_pack'] for x in shared)
(D/'deployment-audit.json').write_text(json.dumps({'deployments':rows,'evaluator_source_equals_package':shared,'note':'UI reviewer driver stays external. Resource-only package deliberately excludes evaluator; its judgment is supplied separately. Prepared package own cwd run_one give_up integration smoke did not call model APIs. Windows only.'},ensure_ascii=False,indent=2),encoding='utf8')
summary=list((D/'unpacked-prepared/runs/bailu-guangguang').glob('B/*/summary.json'));print('smoke',len(summary));print('validated two packages and six-point judge')
