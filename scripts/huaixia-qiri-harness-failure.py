"""Run a game-specific scripted policy through the unmodified evaluator loop."""
import asyncio,json,sys
from pathlib import Path
sys.path.insert(0,str(Path('.').resolve()))
from harness.config import load_config
from harness.loop import _episode, make_harness
from harness.judge import Judge
from harness.serve_local import LocalServer
flee='--flee' in sys.argv

class Policy:
 def act(self,obs):
  es=obs.get('elements',[]); text=obs.get('visible_text','')
  def find(label): return next((e for e in es if e.get('label','')==label),None)
  def click(e): return {'op':'click','n':e['n']}
  for label in ('新的七日','入村'):
   if find(label):return click(find(label))
  if '点击跳过' in text:
   e=next((e for e in es if '点击跳过' in e.get('label','')),None)
   if e:return click(e)
  if flee:
   e=next((e for e in es if '今晚就走，出村' in e.get('label','')),None)
   if e:return click(e)
   if '探 索' in text:
    buttons=[e for e in es if e['kind']=='button' and e['label'] not in {'状态','物品','线索','流程','存档','设置'}]
    if buttons:return click(buttons[-1])
  if '按五行相生的顺序' in text:
   for label in ['金','木','水','火','土']:
    if find(label):return click(find(label))
   if find('确认排列'):return click(find('确认排列'))
  if find('静坐，等子时'): return click(find('静坐，等子时'))
  ignored={'状态','物品','线索','流程','存档','设置'}
  candidates=[e for e in es if e['kind']=='button' and e['label'] not in ignored and e['label']]
  if candidates:return click(candidates[0])
  return {'op':'wait','ms':500}

async def main():
 root=Path('.').resolve();cfg=load_config(root/'configs/huaixia-qiri.json','B')
 cfg['id']='huaixia-qiri-harness-flee' if flee else 'huaixia-qiri-harness-failure';cfg['limits']['max_steps']=260;cfg['settle_ms']=250
 run_dir=root/('runs/huaixia-qiri/harness-flee' if flee else 'runs/huaixia-qiri/harness-failure');run_dir.mkdir(parents=True,exist_ok=True)
 server=LocalServer();h=None
 try:
  server.start(cfg,root,run_dir/'server.log');h=make_harness(cfg,run_dir,True);await h.start()
  judge=Judge.load(root/cfg['judge_path'],cfg['id'],root)
  summary=await _episode(cfg,h,judge,Policy(),'script',run_dir)
  print(json.dumps({'ended_reason':summary.get('ended_reason'),'failure_id':summary.get('failure_id'),'failure_reached':summary.get('failure_reached'),'ending_reached':summary.get('ending_reached')},ensure_ascii=True))
 finally:
  if h: await h.close()
  server.stop()
asyncio.run(main())
