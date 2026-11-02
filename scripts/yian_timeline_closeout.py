import asyncio,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from harness.config import load_config
from harness.browser_harness import BrowserHarness
from harness.judge import Judge
from harness.serve_local import LocalServer
async def main():
 out=R/'judge/yian-juanzong/verification/timeline-closeout';out.mkdir(parents=True,exist_ok=True);cfg=load_config(R/'configs/yian-juanzong.json');cfg['entry_url']='http://127.0.0.1:8844/index.html';cfg['allow_hosts']=['127.0.0.1:8844'];cfg['local_serve'].update(port=8844,ready_url=cfg['entry_url']);cfg['local_serve']['command'][-1]='8844';cfg['settle_ms']=100
 h=BrowserHarness(cfg,out);server=LocalServer();steps=[];j=Judge.load(R/cfg['judge_path'],'yian-juanzong',R)
 async def sample(name):
  v=await j.read(h);j.update(len(steps)+1);steps.append({'case':name,'timeline_10':v['timeline_10'],'timeline_12':v['timeline_12'],'score':j.score()})
 async def click(sel):
  loc=h.page.locator(sel).first;await loc.wait_for(state='visible');await loc.scroll_into_view_if_needed();b=await loc.bounding_box();assert b;assert await h.act({'op':'click','x':b['x']+b['width']/2,'y':b['y']+b['height']/2})=='ok';await sample(sel)
 async def nav(x):await click('#nav [data-view="'+x+'"]')
 try:
  server.start(cfg,R,out/'server.log');await h.start();await h.reset();await sample('fresh');assert not j.checkpoints
  await click('#btn-start');await click('#guide-close');await nav('timeline')
  for i in range(1,10):await click('#tl-pool [data-ev="ev_%03d"]'%i)
  assert 'timeline_10' not in j.checkpoints
  await click('#tl-clear')
  for i in [2,3,4,5,6,7,8,9,1,10,11,12]:await click('#tl-pool [data-ev="ev_%03d"]'%i)
  assert 'timeline_10' not in j.checkpoints and 'timeline_12' not in j.side
  await click('#tl-clear')
  for i in list(range(1,11))+[12,11]:await click('#tl-pool [data-ev="ev_%03d"]'%i)
  assert 'timeline_10' in j.checkpoints and 'timeline_12' not in j.side
  await click('#tl-clear')
  for i in range(1,13):await click('#tl-pool [data-ev="ev_%03d"]'%i)
  assert 'timeline_12' in j.side
  await h.reset();j=Judge.load(R/cfg['judge_path'],'yian-juanzong',R);await sample('fresh reset');assert not j.checkpoints and not j.side
  (out/'result.json').write_text(json.dumps({'passed':True,'normal_ui':True,'cases':'9 correct; clear; 3 other correct (12 different positions accumulated, never 10 simultaneously); 10 correct; 12 correct; fresh reset','steps':steps},ensure_ascii=False,indent=2),encoding='utf8');print('TIMELINE PASS')
 finally:await h.close();server.stop()
asyncio.run(main())
