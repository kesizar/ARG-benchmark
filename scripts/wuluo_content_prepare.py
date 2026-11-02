import json,difflib
from pathlib import Path
r=Path.cwd();p=r/'judge/wuluo-cun/judge.json';old=p.read_text(encoding='utf8');(r/'judge/wuluo-cun/verification/judge-before-content.json').write_text(old,encoding='utf8');d=json.loads(old);optional={'track','stones','fog','carvings','spirit_3'}
for x in d['checkpoints']:
 if x['id'] in optional:x['role']='optional'
for route in d['routes']:route['gates']=[x for x in route['gates'] if x not in optional]
new=json.dumps(d,ensure_ascii=False,indent=2)+'\n';p.write_text(new,encoding='utf8');(r/'judge/wuluo-cun/verification/judge-content.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='before',tofile='after')),encoding='utf8')
s=(r/'judge/wuluo-cun/verify_sample.py').read_text(encoding='utf8').replace('len(self.judge.checkpoints)==21','len(self.judge.checkpoints)==16').replace('acceptance.json','content-closeout.json');(r/'judge/wuluo-cun/verify_content_closeout.py').write_text(s,encoding='utf8');print('judge 16 critical 5 diagnostic')
