"""Check wrong-answer feedback and fresh-context reset through visible UI."""
import asyncio,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from harness.browser_harness import BrowserHarness
from harness.actions import normalize
OUT=ROOT/'data/discovery/english-community/canvas-probes-20261029/text-imonies-errors';OUT.mkdir(parents=True,exist_ok=True)
url='https://html-classic.itch.zone/html/13542853/Textimonies-WebGL/index.html?v=1782564073'
cfg={'id':'textimonies','obs_mode':'B','obs_text':True,'obs_elements':True,'entry_url':url,'viewport':{'width':1280,'height':900},'allow_hosts':['html-classic.itch.zone'],'actions_enabled':['click','wait'],'settle_ms':500}
async def main():
 h=BrowserHarness(cfg,OUT);results=[]
 async def click(x,y):
  a,err=normalize({'op':'click','x':x,'y':y},cfg)
  if err:raise ValueError(err)
  results.append({'action':a,'result':await h.act(a)})
 try:
  await h.start();await h.reset();await h.page.wait_for_timeout(30000)
  await click(1125,115);await h.observe('deduce-before.png')
  await click(635,710);await h.observe('deduce-after.png')
  await h.reset();await h.page.wait_for_timeout(30000);await click(1125,115);await h.observe('fresh-deduce.png')
  (OUT/'probe.json').write_text(json.dumps({'actions':results,'blocked':h.blocked,'complete_tested':False},ensure_ascii=False,indent=2),encoding='utf8')
 finally:await h.close()
asyncio.run(main())
