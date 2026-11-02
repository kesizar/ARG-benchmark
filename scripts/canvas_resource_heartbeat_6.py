"""Inspect new game screens without conflating rendering with completion."""
import asyncio,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from harness.browser_harness import BrowserHarness
BASE=ROOT/'data/discovery/english-community/canvas-probes-20261029'
JOBS=[('dead-girl-trending','https://html.itch.zone/html/13533388/index.html?v=1785092507'),
      ('the-yearbook','https://html.itch.zone/html/17375390/index.html'),
      ('murder-crandock','https://html-classic.itch.zone/html/19058064/10.58web/index.html?v=1788256827')]
async def one(label,url):
 out=BASE/label;out.mkdir(parents=True,exist_ok=True)
 cfg={'id':label,'obs_mode':'B','obs_text':True,'obs_elements':True,'entry_url':url,'viewport':{'width':1280,'height':900},'allow_hosts':[url.split('/')[2]],'actions_enabled':['click','drag','key','wait'],'settle_ms':500}
 h=BrowserHarness(cfg,out);record={'url':url,'complete_tested':False,'reset_tested':False,'interaction_tested':False}
 try:
  await h.start();await h.reset();await h.page.wait_for_timeout(45000);await h.observe('entry.png')
  if label in ('the-yearbook','murder-crandock'):
   point={'the-yearbook':(650,755),'murder-crandock':(1170,380)}[label]
   record['action']={'op':'click','x':point[0],'y':point[1]};record['result']=await h.act(record['action']);await h.page.wait_for_timeout(5000);await h.observe('after.png');record['interaction_tested']=True
  record['blocked']=h.blocked
 except Exception as exc:record['error_type']=type(exc).__name__;record['error']=str(exc)[:200]
 finally:
  await h.close();(out/'probe.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8');print(label,record.get('error_type','captured'),flush=True)
async def main():
 for j in JOBS:
  if len(sys.argv)==1 or j[0]==sys.argv[1]:await one(*j)
asyncio.run(main())
