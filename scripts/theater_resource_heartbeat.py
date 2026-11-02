"""Explore visible player controls in Deductopia Theater and a fresh context."""
import asyncio,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from harness.browser_harness import BrowserHarness
OUT=ROOT/'data/discovery/english-community/canvas-probes-20261029/theater-interaction';OUT.mkdir(parents=True,exist_ok=True)
url='https://html-classic.itch.zone/html/18072902/index.html'
cfg={'id':'theater','obs_mode':'B','obs_text':True,'obs_elements':True,'entry_url':url,'viewport':{'width':1280,'height':900},'allow_hosts':['html-classic.itch.zone'],'actions_enabled':['click','drag','key','wait'],'settle_ms':500}
async def main():
 h=BrowserHarness(cfg,OUT);actions=[]
 async def act(a):actions.append({'action':a,'result':await h.act(a)})
 try:
  await h.start();await h.reset();await h.page.wait_for_timeout(30000);await h.observe('entry.png')
  await act({'op':'click','x':1140,'y':735});await h.observe('panel.png')
  await act({'op':'drag','x1':90,'y1':377,'x2':370,'y2':154});await h.observe('drag.png')
  await h.reset();await h.page.wait_for_timeout(30000);await h.observe('fresh-context.png')
  (OUT/'probe.json').write_text(json.dumps({'actions':actions,'blocked':h.blocked,'complete_tested':False},ensure_ascii=False,indent=2),encoding='utf8')
 finally:await h.close()
asyncio.run(main())
