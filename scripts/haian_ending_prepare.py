import json,difflib
from pathlib import Path
r=Path.cwd()
p=r/'judge/haian-diaopin/judge.json'
old=p.read_text(encoding='utf8')
(r/'judge/haian-diaopin/evidence/judge-before-ending.json').write_text(old,encoding='utf8')
d=json.loads(old)
d['hooks']['ending']['expr']='(()=>{try{const s=JSON.parse(localStorage.getItem("coastfm893_save_v1")||"{}");return s.endingSeen===true && s.endingUnlocked===true && document.body.innerText.includes("真相拼图")}catch{return false}})()'
new=json.dumps(d,ensure_ascii=False,indent=2)+'\n'
p.write_text(new,encoding='utf8')
(r/'judge/haian-diaopin/evidence/judge-ending.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='before',tofile='after')),encoding='utf8')
s=(r/'scripts/haian_diaopin_acceptance.py').read_text(encoding='utf8')
s=s.replace("check('ending reached after recovery',score['ending_reached'] and score['ending_tier']=='normal',score)","check('ending not reached before transcript completion',not score['ending_reached'],score)")
s=s.replace("page.wait_for_timeout(25000);check('transcript complete',page.get_by_text('真相拼图',exact=False).count()>0)","page.get_by_role('button',name='跳过播放').click();page.wait_for_timeout(300);check('transcript complete',page.get_by_text('真相拼图',exact=False).count()>0);score=snap(page,j,4);check('completed ending scores',score['ending_reached'] and score['ending_tier']=='normal',score)")
s=s.replace("out/'acceptance.json'","out/'ending-closeout.json'")
(r/'scripts/haian_diaopin_ending_closeout.py').write_text(s,encoding='utf8')
print('done')
