"""UI-only original probe for concurrent crossword turns; private state read as evidence."""
import argparse,asyncio,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from harness.browser_harness import BrowserHarness
from harness.config import load_config
from harness.serve_local import LocalServer
async def main():
 cfg=load_config(ROOT/'configs/qian-anon-cross.json');cfg['settle_ms']=10;out=ROOT/'judge/qian-anon/verification';out.mkdir(parents=True,exist_ok=True);h=BrowserHarness(cfg,out);server=LocalServer();r={}
 async def click(selector):
  loc=h.page.locator(selector).first;await loc.scroll_into_view_if_needed();b=await loc.bounding_box();assert await h.act({'op':'click','x':b['x']+b['width']/2,'y':b['y']+b['height']/2})=='ok'
 try:
  server.start(cfg,ROOT,out/'probe-server.log');await h.start();await h.reset();await click('button.card[onclick*="show(\'cross\')"]');await click('[onclick="crossStumble(true)"]');first=await h.page.evaluate('({a:CX.aPos,s:CX.sPos,turn:CX.turn})');await click('[onclick="crossStumble(true)"]');second=await h.page.evaluate('({a:CX.aPos,s:CX.sPos,turn:CX.turn})');r.update(first=first,second=second,concurrent_player_advance=second['a']==first['a']+1 and second['s']==first['s']);assert r['concurrent_player_advance'];await h.act({'op':'wait','ms':850});r['after_queued_foes']=await h.page.evaluate('({a:CX.aPos,s:CX.sPos,turn:CX.turn})');r['pass']=True
 finally:
  (out/'original-cross-probe.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();server.stop()
if __name__=='__main__':asyncio.run(main())
