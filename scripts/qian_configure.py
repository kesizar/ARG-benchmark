"""Generate seven separately bounded L1 evaluation units; finite source inventory private."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];TASK='qian-anon'
NAMES={'quiz':'日谜对对碰','pipa':'弹心爱的琵琶吧','cross':'crossword 大赛','hunt':'世界第一 puzzlehunt 游戏设计师','surf':'海啸冲浪','maze':'汉字方阵迷宫','gal':'与时柒的七日'}
INSTALL=r'''(() => {
 if(!window.__qianJudge){const R=window.__qianJudge={quiz:{},cross:{},attempts:[]};
 const capture=e=>{
  const b=e.target.closest?.('#quiz-main .opt');
  if(b&&!b.disabled){const round=QZ.round,old=QZ.ps,q=QZ.cur.q,choice=b.dataset.o;setTimeout(()=>{const ok=b.disabled&&QZ.ps===old+2;R.quiz[round]=ok;R.attempts.push({key:'quiz',round,q,choice,ok});},0);}
  const jump=(e.type==='click'&&e.target.closest?.('[onclick="crossJump()"]'))||(e.type==='keydown'&&e.key==='Enter'&&e.target.id==='cw-input');
  if(jump&&typeof CX!=='undefined'&&CX&&!CX.over&&!CX.busy){const pos=CX.aPos,value=document.querySelector('#cw-input')?.value;setTimeout(()=>{if(CX.aPos-pos>1){R.cross.valid=true;if(value?.trim().length>=5)R.cross.long=true;R.attempts.push({key:'cross',value,jump:CX.aPos-pos});}},0);}
 };document.addEventListener('click',capture,true);document.addEventListener('keydown',capture,true);
 }return RESULT;
})()'''
def hook(expr):return {'type':'js_truthy','expr':INSTALL.replace('RESULT',expr)}
def write(p,o):p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
 units=[]
 for key,name in NAMES.items():
  ident=f'{TASK}-{key}';cfg=json.loads((ROOT/'configs/hushan-xiangcheng-iol.json').read_text(encoding='utf-8'));cfg.update(id=ident,judge_path=f'judge/{TASK}/{key}.json');cfg['local_serve']['command'][3]=f'tasks/{TASK}/mirror';cfg['model_visible']={'title':name,'intro':f'这是千早爱音解谜社合集。本次只进行「{name}」一局，从大厅进入对应游戏，按屏幕规则完成。其他小游戏不属于本次任务。只使用屏幕信息与列出的动作。'};cfg['seed']=20261026;cfg['limits'].update(max_steps=500,max_seconds=1800,max_answer_submits=150);cfg['notes_for_report']=['Independent unit of original base664:0521. Snapshot v1.4 differs from original row label v1.2.']
  if key=='surf':cfg['actions_enabled'].append('long_press');cfg['obs_mode']='A';cfg['obs_modes_to_run']=['A'];cfg['model_visible']['intro']+=' 持续移动需对画面下方方向按钮使用long_press，ms为按住毫秒数。本游戏实时进行，模型推理等待也计入游戏时间。'
  j={'hooks':{},'checkpoints':[],'routes':[],'events':{},'ending':None,'request_milestones':[],'submit_conclusion':{'enabled':False,'schema':None}}
  def cp(cid,expr,role='critical'):
   j['hooks'][cid]=hook(expr);j['checkpoints'].append({'id':cid,'hook':cid,'op':'truthy','role':role})
  def end(eid,expr,tier='normal',gates=None):
   j['hooks'][eid]=hook(expr);j['routes'].append({'id':eid,'tier':tier,'gates':gates if gates is not None else [x['id'] for x in j['checkpoints'] if x['role']=='critical'],'ending':{'hook':eid,'op':'truthy'}})
  if key=='quiz':
   for i in range(1,11):cp(f'round_{i:02}',f'window.__qianJudge.quiz[{i}]===true')
   for label,part,tier in [('win','你赢了！','good'),('lose','机器人赢了。','bad'),('draw','平局！','normal')]:end(label,f"document.querySelector('#quiz-main .ending p')?.textContent.includes({json.dumps(part,ensure_ascii=False)})===true",tier)
  elif key=='pipa':
   cp('answer_acquired',"!!document.querySelector('#pipa-main .ending h2')&&document.querySelector('#pipa-main .ending h2').textContent.includes('答案到手')");cp('star_buff',"typeof PP!=='undefined'&&PP&&PP.popipa===true",'optional')
   end('answer',"document.querySelector('#pipa-main .ending h2')?.textContent.includes('答案到手')===true",'normal');end('caught',"document.querySelector('#pipa-main .ending h2')?.textContent.includes('道 歉 信')===true",'bad',[])
  elif key=='cross':
   cp('valid_word_jump','window.__qianJudge.cross.valid===true');cp('long_word_bonus','window.__qianJudge.cross.long===true','optional')
   for label,text,tier in [('win','钱爱音获胜！','good'),('lose','冯祥子获胜','bad'),('draw_unreachable','同时到达终点！','normal')]:end(label,f"document.querySelector('#cross-main .ending h2')?.textContent==={json.dumps(text,ensure_ascii=False)}",tier)
  elif key=='hunt':
   for attr,nameattr in [('c','creativity'),('l','logic'),('r','reputation')]:cp(nameattr,f"!!document.querySelector('#hunt-main .ending')&&H.{attr}>=9&&H.e>0")
   for eid,text,tier in [('best','世界第一 puzzlehunt 设计师','good'),('great','圈内顶流设计师','good'),('normal','完赛即胜利','normal'),('flop','史诗级烂尾','bad'),('burnout','燃尽了','bad')]:end(eid,f"document.querySelector('#hunt-main .ending h2')?.textContent==={json.dumps(text,ensure_ascii=False)}",tier)
  elif key=='surf':
   end('escaped',"document.querySelector('#surf-main .ending h2')?.textContent==='逃离成功！'",'normal',[]);end('swallowed',"document.querySelector('#surf-main .ending h2')?.textContent==='被速记吞没'",'bad',[])
  elif key=='maze':
   cp('unlocked_exit',"!!document.querySelector('#maze-main .ending')");end('escaped',"document.querySelector('#maze-main .ending h2')?.textContent==='「谜子万岁！」'")
   for ch in '谜子万岁':j['hooks']['collected_'+ch]=hook(f"typeof MZ!=='undefined'&&MZ&&MZ.got.includes({json.dumps(ch,ensure_ascii=False)})");j['events']['collected_'+ch]={'hook':'collected_'+ch,'op':'truthy'}
  else:
   for eid,title in [('hi','结局 · 哈柒谜一号'),('mid','结局 · 远征队队友'),('lo','结局 · 速记地狱')]:end(eid,f"document.querySelector('#gal-text b')?.textContent==={json.dumps(title,ensure_ascii=False)}",'normal',[])
  write(f'configs/{ident}.json',cfg);write(f'judge/{TASK}/{key}.json',j);units.append({'id':ident,'key':key,'title':name,'config':f'configs/{ident}.json','judge':cfg['judge_path'],'status':'pending_ui_verification','scope':'first round only','endings':[x['id'] for x in j['routes']]})
 maincfg=json.loads((ROOT/f'configs/{TASK}-gal.json').read_text(encoding='utf-8'));maincfg['id']=TASK;maincfg['notes_for_report'].append('Legacy main config aliases GAL only, not full collection.');write(f'configs/{TASK}.json',maincfg)
 write(f'tasks/{TASK}/collection.json',{'record_id':'base664:0521','snapshot_version':'v1.4','units':units,'resource_sharing':f'tasks/{TASK}/mirror/index.html','global_ending':None,'default_config_scope':'GAL alias only','score_scope':'Quiz: correct player answers only, excludes robot randomness. Pipa: answer plus optional buff. Cross: submitted valid-word mechanic plus optional long-word bonus. Hunt: native final three >=9 attribute targets, one planning problem with rubric components. Maze: one route puzzle, ordinary collectible events do not become four puzzles. Surf and GAL: no invented reasoning checkpoints; native outcome only, benchmark inclusion requires review.','unreachable_branch':'Cross draw: check order ends immediately when either actor first reaches59; no legitimate normal transition can make both59 before an earlier end. Never fake a UI proof.'})
if __name__=='__main__':main()
