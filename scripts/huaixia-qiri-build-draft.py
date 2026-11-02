"""Generate provisional local integration and judge. Requires independent acceptance before use."""
import json, shutil
from pathlib import Path
task=Path('tasks/huaixia-qiri'); mirror=task/'mirror'; mirror.mkdir(exist_ok=True)
shutil.copyfile(task/'original.html',mirror/'index.html')
judge_dir=Path('judge/huaixia-qiri'); judge_dir.mkdir(exist_ok=True)
visible="!document.querySelector('.fixed.inset-0.z-40')"
hooks={}
for ident, phrase in {'wuxing':'锁开了。','ganzhi':'锁开了。门轴','shengxiao':'最后一块牌位归位','ritual':'净手。请灵。焚书。断线。'}.items():
 title={'wuxing':'樟木箱','ganzhi':'义庄内','shengxiao':'暗格','ritual':None}[ident]
 extra=f' && document.querySelector(".paper-panel").innerText.includes({json.dumps(title,ensure_ascii=False)})' if title else ''
 hooks[ident]={'type':'js_truthy','expr':f'{visible} && !!document.querySelector(".paper-panel") && document.querySelector(".paper-panel").innerText.includes({json.dumps(phrase,ensure_ascii=False)}){extra}'}
for ident,name in [('ded_axiu','阿秀其人'),('ded_minghun','冥婚真相'),('ded_touqi','头七之约'),('ded_self','我是谁')]:
 hooks[ident]={'type':'js_truthy','expr':f'''Array.from(document.querySelectorAll('.fixed.inset-0.z-40 .paper-panel div')).some(e => e.textContent.trim() === {json.dumps('推理成立：'+name,ensure_ascii=False)} && e.getClientRects().length > 0)'''}
endings=[('good','归土','good'),('vigil','守夜','normal'),('double','替身','normal'),('bride','新娘','bad'),('sacrifice','替嫁','bad'),('flee','出村','bad'),('hidden','头七','good')]
failures=[('sanity','纸人'),('yang','阳尽'),('hp','力竭')]
for ident,name,*_ in endings+failures:
 # Require the actual ending controls in the revealed panel, not guide text or an opacity-zero ending template.
 hooks['end_'+ident]={'type':'js_truthy','expr':f'''{visible} && Array.from(document.querySelectorAll('.paper-panel .opacity-100')).some(p => Array.from(p.querySelectorAll('div')).some(e => e.textContent.trim() === {json.dumps('「'+name+'」',ensure_ascii=False)}) && Array.from(p.querySelectorAll('button')).some(e => e.textContent.trim() === '返回标题 · 开始新的周目'))'''}
judge={'hooks':hooks,'checkpoints':[{'id':k,'hook':k,'op':'truthy'} for k in ['wuxing','ganzhi','shengxiao','ritual','ded_axiu','ded_minghun','ded_touqi','ded_self']], 'events':{},'routes':[{'id':i,'tier':tier,'gates':[],'ending':{'hook':'end_'+i,'op':'truthy'}} for i,n,tier in endings], 'ending':None,'terminal_failures':[{'id':'death_'+i,'hook':'end_'+i,'op':'truthy'} for i,n in failures], 'answer_sha256':[],'answer_hash_file':None,'request_milestones':[],'submit_conclusion':{'enabled':False,'schema':None},'rubric_path':None}
judge['checkpoints'][-1]['role']='optional'  # d_self is unavailable before the first ending.
(judge_dir/'judge.json').write_text(json.dumps(judge,ensure_ascii=False,indent=2),encoding='utf-8')
hidden_judge=dict(judge)
hidden_judge['routes']=[r for r in judge['routes'] if r['id']=='hidden']
hidden_judge['checkpoints']=[{k:v for k,v in c.items() if k!='role'} for c in judge['checkpoints']]
(judge_dir/'judge-hidden.json').write_text(json.dumps(hidden_judge,ensure_ascii=False,indent=2),encoding='utf-8')
config=json.loads(Path('configs/bailu-guangguang.json').read_text(encoding='utf-8'))
config.update(id='huaixia-qiri',model_visible={'title':'槐下七日','intro':'在槐下村度过七日。根据游戏中可见的线索和选项行动。'},judge_path='judge/huaixia-qiri/judge.json',viewport={'width':1280,'height':1000},account_requirement='none',notes_for_report=['Provisional config: judge and full routes not yet accepted.'],limits={'max_steps':800,'max_seconds':3600,'max_answer_submits':5})
config['local_serve']['command'][3]='tasks/huaixia-qiri/mirror'
Path('configs/huaixia-qiri.json').write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
hidden_config=dict(config)
hidden_config.update(id='huaixia-qiri-hidden',judge_path='judge/huaixia-qiri/judge-hidden.json',model_visible={'title':'槐下七日：隐藏结局','intro':'进入二周目，探索游戏的隐藏结局。根据游戏中可见的线索和选项行动。'},notes_for_report=['Draft hidden route configuration: normal story endings do not terminate this task, allowing a second playthrough. Death is still terminal failure.'])
Path('configs/huaixia-qiri-hidden.json').write_text(json.dumps(hidden_config,ensure_ascii=False,indent=2),encoding='utf-8')
