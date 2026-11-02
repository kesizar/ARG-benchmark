import json
from pathlib import Path
r=Path.cwd(); jp=r/'judge/feiqi-yiyuan/judge.json'; cp=r/'configs/feiqi-yiyuan.json'; old=json.loads(jp.read_text(encoding='utf8')); base=json.loads(cp.read_text(encoding='utf8'))
(r/'judge/feiqi-yiyuan/verification/judge-before-cumulative.json').write_text(json.dumps(old,ensure_ascii=False,indent=2),encoding='utf8')
for target in ['follow','truth','deeper','final']:
 j=json.loads(json.dumps(old)); route=next(x for x in j['routes'] if x['id']==target); j['routes']=[route]; j['ending']=route['ending']; j['events']={x+'_observed':{'hook':x+'_ending','op':'truthy'} for x in ['follow','truth','deeper','final'] if x!=target}; path=jp if target=='final' else jp.parent/('judge-'+target+'.json'); path.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 c=json.loads(json.dumps(base)); c['judge_path']=path.relative_to(r).as_posix(); c['model_visible']['intro'] += ' 本次任务目标：'+{'follow':'回到帖子查看后续。','truth':'解锁手机后回帖查看真相。','deeper':'进入医院内网后回帖查看更深的真相。','final':'继续调查至院长手记，再回帖子查看最深的真相。'}[target]; c['notes_for_report'] += ['本配置只以 '+target+' 层终止；其他尾声为可继续事件。']; path=cp if target=='final' else cp.parent/('feiqi-yiyuan-'+target+'.json'); path.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('wrote target configs and judges')
