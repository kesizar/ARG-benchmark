"""Diagnostic recorded before pause; run only when work is resumed."""
import asyncio,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from harness.browser_harness import BrowserHarness
async def main():
 h=BrowserHarness({'entry_url':'','settle_ms':0,'allow_hosts':[]},R/'runs/feiqi-prompt-diagnostic')
 try:
  await h.start();await h.reset();await h.page.set_content("<button onclick=\"prompt('code')\">prompt</button>");b=await h.page.locator('button').bounding_box()
  try:r=await asyncio.wait_for(h.act({'op':'click','x':b['x']+b['width']/2,'y':b['y']+b['height']/2}),5)
  except asyncio.TimeoutError:r='timeout'
  print(json.dumps({'click_result':r,'pending':bool(h.pending)}),flush=True)
  if h.pending:print(await h.act({'op':'dialog','text':'test','accept':True}),flush=True)
 finally:await h.close()
if __name__=='__main__':asyncio.run(main())
