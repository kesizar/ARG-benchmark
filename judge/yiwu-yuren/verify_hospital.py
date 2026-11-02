from pathlib import Path
import asyncio,json,sys,argparse
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from harness.config import load_config
from harness.browser_harness import BrowserHarness
from harness.serve_local import LocalServer
from harness.judge import Judge
async def main():
 O=R/'judge/yiwu-yuren/verification';c=load_config(R/'configs/yiwu-yuren.json');h=BrowserHarness(c,O);sv=LocalServer();rep={'errors':[],'checks':[]}
 async def ck(sel):
  loc=h.page.locator(sel).first;await loc.scroll_into_view_if_needed();b=await loc.bounding_box();assert await h.act({'op':'click','x':b['x']+b['width']/2,'y':b['y']+b['height']/2})=='ok';await asyncio.sleep(.5)
 try:
  sv.start(c,R,O/'hospital-server.log');assert sv.owned;await h.start();await h.reset();h.context.on('page',lambda pg:pg.on('pageerror',lambda e:rep['errors'].append(e.stack)))
  await h.page.locator('#searchInput').fill('青岚第二医院');await ck('.suggestion-item');await ck('#gotoQueryBtn');await ck('#searchRecordBtn');assert '完整填写' in await h.page.locator('#searchFeedback').inner_text();rep['checks'].append('empty rejected visibly')
  for sel,val in [('#patientName','沈沁'),('#birthDate','2001-10-05'),('#admitDate','2025-03-02')]:await h.page.locator(sel).fill(val)
  await ck('#searchRecordBtn');assert '住院日期错误' in await h.page.locator('#searchFeedback').inner_text();rep['checks'].append('wrong date rejected visibly');await h.page.screenshot(path=str(O/'hospital-negative-fixed.png'),full_page=True)
  j=Judge.load(R/c['judge_path'],'yiwu-yuren',R);await j.read(h);j.update(1);assert not j.checkpoints and not j.ending_reached
  await h.page.locator('#admitDate').fill('2025-03-01');await ck('#searchRecordBtn');assert h.page.url.endswith('yiyuanjilu.html');rep['checks'].append('correct match loads record');await h.page.screenshot(path=str(O/'hospital-positive-fixed.png'),full_page=True);assert not rep['errors'];rep['pass']=True
 finally:
  (O/'hospital-compatibility-retest.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();sv.stop()
asyncio.run(main())
