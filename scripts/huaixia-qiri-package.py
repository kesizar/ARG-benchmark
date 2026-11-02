import hashlib,json,zipfile
from pathlib import Path
root=Path('tasks/huaixia-qiri/mirror'); content=root/'index.html'
data=content.read_bytes(); digest=hashlib.sha256(data).hexdigest()
manifest={'task_id':'huaixia-qiri','source':'https://01a06cd1-d760-7e8d-9f38-5c84d285a9bf.arena.site/','files':[{'path':'index.html','sha256':digest,'bytes':len(data)}],'scope':'Game only. Scoring and full resource completeness still require acceptance.'}
out=Path('packs/huaixia-qiri.game.zip');out.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('index.html',data)
 z.writestr('MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
print(out, hashlib.sha256(out.read_bytes()).hexdigest())
