"""Continue two candidate investigations using browser actions, no injected state."""
import asyncio,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from harness.browser_harness import BrowserHarness
from harness.actions import normalize
BASE=ROOT/'data/discovery/english-community/canvas-probes-20261029'
JOBS=[('leaftaker-retry','https://html-classic.itch.zone/html/19515427/Leaftaker%20Web%203.03/index.html?v=1790922151',{'op':'click','x':512,'y':610}),
      ('text-imonies-deduce','https://html-classic.itch.zone/html/13542853/Textimonies-WebGL/index.html?v=1782564073',{'op':'click','x':1125,'y':115})]
async def one(label,url,action):
 out=BASE/label;out.mkdir(parents=True,exist_ok=True)
 cfg={'id':label,'obs_mode':'B','obs_text':True,'obs_elements':True,'entry_url':url,'viewport':{'width':1280,'height':900},'allow_hosts':['html-classic.itch.zone'],'actions_enabled':['click','drag','key','wait'],'settle_ms':500}
 h=BrowserHarness(cfg,out);record={'url':url,'action':action,'complete_tested':False,'reset_tested':False}
 try:
  await h.start();await h.reset();await h.page.wait_for_timeout(30000);await h.observe('before.png')
  a,err=normalize(action,cfg)
  if err:raise ValueError(err)
  record['result']=await h.act(a);await h.page.wait_for_timeout(3000);await h.observe('after.png')
  if label=='leaftaker-retry':
   await h.page.wait_for_timeout(30000);await h.observe('after-wait.png')
  record['blocked']=h.blocked
 except Exception as exc:record['error_type']=type(exc).__name__;record['error']=str(exc)[:200]
 finally:
  await h.close();(out/'probe.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8');print(label,record.get('result'),record.get('error_type'),flush=True)
async def main():
 for j in JOBS:
  if len(sys.argv)==1 or j[0]==sys.argv[1]:await one(*j)
asyncio.run(main())
