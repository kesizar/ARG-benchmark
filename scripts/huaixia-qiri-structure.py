from pathlib import Path
import json, re
s = Path('tasks/huaixia-qiri/original.html').read_text(encoding='utf-8')
endings = [dict(id=a,name=b,rank=c) for a,b,c in re.findall(r'ending:\{id:"([^"]+)",name:"([^"]+)",rank:"([^"]+)', s)]
nodes = re.findall(r'\{id:"((?:c[1-8]_|end_|death_|ev_)[^"]+)"', s)
Path('runs/huaixia-qiri/structure.json').write_text(json.dumps({'endings':endings,'node_count':len(nodes),'nodes':nodes},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'endings':endings,'node_count':len(nodes)},ensure_ascii=False))
