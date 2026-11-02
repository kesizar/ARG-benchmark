"""Small, resumable real-canvas input probes; results do not assert completion."""
import asyncio, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from harness.browser_harness import BrowserHarness
from harness.actions import normalize
BASE=ROOT/'data/discovery/english-community/canvas-probes-20261029'
JOBS=[('scout-camp','https://html-classic.itch.zone/html/15866432/index.html',{'op':'click','x':625,'y':478}),
      ('hill-dale','https://html-classic.itch.zone/html/14204543/index.html',{'op':'click','x':625,'y':478}),
      ('ari','https://html-classic.itch.zone/html/11493828/index.html?v=1782619621',{'op':'key','key':'Enter'})]
async def one(label,url,action):
 out=BASE/label;out.mkdir(parents=True,exist_ok=True)
 cfg={'id':label,'obs_mode':'B','obs_text':True,'obs_elements':True,'entry_url':url,'viewport':{'width':1280,'height':900},'allow_hosts':['html-classic.itch.zone'],'actions_enabled':['click','drag','key','wait'],'settle_ms':500}
 h=BrowserHarness(cfg,out);record={'url':url,'action':action,'complete_tested':False,'reset_tested':False}
 try:
  await h.start();await h.reset();await h.page.wait_for_timeout(30000);await h.observe('before.png')
  a,err=normalize(action,cfg)
  if err:raise ValueError(err)
  record['result']=await h.act(a);await h.page.wait_for_timeout(3000);await h.observe('after.png');record['blocked']=h.blocked
  if label in ('scout-camp','hill-dale'):
   action2,err=normalize({'op':'click','x':840,'y':355},cfg)
   if err:raise ValueError(err)
   record['difficulty_result']=await h.act(action2);await h.observe('game.png')
 except Exception as exc:record['error_type']=type(exc).__name__;record['error']=str(exc)[:200]
 finally:
  await h.close();(out/'probe.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8');print(label,record.get('result'),record.get('error_type'),flush=True)
async def main():
 for j in JOBS:await one(*j)
asyncio.run(main())
