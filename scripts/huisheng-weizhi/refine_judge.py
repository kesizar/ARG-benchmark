import json,pathlib
p=pathlib.Path('judge/huisheng-weizhi/judge.json');j=json.loads(p.read_text(encoding='utf8'))
for point in j['checkpoints']:
 if point['id'] in ('confession','handback'):point['role']='diagnostic'
for route in j['routes']:
 if route['id']=='handback':route['gates']=['null_search']
p.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf8')
