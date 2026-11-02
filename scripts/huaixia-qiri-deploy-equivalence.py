import hashlib,json,zipfile
from pathlib import Path
root=Path('runs/huaixia-qiri/deploy-check/evaluation')
with zipfile.ZipFile('packs/huaixia-qiri.prepared.zip') as z:
 names=[n for n in z.namelist() if n.startswith('harness/') or n.startswith('judge/huaixia-qiri/') and n.endswith('.json') or n=='tasks/huaixia-qiri/mirror/index.html' or n in ['scripts/run_one.py','scripts/serve_static.py']]
 checks=[{'path':n,'equal':(root/n).exists() and hashlib.sha256(z.read(n)).digest()==hashlib.sha256((root/n).read_bytes()).digest()} for n in names]
 configs=[]
 for n in ['configs/huaixia-qiri.json','configs/huaixia-qiri-hidden.json']:
  original=json.loads(z.read(n));unpacked=json.loads((root/n).read_text(encoding='utf-8'))
  unpacked['entry_url']=unpacked['entry_url'].replace('8813','8811');unpacked['allow_hosts']=['127.0.0.1:8811']
  unpacked['local_serve']['port']=8811;unpacked['local_serve']['ready_url']=unpacked['local_serve']['ready_url'].replace('8813','8811');unpacked['local_serve']['command'][-1]='8811'
  configs.append({'path':n,'equal_after_port_restore':original==unpacked})
 data={'files':checks,'configs':configs,'all_equal':all(x['equal'] for x in checks) and all(x['equal_after_port_restore'] for x in configs),'scope':'Runtime, game, and judges match independently tested unpack; configs match after restoring test port. Review prose and manifests excluded.'}
Path('runs/huaixia-qiri/deploy-equivalence.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print('files',len(checks),'all_equal',data['all_equal'])
assert data['all_equal']
