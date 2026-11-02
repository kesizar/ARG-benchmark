"""Check a wider viewport as a per-game configuration, without altering content."""
import asyncio,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from harness.browser_harness import BrowserHarness
OUT=ROOT/'data/discovery/english-community/canvas-probes-20261029/dead-girl-wide';OUT.mkdir(parents=True,exist_ok=True)
url='https://html.itch.zone/html/13533388/index.html?v=1785092507'
cfg={'id':'dead-girl-wide','obs_mode':'B','obs_text':True,'obs_elements':True,'entry_url':url,'viewport':{'width':1920,'height':1080},'allow_hosts':['html.itch.zone'],'actions_enabled':['click','drag','key','wait'],'settle_ms':500}
async def main():
 h=BrowserHarness(cfg,OUT);record={'url':url,'viewport':cfg['viewport'],'complete_tested':False,'reset_tested':False,'interaction_tested':False}
 try:
  await h.start();await h.reset();await h.page.wait_for_timeout(45000);await h.observe('wide-entry.png')
  record['action']={'op':'click','x':1318,'y':747};record['result']=await h.act(record['action']);await h.page.wait_for_timeout(8000);await h.observe('wide-after.png');record['interaction_tested']=True;record['blocked']=h.blocked
 except Exception as exc:record['error_type']=type(exc).__name__;record['error']=str(exc)[:200]
 finally:
  await h.close();(OUT/'probe.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8');print(record.get('error_type','captured'),flush=True)
asyncio.run(main())
