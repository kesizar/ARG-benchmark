"""Probe separate canvas candidates through player-visible input only."""
import asyncio,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from harness.browser_harness import BrowserHarness
from harness.actions import normalize
BASE=ROOT/'data/discovery/english-community/canvas-probes-20261029'
JOBS=[('ari-click','https://html-classic.itch.zone/html/11493828/index.html?v=1782619621',{'op':'click','x':600,'y':500}),
      ('quid-pro-quo','https://html-classic.itch.zone/html/15856730/index.html',{'op':'click','x':640,'y':450}),
      ('adlerstream','https://html-classic.itch.zone/html/14250913/index.html',{'op':'click','x':530,'y':275})]
async def one(label,url,action):
 out=BASE/label;out.mkdir(parents=True,exist_ok=True)
 cfg={'id':label,'obs_mode':'B','obs_text':True,'obs_elements':True,'entry_url':url,'viewport':{'width':1280,'height':900},'allow_hosts':['html-classic.itch.zone'],'actions_enabled':['click','drag','key','wait'],'settle_ms':500}
 h=BrowserHarness(cfg,out);record={'url':url,'action':action,'complete_tested':False,'reset_tested':False}
 try:
  await h.start();await h.reset();await h.page.wait_for_timeout(30000);await h.observe('before.png')
  a,err=normalize(action,cfg)
  if err:raise ValueError(err)
  record['result']=await h.act(a);await h.page.wait_for_timeout(2000);await h.observe('after.png');record['blocked']=h.blocked
 except Exception as exc:record['error_type']=type(exc).__name__;record['error']=str(exc)[:200]
 finally:
  await h.close();(out/'probe.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8');print(label,record.get('result'),record.get('error_type'),flush=True)
async def main():
 for j in JOBS:await one(*j)
asyncio.run(main())
