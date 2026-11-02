"""Supplemental actual UI proof that optional collection is not required."""
import argparse,asyncio,hashlib,json,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--port',type=int,default=8821);a=p.parse_args();R=a.root.resolve();OUT=Path(__file__).resolve().parent/'verification';sys.path.insert(0,str(R))
from harness.config import load_config
from harness.browser_harness import BrowserHarness
from harness.judge import Judge
from harness.serve_local import LocalServer
async def main():
 c=load_config(R/'configs/duoluoleisi.json');c['entry_url']=f'http://127.0.0.1:{a.port}/index.html';c['allow_hosts']=[f'127.0.0.1:{a.port}'];c['local_serve'].update(port=a.port,ready_url=c['entry_url']);c['local_serve']['command'][-1]=str(a.port)
 h=BrowserHarness(c,OUT);server=LocalServer();result={'runtime_root':str(R),'kind':'additional_packaged_runtime_minimal_UI_not_model_score','routes':[],'resource_sha256':hashlib.sha256((R/'tasks/duoluoleisi/mirror/index.html').read_bytes()).hexdigest()}
 async def click(sel):
  l=h.page.locator(sel).first;await l.scroll_into_view_if_needed();await l.click(trial=True);b=await l.bounding_box();assert b;assert await h.act({'op':'click','x':b['x']+b['width']/2,'y':b['y']+b['height']/2})=='ok'
 async def fill(sel,v):
  l=h.page.locator(sel);await l.scroll_into_view_if_needed();ob=await h.observe();b=await l.bounding_box();cx=b['x']+b['width']/2;cy=b['y']+b['height']/2;e=min(ob['elements'],key=lambda e:(e['x']-cx)**2+(e['y']-cy)**2);assert abs(e['x']-cx)<5 and abs(e['y']-cy)<5;assert await h.act({'op':'type','n':e['n'],'text':v,'clear':True})=='ok'
 try:
  server.start(c,R,OUT/'minimal-server.log');assert server.owned;await h.start()
  for route,query in [('true','Observator'),('good','停下')]:
   await h.reset();j=Judge.load(R/c['judge_path'],'duoluoleisi',R);await fill('#searchInput',query);await click('#searchBtn');await click('.search-result-item')
   if route=='true':await fill('#observerCode','你已经够好了');await click('[onclick="checkObserver()"]')
   await j.read(h);j.update(1);assert j.ending_reached and j.score()['route_id']==route and j.score()['route_progress']==1;assert not j.side;assert not await h.page.evaluate('playerProgress.wheel');result['routes'].append({'route':route,'score':j.score(),'no_optional_collection':True});await h.page.bring_to_front();await h.observe('minimal-'+route+'.png')
  result['pass']=True
 finally:
  (OUT/'minimal-acceptance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();server.stop()
 print('MINIMAL ACADEMY PASS',flush=True)
if __name__=='__main__':asyncio.run(main())
