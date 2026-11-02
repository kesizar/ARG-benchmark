from pathlib import Path
import json,re
root=Path('.');task='mingde-zhuilou';t=root/'tasks'/task
base=json.loads((root/'configs/qingshu-shizong.json').read_text(encoding='utf-8'))
base.update(id=task,model_visible={'title':'明德中学坠楼案','intro':'你是警员岳月，调查明德中学坠楼案。通过屏幕和站内资料推理，提交案件报告。开局作者名线索尚待补充，本版本只供条件验收。'},entry_url='http://127.0.0.1:8831/index.html',judge_path=f'judge/{task}/judge.json',policy_script=[{'op':'give_up'}])
base['local_serve'].update(command=['python','scripts/serve_static.py','--root',f'tasks/{task}/mirror','--port','8831'])
base['notes_for_report']=['Conditional engineering fixture: first password depends on an author name absent from supplied player material. Not approved for formal scoring.','Three endings depend only on selected compensation agreement and Li Yang; unlocked document puzzles are optional.','Two orphan pages locked_mail and qiongdinghui are preserved but have no inbound game link.']
(root/'configs'/f'{task}.json').write_text(json.dumps(base,ensure_ascii=False,indent=2),encoding='utf-8')
def vis(file,sel): return f"location.pathname.endsWith('/{file}.html') && !!document.querySelector('{sel}') && getComputedStyle(document.querySelector('{sel}')).display!=='none'"
exprs={'boot':"location.pathname.endsWith('/desk.html')",'diary':vis('dairy','#diaryContent'),'logs':vis('work_logs','#hiddenJournal'),'account':vis('account_records','#main-content.show'),'counseling':vis('counseling_records','#recordSection'),'monitor':vis('monitoring','#mainContainer'),'office':"location.pathname.endsWith('/monitoring.html') && typeof officePasswordEntered!=='undefined' && officePasswordEntered",'mail':vis('locked_mail','#emailContainer'),'server':vis('qiongdinghui','#serverContent'),'ark':vis('qiongdinghui','#arkContent')}
for i in range(1,4):exprs[f'ending{i}']=vis('evidence',f'#ending{i}')
exprs['compensation']="location.pathname.endsWith('/evidence.html') && typeof selectedEvidences!=='undefined' && selectedEvidences.includes('赔偿协议') && [1,2,3].some(i=>getComputedStyle(document.querySelector('#ending'+i)).display!=='none')"
exprs['witness']="location.pathname.endsWith('/evidence.html') && typeof selectedEvidences!=='undefined' && selectedEvidences.includes('李阳') && [1,2,3].some(i=>getComputedStyle(document.querySelector('#ending'+i)).display!=='none')"
judge={'hooks':{k:{'type':'js_truthy','expr':v} for k,v in exprs.items()},'checkpoints':[{'id':k,'hook':k,'op':'truthy','role':'critical' if k in ['compensation','witness'] else 'diagnostic' if k in ['boot','mail','server','ark'] else 'optional'} for k in exprs if not k.startswith('ending')],'events':{},'routes':[{'id':'silent','tier':'bad','gates':[],'ending':{'hook':'ending1','op':'truthy'}},{'id':'late-justice','tier':'normal','gates':['compensation'],'ending':{'hook':'ending2','op':'truthy'}},{'id':'bright-trial','tier':'good','gates':['compensation','witness'],'ending':{'hook':'ending3','op':'truthy'}}],'ending':{'hook':'ending3','op':'truthy'}}
(root/'judge'/task/'judge.json').write_text(json.dumps(judge,ensure_ascii=False,indent=2),encoding='utf-8')
# Inventory every static file link and literal window navigation.
files={p.name for p in (t/'mirror').iterdir()};edges=[];missing=[]
for p in (t/'mirror').glob('*.html'):
 s=p.read_text(encoding='utf-8')
 for dest in sorted(set(re.findall(r'''["']([A-Za-z_]+\.html)["']''',s))):
  edges.append([p.name,dest])
  if dest not in files:missing.append([p.name,dest])
(t/'evidence/link-inventory.json').write_text(json.dumps({'edges':edges,'missing':missing,'external_live_dependency':'Only cosmetic FontAwesome stylesheet; blocked in L1. ProtonMail-looking URL is readonly text, not a service.'},indent=2),encoding='utf-8')
print('created config/judge; missing references',missing)
