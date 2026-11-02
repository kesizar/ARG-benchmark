"""Build declared local adaptation from source graph, refusing unsupported semantics."""
import json,pathlib
R=pathlib.Path('judge/youlun-xia/recovery');rows=json.loads((R/'audit-graph.json').read_text(encoding='utf-8'))
for r in rows:
 assert len(r['questions'])<=1
 for q in r['questions']:
  assert q['type']==1 and q['duration']==-1 and q['pause_video']==1
  for c in q['choices']:
   assert not c.get('condition') and not c.get('native_action')
out={str(r['edge']):r for r in rows}
pathlib.Path('tasks/youlun-xia/graph.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print({'nodes':len(out),'unsupported_semantics':0})
