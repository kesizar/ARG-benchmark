from pathlib import Path
import importlib.util,json
R=Path(__file__).resolve().parents[1];p=R/'judge/guangying-she/audit_judge.py';spec=importlib.util.spec_from_file_location('judge',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
canonical={'hintMode':'off','slots':m.ORDER,'solved':True,'checkedCount':1,'darkroom':False};cases=[]
for label,s,route,text,expected in [('fresh',{},'#/','',False),('locked-opening',{'hintMode':'off'},'#/opening','本页尚在布展中',False),('wrong-wall',{**canonical,'slots':m.ORDER[::-1]},'#/opening','名 誉 观 展 证',False),('unsubmitted',{**canonical,'solved':False},'#/wall','',False),('forged-solved-only',{'hintMode':'off','solved':True},'#/opening','名 誉 观 展 证',False),('guided',{**canonical,'hintMode':'on'},'#/opening','名 誉 观 展 证',False),('correct-wall',canonical,'#/wall','',False),('correct-ending-no-login',canonical,'#/opening','名 誉 观 展 证',True),('correct-ending-login',{**canonical,'darkroom':True},'#/opening','名 誉 观 展 证',True),('reset',{'hintMode':'off','slots':[None]*8},'#/','',False)]:
 result=m.evaluate(s,route,text);assert result['ending_reached']==expected;cases.append({'case':label,'state':s,'route':route,'result':result})
(R/'runs/guangying-she/judge-tests.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2),encoding='utf8');print('10 independent judge cases passed.')
