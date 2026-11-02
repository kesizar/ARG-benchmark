import asyncio, json, os, pathlib, subprocess, sys, time
ROOT=pathlib.Path(os.environ.get('MIDNIGHT_ROOT',pathlib.Path(__file__).resolve().parents[2])).resolve(); sys.path.insert(0,str(ROOT))
from harness.browser_harness import BrowserHarness
from harness.judge import Judge
async def main():
 port=int(os.environ.get('MIDNIGHT_PORT','8961')); live=os.environ.get('MIDNIGHT_L3')=='1'; cfg=json.loads((ROOT/('configs/new31-midnight-l3.json' if live else 'configs/new31-midnight.json')).read_text(encoding='utf8'));
 if not live: cfg['entry_url']=f'http://127.0.0.1:{port}/';cfg['allow_hosts']=[f'127.0.0.1:{port}'];
 p=None if live else subprocess.Popen([sys.executable,str(ROOT/'scripts/serve_static.py'),'--root',str(ROOT/'tasks/new31-midnight/mirror'),'--port',str(port)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 h=BrowserHarness(cfg,ROOT); result={}; step=0
 try:
  await asyncio.sleep(1);await h.start();await h.reset(); page=h.page;j=Judge.load(ROOT/'judge/new31-midnight/judge.json',cfg['id'],ROOT)
  async def read(label):
   nonlocal step
   step+=1; values=await j.read(h);j.update(step);result[label]={'values':values,'score':j.score()}
  async def drag(a,b):
   src=await page.locator(f'[data-id="{a}"] .pin').bounding_box();dst=await page.locator(f'[data-id="{b}"]').bounding_box();assert src and dst,(a,b);await page.mouse.move(src['x']+src['width']/2,src['y']+src['height']/2);await page.mouse.down();await page.mouse.move(dst['x']+dst['width']/2,dst['y']+dst['height']/2,steps=15);await page.mouse.up();await page.wait_for_timeout(300)
  await read('initial')
  for i,(a,b,c,wrong) in enumerate([('clock','watch','photo','decoy'),('route','receipt','car','alibi'),('blueprint','vent','tapeclue','memo')],1):
   await drag(a,wrong);await read(f'case{i}_wrong');assert len(j.checkpoints)==i-1 and not j.ending_reached
   await drag(a,b);await read(f'case{i}_partial');assert len(j.checkpoints)==i-1 and not j.ending_reached
   await drag(b,c);await page.wait_for_timeout(3200);await read(f'case{i}_completed');assert len(j.checkpoints)==i
  assert j.ending_reached;result['ending_visible']=await page.locator('#ending').evaluate("e=>e.classList.contains('show')")
  await page.locator('#restart').click();await page.wait_for_timeout(300); fresh=Judge.load(ROOT/'judge/new31-midnight/judge.json',cfg['id'],ROOT);await fresh.read(h);fresh.update(1);result['restart_score']=fresh.score();assert not fresh.checkpoints and not fresh.ending_reached
  await h.reset();fresh=Judge.load(ROOT/'judge/new31-midnight/judge.json',cfg['id'],ROOT);await fresh.read(h);fresh.update(1);result['new_context_score']=fresh.score();assert not fresh.checkpoints and not fresh.ending_reached
  result['blocked_requests']=h.blocked;result['requests']=h.all_requests;result['passed']=True
 finally:
  await h.close();
  if p: p.terminate();p.wait(timeout=10)
 print(json.dumps(result,ensure_ascii=False,indent=2))
asyncio.run(main())
