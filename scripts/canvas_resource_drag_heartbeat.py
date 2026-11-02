"""Validate interaction and fresh-context reset on two original canvas games."""
import asyncio, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from harness.browser_harness import BrowserHarness
from harness.actions import normalize
BASE=ROOT/'data/discovery/english-community/canvas-probes-20261029'
JOBS=[('scout-camp','https://html-classic.itch.zone/html/15866432/index.html',{'op':'click','x':410,'y':125}),
      ('hill-dale','https://html-classic.itch.zone/html/14204543/index.html',{'op':'click','x':520,'y':770})]
async def one(label,url,show):
 out=BASE/label
 cfg={'id':label,'obs_mode':'B','obs_text':True,'obs_elements':True,'entry_url':url,'viewport':{'width':1280,'height':900},'allow_hosts':['html-classic.itch.zone'],'actions_enabled':['click','drag','key','wait'],'settle_ms':500}
 h=BrowserHarness(cfg,out);record={'url':url,'complete_tested':False}
 async def act(a):
  normalized,err=normalize(a,cfg)
  if err:raise ValueError(err)
  return await h.act(normalized)
 try:
  await h.start();await h.reset();await h.page.wait_for_timeout(30000)
  await act({'op':'click','x':625,'y':478});await act({'op':'click','x':840,'y':355})
  record['show_result']=await act(show);await h.observe('labels.png')
  drag=({'op':'drag','x1':90,'y1':278,'x2':380,'y2':334} if label=='scout-camp'
        else {'op':'drag','x1':65,'y1':311,'x2':450,'y2':200})
  record['drag']=drag;record['drag_result']=await act(drag);await h.observe('drag.png')
  await h.reset();await h.page.wait_for_timeout(30000);await h.observe('fresh-reset.png')
  record['reset_result']='fresh_context_captured';record['blocked']=h.blocked
 except Exception as exc:record['error_type']=type(exc).__name__;record['error']=str(exc)[:200]
 finally:
  await h.close();(out/'heartbeat-probe.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8');print(label,record.get('reset_result'),record.get('error_type'),flush=True)
async def main():
 for j in JOBS:await one(*j)
asyncio.run(main())
