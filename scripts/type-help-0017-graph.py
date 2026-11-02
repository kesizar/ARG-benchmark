import json, re, collections
from pathlib import Path
p=Path('data/preparation/type-help-0017')
data=json.loads((p/'source-index.json').read_text(encoding='utf8'))
scenes={x['name']:x for x in data['passages'] if re.match(r'^\d\d-',x['name']) and not re.search(r'-(Ja|Br|Ge|It|Ar|Ko|Fr)$',x['name'])}
edges=[]; missing=[]
for name, scene in scenes.items():
    for tag in scene['tags'].split():
        (edges if tag in scenes else missing).append([name,tag])
adj=collections.defaultdict(list)
for a,b in edges: adj[a].append(b)
seen={'00-readme'}; q=collections.deque(['00-readme'])
while q:
    for v in adj[q.popleft()]:
        if v not in seen: seen.add(v); q.append(v)
graph={'scenes':len(scenes),'edges':edges,'missing_tags':missing,'reachable_from_readme':sorted(seen),'unreachable_from_readme':sorted(set(scenes)-seen), 'scene_data':[{k:x[k] for k in ('name','tags','body')} for x in scenes.values()]}
(p/'scene-graph.json').write_text(json.dumps(graph,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v if not isinstance(v,list) else len(v) for k,v in graph.items() if k!='scene_data'}))
print('unreachable',graph['unreachable_from_readme'])
