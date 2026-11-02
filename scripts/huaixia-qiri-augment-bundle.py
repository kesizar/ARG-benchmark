"""Add the separate multi-playthrough task to the generic draft evaluation bundle."""
import hashlib,json,zipfile
from pathlib import Path
zpath=Path('packs/huaixia-qiri.prepared.zip')
extra=['configs/huaixia-qiri-hidden.json','judge/huaixia-qiri/judge-hidden.json','judge/huaixia-qiri/review.md']
with zipfile.ZipFile(zpath) as z:
 data={n:z.read(n) for n in z.namelist() if n not in extra and n not in ['BUNDLE-MANIFEST.json','START-HERE.txt']}
 manifest=json.loads(z.read('BUNDLE-MANIFEST.json'))
 start=z.read('START-HERE.txt').decode('utf-8')
# Pin the two runtime modules actually exercised by independent deployment tests.
for name in ['browser_harness.py','loop.py']:
 data['harness/'+name]=Path('judge/huaixia-qiri/tested-harness',name).read_bytes()
for entry in manifest['files']:
 if entry['path'] in ['harness/browser_harness.py','harness/loop.py']:
  b=data[entry['path']];entry.update(sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
manifest['runtime_pin']='browser_harness.py and loop.py pinned to independently tested snapshots; current shared harness may differ.'
for x in extra:
 b=Path(x).read_bytes();data[x]=b
manifest['files']=[x for x in manifest['files'] if x['path'] not in extra]
manifest['files'] += [{'path':x,'sha256':hashlib.sha256(data[x]).hexdigest(),'bytes':len(data[x])} for x in extra]
manifest['hidden_config']='configs/huaixia-qiri-hidden.json'
manifest['readiness']='Draft only: full acceptance pending. Hidden task needs its own config so the first normal ending does not terminate the episode.'
data['BUNDLE-MANIFEST.json']=json.dumps(manifest,ensure_ascii=False,indent=2).encode()
data['START-HERE.txt']=(start+'Hidden route: python scripts/run_one.py --config configs/huaixia-qiri-hidden.json --policy script\n').encode()
with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in data.items():z.writestr(n,b)
manifest['archive']=zpath.as_posix();manifest['archive_sha256']=hashlib.sha256(zpath.read_bytes()).hexdigest()
Path('packs/huaixia-qiri.prepared.manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(manifest['archive_sha256'])
