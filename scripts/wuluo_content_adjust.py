import json,difflib
from pathlib import Path
r=Path.cwd();p=r/'judge/wuluo-cun/judge.json';d=json.loads(p.read_text(encoding='utf8'))
for x in d['checkpoints']:
 if x['id']=='sachet_alignment':x['role']='optional'
for x in d['routes']:x['gates'].remove('sachet_alignment')
n=json.dumps(d,ensure_ascii=False,indent=2)+'\n';p.write_text(n,encoding='utf8');old=(r/'judge/wuluo-cun/verification/judge-before-content.json').read_text(encoding='utf8');(r/'judge/wuluo-cun/verification/judge-content.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),n.splitlines(True),fromfile='before',tofile='after')),encoding='utf8')
p=r/'judge/wuluo-cun/checkpoint-spec.json';d=json.loads(p.read_text(encoding='utf8'));next(x for x in d['points'] if x['id']=='sachet_alignment')['role']='optional_diagnostic';d['critical_point_count']=15;d['diagnostic_point_count']=6;d['counting_rule']+=' Sachet cut alignment is also diagnostic because the two displayed halves have identical imagery and lack a discriminating orientation.';p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
p=r/'configs/wuluo-cun.json';d=json.loads(p.read_text(encoding='utf8'));d['notes_for_report'][0]=d['notes_for_report'][0].replace('16 个关键点及 5 个诊断点','15 个关键点及 6 个诊断点');p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
p=r/'judge/wuluo-cun/verify_content_closeout.py';s=p.read_text(encoding='utf8').replace('len(self.judge.checkpoints)==16','len(self.judge.checkpoints)==15');p.write_text(s,encoding='utf8')
