"""Inspect visible controls and player actions in the original NOCTUA entry."""
import asyncio,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from harness.browser_harness import BrowserHarness
OUT=ROOT/'data/discovery/english-community/canvas-probes-20261029/noctua-entry';OUT.mkdir(parents=True,exist_ok=True)
url='https://html-classic.itch.zone/html/19616989/index.html?v=1791378830'
cfg={'id':'noctua','obs_mode':'B','obs_text':True,'obs_elements':True,'entry_url':url,'viewport':{'width':1280,'height':900},'allow_hosts':['html-classic.itch.zone'],'actions_enabled':['click','drag','key','wait','hover'],'settle_ms':500}
async def main():
 h=BrowserHarness(cfg,OUT);record={'url':url,'complete_tested':False}
 try:
  await h.start();await h.reset();await h.page.wait_for_timeout(5000);obs=await h.observe('entry.png')
  record['visible_text']=obs.get('visible_text','');record['elements']=obs.get('elements',[])
  for e in obs.get('elements',[]):
   if 'NEW GAME' in str(e).upper():
    record['action']={'op':'click','n':e['n']};record['result']=await h.act(record['action']);await h.observe('after.png');break
  if 'action' not in record:
   record['action']={'op':'click','x':650,'y':512};record['result']=await h.act(record['action']);await h.page.wait_for_timeout(3000);await h.observe('after.png')
  record['monitor_action']={'op':'click','x':625,'y':450};record['monitor_result']=await h.act(record['monitor_action']);await h.page.wait_for_timeout(3000);await h.observe('monitor.png')
  record['blocked']=h.blocked
 except Exception as exc:record['error_type']=type(exc).__name__;record['error']=str(exc)[:200]
 finally:
  await h.close();(OUT/'probe.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8');print('done',record.get('result'),record.get('error_type'),flush=True)
asyncio.run(main())
