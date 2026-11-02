from pathlib import Path
import asyncio,json,sys,traceback
from types import SimpleNamespace
from playwright.async_api import async_playwright
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));A=R/'judge/kongguan/acceptance'
from harness.judge import Judge
async def run(b,mode,route):
 label=mode+'-'+route;d={'mode':mode,'route':route,'samples':[],'errors':[],'missing':[]};save=A/f'prefuneral-{mode}-storage.json';c=await b.new_context(viewport={'width':1920,'height':1080},storage_state=str(save));await c.tracing.start(screenshots=True,snapshots=True,sources=False);p=await c.new_page();p.on('pageerror',lambda e:d['errors'].append(str(e)));p.on('response',lambda r:d['missing'].append({'url':r.url,'status':r.status}) if r.status>=400 else None);j=Judge.load(R/'judge/kongguan/judge.json','kongguan',R)
 async def rec():await j.read(SimpleNamespace(page_expr=p.evaluate));j.update(len(d['samples']));d['samples'].append({'values':dict(j.values),'score':j.score()})
 try:
  await p.clock.install();await p.goto('http://127.0.0.1:8821/s1coffin/ending/e3funeral.html');await rec();assert not j.route_endings;pa=False;pb=False;expected='truth' if mode=='good' else 'endless' if route=='B2' else 'husband'
  for i in range(220):
   if not pa and await p.locator('.choice[data-id="'+('A1' if route=='A1' else 'A2')+'"]').count():await p.locator('.choice[data-id="'+('A1' if route=='A1' else 'A2')+'"]').click();pa=True
   elif pa and route!='A1' and not pb and await p.locator('.choice[data-id="'+route+'"]').count():await p.locator('.choice[data-id="'+route+'"]').click();pb=True
   else:await p.mouse.click(100,100)
   await p.clock.run_for(15000)
   if await p.evaluate(j.cfg['hooks'][expected]['expr']):await rec();break
  assert expected in j.route_endings,j.score();d['ending']=expected;d['score']=j.score();d['timing']='Virtual browser clock advances authored typing/animation timers; all choices are native UI clicks, no state writes or game function calls.';await p.screenshot(path=str(A/f'ending-{label}.png'));await c.storage_state(path=str(A/f'ending-{label}-storage.json'))
  if mode=='good' and route=='A1':
   await p.locator('.ending-btn').filter(has_text='继 续 前 行').click();await p.wait_for_url('**/prelude-watercell.html');d['sequel_prelude']=True;await rec();d['prelude_title']=await p.title()
  if mode=='bad' and route=='A1':
   await p.locator('.ending-btn').filter(has_text='时 光 回 溯').click();await p.wait_for_url('**/index-hanxiu.html');assert await p.evaluate('!localStorage.getItem("exam_passed")&&!localStorage.getItem("exam_answers")');d['authored_reset_clears_exam']=True
 except Exception as e:d['failure']=str(e);d['traceback']=traceback.format_exc()
 d['visible']=(await p.locator('body').inner_text())[-1500:];await c.tracing.stop(path=str(A/f'ending-{label}-trace.zip'));await c.close();(A/f'ending-{label}-report.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:d[k] for k in ['mode','route','ending','failure','errors','missing'] if k in d},ensure_ascii=True))
async def main():
 async with async_playwright() as pw:
  b=await pw.chromium.launch(channel='msedge',headless=True)
  for mode in ['good','bad']:
   for route in ['A1','B1','B2']:await run(b,mode,route)
  await b.close()
if __name__=='__main__':asyncio.run(main())
