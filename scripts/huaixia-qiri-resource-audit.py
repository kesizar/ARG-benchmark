import json,re,hashlib
from pathlib import Path
p=Path('tasks/huaixia-qiri/original.html');s=p.read_text(encoding='utf-8');out=[]
for path in Path('runs/huaixia-qiri').glob('route-*.json'):
 d=json.loads(path.read_text(encoding='utf-8'))
 if 'states' in d: out.append({'trace':path.name,'blocked':d.get('blocked',[]),'errors':d.get('errors',[]),'states':len(d['states'])})
urls=sorted(set(re.findall(r'https?://[^"\x27 <>]+',s)))
audit={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'absolute_url_mentions':urls,'data_images':s.count('data:image'),'traces':out,'scope':'Static URL scan and observed requests on UI paths; not proof that every unvisited branch lacks dynamic dependencies.'}
Path('runs/huaixia-qiri/resource-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'traces':len(out),'blocked':sorted({u for x in out for u in x['blocked']}),'errors':sum(len(x['errors']) for x in out),'url_mentions':len(urls)},ensure_ascii=True))
