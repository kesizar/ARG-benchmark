import json
from pathlib import Path
r=Path.cwd();p=r/'configs/wuluo-cun.json';d=json.loads(p.read_text(encoding='utf8'));d['notes_for_report'][0]='本地兼容修复保留原作。16 个关键点及 5 个诊断点；两条结局均为无好坏评级的正式完成。人工脚本验收不作为模型成绩。';p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
p=r/'judge/wuluo-cun/checkpoint-spec.json';old=p.read_text(encoding='utf8');(r/'judge/wuluo-cun/verification/checkpoint-spec-before-content.json').write_text(old,encoding='utf8');d=json.loads(old);opt={'track','stones','fog','carvings','spirit_3'}
for x in d['points']:x['role']='optional_diagnostic' if x['id'] in opt else 'critical'
d['point_count']=21;d['critical_point_count']=16;d['diagnostic_point_count']=5;d['counting_rule']='Directly supplied steps track/stones/fog/carvings and the semantically ambiguous spirit_3 are diagnostic. Other points count as critical; game requires all to advance.';p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
