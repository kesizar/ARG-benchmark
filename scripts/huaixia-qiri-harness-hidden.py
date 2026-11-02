"""Screen-observation policy for a two-playthrough hidden-ending harness test."""
import asyncio,json,sys
from pathlib import Path
sys.path.insert(0,str(Path('.').resolve()))
from harness.config import load_config
from harness.loop import _episode, make_harness
from harness.judge import Judge
from harness.serve_local import LocalServer

class Policy:
 def __init__(self):
  self.ng=1;self.shop=0;self.temple=False;self.tablet=False;self.deduced=False;self.picked=set();self.panel=False
 def act(self,obs):
  es=obs.get('elements',[]);text=obs.get('visible_text','')
  def find(label): return next((e for e in es if e.get('label','')==label),None)
  def has(label): return next((e for e in es if label in e.get('label','')),None)
  def click(e):return {'op':'click','n':e['n']}
  if find('返回标题 · 开始新的周目'):
   if self.ng==1:self.ng=2;return click(find('返回标题 · 开始新的周目'))
  new_game=next((e for e in es if e['kind']=='button' and e['label'].startswith('新的七日')),None)
  if new_game:return click(new_game)
  if '选择视角' in text and self.ng==2:
   e=has('鬼魂视角')
   if e and not self.panel:self.panel=True;return click(e)
  if find('入村'):return click(find('入村'))
  if '点击跳过' in text:
   e=has('点击跳过')
   if e:return click(e)
  if self.ng==2 and self.shop==1 and '探 索' in text:self.shop=2
  if self.ng==2 and '线索 · 证据链' in text:
   if '推理成立：' in text and '我是谁' in text:self.deduced=True
   if self.deduced and find('✕'):return click(find('✕'))
   for name in ['镜中无人','广播新闻','犬吠']:
    if name not in self.picked and has(name):self.picked.add(name);return click(has(name))
   if len(self.picked)==3 and find('串联线索 · 推理'):return click(find('串联线索 · 推理'))
   return {'op':'wait','ms':500}
  if self.ng==2 and self.shop==2 and not self.deduced and find('线索'):return click(find('线索'))
  for label in ['拿起铜镜，看一眼','静坐，等子时']:
   if find(label):return click(find(label))
  if self.ng==2:
   for phrase in ['【鬼魂视角】看最下一排','【鬼魂视角】"我知道我是谁了']:
    e=has(phrase)
    if e:
     if '看最下一排' in phrase:self.tablet=True
     return click(e)
   if '按十二生肖的正确顺序' in text and find('暂时放弃'):return click(find('暂时放弃'))
   if find('整理牌位'):
    if not self.tablet:return {'op':'scroll','x':640,'y':850,'dy':500}
    if find('离开'):return click(find('离开'))
  if self.ng==1 and has('今晚就走，出村'):return click(has('今晚就走，出村'))
  if '探 索' in text:
   buttons=[e for e in es if e['kind']=='button' and e['label'] not in {'状态','物品','线索','流程','存档','设置'}]
   if self.ng==2 and '第二日 · 槐下村' in text and self.shop==0:
    e=next((e for e in buttons if '小卖部' in e['label']),None)
    if e:self.shop=1;return click(e)
   if self.ng==2 and '第四日 · 槐下村' in text and not self.temple:
    e=next((e for e in buttons if '祠堂' in e['label']),None)
    if e:self.temple=True;return click(e)
   if buttons:return click(buttons[-1])
  if '按退亲仪式的正确次序' in text:
   for label in ['净手','请灵','焚书','断线','送归']:
    if find(label):return click(find(label))
   if find('确认排列'):return click(find('确认排列'))
  ignored={'状态','物品','线索','流程','存档','设置'}
  buttons=[e for e in es if e['kind']=='button' and e['label'] not in ignored and e['label']]
  if buttons:return click(buttons[0])
  return {'op':'wait','ms':500}

async def main():
 root=Path('.').resolve();cfg=load_config(root/'configs/huaixia-qiri-hidden.json','B')
 if '--port=8812' in sys.argv:
  port=cfg['local_serve']['port'];cfg['entry_url']=cfg['entry_url'].replace(str(port),'8812');cfg['allow_hosts']=['127.0.0.1:8812']
  cfg['local_serve']['port']=8812;cfg['local_serve']['ready_url']=cfg['local_serve']['ready_url'].replace(str(port),'8812');cfg['local_serve']['command'][-1]='8812'
 cfg['id']='huaixia-qiri-harness-hidden';cfg['limits']['max_steps']=600;cfg['settle_ms']=250
 run_dir=root/'runs/huaixia-qiri/harness-hidden';run_dir.mkdir(parents=True,exist_ok=True)
 server=LocalServer();h=None
 try:
  server.start(cfg,root,run_dir/'server.log');h=make_harness(cfg,run_dir,True);await h.start()
  judge=Judge.load(root/cfg['judge_path'],cfg['id'],root)
  summary=await _episode(cfg,h,judge,Policy(),'script',run_dir)
  print(json.dumps({k:summary.get(k) for k in ['ended_reason','route_id','failure_id','ending_reached','failure_reached','checkpoints_reached','checkpoints_total']},ensure_ascii=True))
 finally:
  if h:await h.close()
  server.stop()
asyncio.run(main())
