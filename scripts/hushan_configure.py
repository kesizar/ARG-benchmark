"""Collection-specific evaluator configuration; never changes game answers."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];TASK='hushan-xiangcheng'
NAMES={'ids':'IDS 拆字工坊','radical':'鉝猫偏旁正名所','iol':'IOL 迷你体验赛','family':'语言归队大作战','tone':'声调大师','merge':'汉字合体消消乐'}
IOL=[('请翻译：我 追 月亮','ne mi lu ka'),('请翻译：月亮 看 你','lu su ta ka'),('请翻译：星星 追 我','ku mi ne ka'),('请用数数语写出：8','mu ro ki'),('请用数数语写出：25','ze ze mu'),('请用数数语写出：14','ze ro ro'),('yama = 山。「群山」怎么说？','yama yama'),('warai = 笑。「笑了又笑」怎么说？','warai warai'),('toshi = 年。「每一年」怎么说？','toshi toshi')]
INSTALL=r"""(() => {
 if(!window.__hushanJudge){
 const R=window.__hushanJudge={slots:{},iol:{},merge:{},attempts:[]};
 const score=k=>+(document.querySelector('#'+k+'-hud')?.textContent.match(/(?:得分|⭐(?:\s*分数)?)\s*(\d+)/)?.[1]||0);
 const submit=e=>{
  const b=e.target.closest?.('.opt');
  if(b&&!b.disabled){const key=b.closest('.screen')?.id.replace('screen-',''),old=score(key),slot=document.querySelector('#'+key+'-hud')?.textContent.match(/第\s*(\d+)/)?.[1],q=b.closest('[id$="-main"]').querySelector('.quiz-q').textContent,choice=b.textContent;
   setTimeout(()=>{const ok=b.disabled&&score(key)===old+1; R.slots[key]??={};R.slots[key][slot]=ok;R.attempts.push({key,slot,q,choice,ok});});}
  const input=document.querySelector('#iol-input');
  if(input&&!input.disabled&&((e.type==='click'&&e.target.closest?.('[onclick="iolCheck()"]'))||(e.type==='keydown'&&e.key==='Enter'&&e.target===input))){const q=[...document.querySelectorAll('#iol-main > p')].at(-1)?.textContent,old=score('iol'),value=input.value;
   setTimeout(()=>{const ok=input.disabled&&document.querySelector('#iol-msg').textContent.includes('✔');R.iol[q]=ok;R.attempts.push({key:'iol',q,value,ok});});}
  const cell=e.target.closest?.('.mg-cell');
  if(cell&&e.type==='click'&&!document.querySelector('#merge-main .ending')){const ch=cell.textContent,old=score('merge');setTimeout(()=>{if(score('merge')>old){const level='木人口日火水土又一'.includes(ch)?'base_merge':'林从吕昌炎沝圭双二'.includes(ch)?'tier2_merge':'tier3_clear';R.merge[level]=true;R.attempts.push({key:'merge',ch,level,gain:score('merge')-old});}});}
 };
 document.addEventListener('click',submit,true);document.addEventListener('keydown',submit,true);
 } return REPLACE;
})()"""
def hook(expr):return {'type':'js_truthy','expr':INSTALL.replace('REPLACE',expr)}
def write(p,o):
 p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
 units=[]
 for key,name in NAMES.items():
  ident=f'{TASK}-{key}';cfg=json.loads((ROOT/'configs/sis.json').read_text(encoding='utf-8'))
  cfg.update(id=ident,entry_url='http://127.0.0.1:8831/index.html',seed=20261026,judge_path=f'judge/{TASK}/{key}.json')
  cfg['model_visible']={'title':name,'intro':f'这是户山香澄解谜社合集。本次只评测「{name}」：从大厅进入该游戏，完成一轮并取得尽可能高的成绩。只根据屏幕信息推理与操作。其他小游戏和友情链接不属于本次任务。'}
  cfg['local_serve'].update(command=['python','scripts/serve_static.py','--root',f'tasks/{TASK}/mirror','--port','8831'],ready_url=cfg['entry_url'])
  cfg['limits'].update(max_steps=180,max_seconds=1800,max_answer_submits=40);cfg['notes_for_report']=['One independently scored unit of base664:0445, not whole-collection completion.'];cfg['account_requirement']='none'
  judge={'hooks':{},'checkpoints':[],'routes':[],'events':{},'ending':None,'request_milestones':[],'submit_conclusion':{'enabled':False,'schema':None}}
  if key in ['ids','radical','family','tone']:
   for i in range(1,11):
    cp=f'question_{i:02}';judge['hooks'][cp]=hook(f'window.__hushanJudge.slots.{key}?.[{i}]===true');judge['checkpoints'].append({'id':cp,'hook':cp,'op':'truthy','role':'critical','description':'Correct submitted answer in sampled round slot '+str(i)})
   for rank,(lo,hi) in enumerate([(9,10),(6,8),(3,5),(0,2)]):
    end=f'rank_{rank}';judge['hooks'][end]=hook(f"(() => {{const e=document.querySelector('#{key}-main .ending h2');if(!e)return false;const n=parseInt(e.textContent);return n>={lo}&&n<={hi};}})()")
    judge['routes'].append({'id':end,'tier':'normal','gates':[p['id'] for p in judge['checkpoints']],'ending':{'hook':end,'op':'truthy'}})
  elif key=='iol':
   for i,(q,ans) in enumerate(IOL,1):
    cp=f'iol_{i:02}';judge['hooks'][cp]=hook(f'window.__hushanJudge.iol[{json.dumps(q,ensure_ascii=False)}]===true');judge['checkpoints'].append({'id':cp,'hook':cp,'op':'truthy','role':'critical','description':q})
   for end,lo,hi in [('preparatory',7,9),('experience',0,6)]:
    judge['hooks'][end]=hook(f"(() => {{const e=document.querySelector('#iol-main .ending h2');if(!e)return false;const n=parseInt(e.textContent);return n>={lo}&&n<={hi};}})()")
    judge['routes'].append({'id':end,'tier':'normal','gates':[p['id'] for p in judge['checkpoints']],'ending':{'hook':end,'op':'truthy'}})
  else:
   for cp in ['base_merge','tier2_merge','tier3_clear']:
    judge['hooks'][cp]=hook(f'window.__hushanJudge.merge.{cp}===true');judge['checkpoints'].append({'id':cp,'hook':cp,'op':'truthy','role':'optional' if cp=='tier3_clear' else 'critical'})
   for end,title,gates in [('triple','三叠字制造者！',['base_merge','tier2_merge']),('practice','合体练习生',['base_merge'])]:
    judge['hooks'][end]=hook(f"document.querySelector('#merge-main .ending p b')?.textContent==={json.dumps(title,ensure_ascii=False)}")
    judge['routes'].append({'id':end,'tier':'normal','gates':gates,'ending':{'hook':end,'op':'truthy'}})
  write(f'configs/{ident}.json',cfg);write(f'judge/{TASK}/{key}.json',judge)
  units.append({'id':ident,'game':key,'title':name,'config':f'configs/{ident}.json','judge':cfg['judge_path'],'shared_resources':f'tasks/{TASK}/mirror','endings':[r['id'] for r in judge['routes']],'status':'pending_ui_verification'})
 # Main config is explicitly the IDS unit. The collection manifest, not main config, represents the original record.
 maincfg=json.loads((ROOT/f'configs/{TASK}-ids.json').read_text(encoding='utf-8'));maincfg['id']=TASK;maincfg['notes_for_report'].append('Compatibility default aliases IDS only; never a collection-level score.');write(f'configs/{TASK}.json',maincfg)
 write(f'tasks/{TASK}/collection.json',{'record_id':'base664:0445','title':'户山香澄解谜社v1.2','scope':'six independent games; no authored global ending','main_config_scope':'IDS default alias only','units':units,'score_policy':'MCQ: ten sampled questions, one point per correct submitted slot; IOL: nine fixed subquestions, retries allowed, skip unscored; merge: reasoning milestones and native score; every game has round settlement, ranks not labeled good/bad.','randomness':'Original biased sort(random-.5), preserve mechanism. Full 16-item pool coverage is curator evidence across rounds, not a 16-point denominator for one 10-question round.','iol_questions':[{'id':f'iol_{i:02}','prompt':q,'answer_private':a} for i,(q,a) in enumerate(IOL,1)]})
if __name__=='__main__':main()
