"""Capture three previously unverified direct game entry states."""
import asyncio,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from harness.browser_harness import BrowserHarness
BASE=ROOT/'data/discovery/english-community/canvas-probes-20261029'
JOBS=[('bold-scheme','https://html.itch.zone/html/15695550/heister/index.html?v=1785115138'),
      ('deductopia-theater','https://html-classic.itch.zone/html/18072902/index.html'),
      ('mail-watcher','https://html-classic.itch.zone/html/12494552/index.html?v=1782553400')]
async def one(label,url):
 out=BASE/label;out.mkdir(parents=True,exist_ok=True)
 host=url.split('/')[2]
 cfg={'id':label,'obs_mode':'B','obs_text':True,'obs_elements':True,'entry_url':url,'viewport':{'width':1280,'height':900},'allow_hosts':[host],'actions_enabled':['click','drag','key','wait'],'settle_ms':500}
 h=BrowserHarness(cfg,out);record={'url':url,'complete_tested':False,'reset_tested':False,'interaction_tested':False}
 try:
  await h.start();await h.reset();await h.page.wait_for_timeout(45000);await h.observe('entry.png')
  point={'bold-scheme':(210,365),'deductopia-theater':(1200,738),'mail-watcher':(360,425)}[label]
  record['action']={'op':'click','x':point[0],'y':point[1]};record['result']=await h.act(record['action'])
  await h.page.wait_for_timeout(3000);await h.observe('after.png')
  if label in ('bold-scheme','mail-watcher'):
   second={'bold-scheme':(1100,670),'mail-watcher':(640,440)}[label]
   record['second_action']={'op':'click','x':second[0],'y':second[1]}
   record['second_result']=await h.act(record['second_action']);await h.page.wait_for_timeout(2000);await h.observe('after-second.png')
  if label=='bold-scheme':
   record['third_action']={'op':'click','x':190,'y':550};record['third_result']=await h.act(record['third_action']);await h.observe('after-third.png')
   record['fourth_action']={'op':'click','x':240,'y':300};record['fourth_result']=await h.act(record['fourth_action']);await h.observe('after-fourth.png')
  if label=='mail-watcher':
   await h.page.wait_for_timeout(6000);record['third_action']={'op':'click','x':640,'y':440};record['third_result']=await h.act(record['third_action']);await h.page.wait_for_timeout(4000);await h.observe('after-third.png')
   record['fourth_action']={'op':'click','x':870,'y':650};record['fourth_result']=await h.act(record['fourth_action']);await h.observe('after-fourth.png')
  record['blocked']=h.blocked
 except Exception as exc:record['error_type']=type(exc).__name__;record['error']=str(exc)[:200]
 finally:
  await h.close();(out/'probe.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8');print(label,record.get('error_type','captured'),flush=True)
async def main():
 for j in JOBS:
  if len(sys.argv)==1 or j[0]==sys.argv[1]:await one(*j)
asyncio.run(main())
