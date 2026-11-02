import json,difflib
from pathlib import Path
r=Path(__file__).resolve().parents[1];p=r/'judge/xinshiji/judge.json';before=p.read_text('utf8');backup=r/'tasks/xinshiji/source/judge.before-checkpoints.json'
if not backup.exists():backup.write_text(before,encoding='utf8')
d=json.loads(before)
defs={'company-lock':("['/sunflower.html','/darkweb.html'].some(x=>location.pathname.endsWith(x))",'critical'), 'garden':("location.pathname.endsWith('/darkweb.html')",'critical'), 'manager-food':("Number(localStorage.getItem('sunStep')||0)>=2",'optional'),'manager-parents':("Number(localStorage.getItem('sunStep')||0)>=3",'optional'),'manager-hobby':("Number(localStorage.getItem('sunStep')||0)>=4",'optional'),'manager-date':("Number(localStorage.getItem('sunStep')||0)>=5",'optional'),'member':("location.pathname.endsWith('/member-page.html')",'optional'),'portraits':("location.pathname.endsWith('/member-page.html')&&typeof photosAllLit!=='undefined'&&photosAllLit",'optional')}
for k,(expr,role) in defs.items():d['hooks'][k]={'type':'js_truthy','expr':expr}
for k in ['archive','chat','plan']:defs[k]=('', 'critical')
d['checkpoints']=[{'id':k,'hook':k,'op':'truthy','role':v[1]} for k,v in defs.items()]
d['hooks']['survey']={'type':'js_truthy','expr':"localStorage.getItem('surveyPassed')==='true'"}
d['events']={'survey_passed':{'hook':'survey','op':'truthy'}}
d['routes'][0]['gates']=['company-lock','garden','archive','chat','plan']
after=json.dumps(d,ensure_ascii=False,indent=2)+'\n';p.write_text(after,encoding='utf8')
(r/'judge/xinshiji/recovery/checkpoint-judge.diff').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='judge.before-checkpoints.json',tofile='judge.json')),encoding='utf8')
print('5 critical reasoning gates,6 optional reasoning gates; survey unscored event')
