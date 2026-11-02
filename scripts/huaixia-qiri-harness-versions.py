import hashlib,json
from pathlib import Path
files={}
for name in ['browser_harness.py','loop.py']:
 for label,path in [('tested',Path('judge/huaixia-qiri/tested-harness')/name),('shared',Path('harness')/name)]:
  files[label+'/'+name]=hashlib.sha256(path.read_bytes()).hexdigest()
Path('runs/huaixia-qiri/harness-versions.json').write_text(json.dumps({'sha256':files,'diffs':['runs/huaixia-qiri/browser-harness-shared.diff','runs/huaixia-qiri/loop-shared.diff'],'scope':'Only pinned modules differ from current shared at capture time; package equivalence covers all runtime modules.'},indent=2),encoding='utf-8')
print(json.dumps(files))
