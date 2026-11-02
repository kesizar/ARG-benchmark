import asyncio,json,subprocess,sys
from pathlib import Path
from playwright.async_api import async_playwright
R=Path(__file__).resolve().parents[1]
async def main():
 port=int(sys.argv[1]);root=Path(sys.argv[2]);out=Path(sys.argv[3]);out.mkdir(parents=True,exist_ok=True)
 server=subprocess.Popen([sys.executable,str(R/'scripts/serve_static.py'),'--root',str(root),'--port',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 report={'scope':'resource blocker smoke only; not full gameplay acceptance','port':port,'root':str(root),'pages':[],'http_errors':[],'external_blocked':[]}
 try:
  await asyncio.sleep(1)
  async with async_playwright() as pw:
   b=await pw.chromium.launch(channel='msedge',headless=True);c=await b.new_context(viewport={'width':1366,'height':900});p=await c.new_page();base=f'http://127.0.0.1:{port}/'
   async def route(r):
    if r.request.url.startswith(base):await r.continue_()
    else:report['external_blocked'].append(r.request.url);await r.abort()
   await c.route('**/*',route);p.on('response',lambda r:report['http_errors'].append({'url':r.url,'status':r.status}) if r.status>=400 else None)
   for n in ['index.html','toshi7.html','weixian.html','ending1.html','endingzz.html']:
    await p.goto(base+n);await p.wait_for_timeout(300)
    row={'page':n,'title':await p.title(),'images':await p.locator('img').evaluate_all('(els)=>els.map(e=>({src:e.getAttribute("src"),alt:e.alt,complete:e.complete,width:e.naturalWidth}))')}
    if n in ['toshi7.html','weixian.html']:
     await p.locator('.puzzle-piece-container').scroll_into_view_if_needed();await p.screenshot(path=str(out/(n+'.png')))
    report['pages'].append(row)
   # Verify recovered endings through original page buttons; no state injection.
   await p.goto(base+'xihe.html');await p.locator('.outcome-button').click();await p.wait_for_url('**/ending1.html');report['ending1_ui_link']=True
   await p.goto(base+'chuiji.html');await p.locator('.ending-button').click();await p.wait_for_url('**/endingzz.html');report['endingzz_ui_link']=True
   await b.close()
  report['passed']=True
 finally:
  server.terminate();server.wait(timeout=10);(out/'smoke.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'passed':report.get('passed'),'http_errors':report['http_errors']},ensure_ascii=True))
asyncio.run(main())
