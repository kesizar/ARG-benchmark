import hashlib,json,zipfile
from pathlib import Path
archives=[Path('packs/huaixia-qiri.game.zip'),Path('packs/huaixia-qiri.prepared.zip')]
reports=[]
for p in archives:
 with zipfile.ZipFile(p) as z:
  manifest=json.loads(z.read('MANIFEST.json' if p.name.endswith('game.zip') else 'BUNDLE-MANIFEST.json'))
  checks=[{'path':f['path'],'ok':hashlib.sha256(z.read(f['path'])).hexdigest()==f['sha256'] and len(z.read(f['path']))==f['bytes']} for f in manifest['files']]
  reports.append({'archive':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'count':len(checks),'all_manifest_entries_match':all(x['ok'] for x in checks),'failures':[x for x in checks if not x['ok']]})
game=hashlib.sha256(Path('tasks/huaixia-qiri/original.html').read_bytes()).hexdigest()
with zipfile.ZipFile(archives[0]) as a,zipfile.ZipFile(archives[1]) as b:
 match=hashlib.sha256(a.read('index.html')).hexdigest()==game==hashlib.sha256(b.read('tasks/huaixia-qiri/mirror/index.html')).hexdigest()
out={'archives':reports,'both_game_bytes_match_original':match,'scope':'Archive hashes and manifests; not a substitute for gameplay acceptance.'}
Path('runs/huaixia-qiri/bundle-verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
assert match and all(x['all_manifest_entries_match'] for x in reports)
print(json.dumps(out,ensure_ascii=True))
