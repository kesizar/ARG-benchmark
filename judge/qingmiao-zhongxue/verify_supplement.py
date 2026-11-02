import asyncio,json,subprocess,sys,hashlib,re,urllib.parse,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R));from harness.browser_harness import BrowserHarness
T='qingmiao-zhongxue';E=R/'judge'/T/'verification'
async def main():
 cfg=json.loads((R/'configs'/f'{T}.json').read_text(encoding='utf8'));cfg['entry_url']=cfg['entry_url'].replace('8811','8813');cfg['allow_hosts']=['127.0.0.1:8813'];h=BrowserHarness(cfg,E);failed=[];requests=[];documents=[]
 log=(E/'supplement-server.log').open('w');proc=subprocess.Popen([sys.executable,str(R/'scripts/serve_static.py'),'--root',str(R/'tasks'/T/'mirror'),'--port','8813'],stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 try:
  await asyncio.sleep(1);await h.start();await h.reset();h.context.on('request',lambda r:requests.append(r.url));h.context.on('requestfailed',lambda r:failed.append({'url':r.url,'failure':r.failure}));h.page.on('dialog',lambda d:asyncio.create_task(d.accept()))
  for site in ['Hospital-Ingenium','Lin-You-s-Blog']:
   await h.page.goto(f'http://127.0.0.1:8813/qingmiaomiddleschool.github.io/{site}/');await h.page.wait_for_timeout(500)
   if site=='Hospital-Ingenium':
    search=await h.page.evaluate('searchData');documents.append({'site':site,'searchData':search})
    for item in search:
     await h.page.locator('#searchInput').fill(item['keywords'][0]);await h.page.locator('#searchButton').click()
     loc=h.page.locator(f'.keyword-link[data-target="{item["target"]}"]')
     if await loc.is_visible():await loc.click()
     page=h.page.locator('#'+item['target']);assert await page.is_visible();documents.append({'target':item['target'],'visible_text':await page.inner_text()})
     image=page.locator('.article-image')
     if await image.count():await image.first.click();await h.page.locator('body > div').last.click(position={'x':1,'y':1})
     await h.page.locator('.back-to-home:visible').first.click()
    await h.page.locator('#searchInput').fill('NO-SUCH-RECORD');await h.page.locator('#searchButton').click();assert '没有查找到' in await h.page.locator('#searchResultsContent').inner_text()
   else:
    documents.append({'site':site,'visible_text':await h.page.locator('body').inner_text()});await h.page.locator('.album-item').first.click();await h.page.keyboard.press('ArrowRight');await h.page.keyboard.press('Escape')
   await h.page.screenshot(path=str(E/(site+'-visible.png')))
   images=await h.page.locator('img').evaluate_all('(xs)=>xs.map(x=>({src:x.src,ok:x.complete&&x.naturalWidth>0}))');documents.append({'site':site,'images':images});assert all(i['ok'] for i in images),images
  out={'pass':True,'requests':requests,'failed_requests':failed,'documents':documents,'scope':'UI search and visible article/album exploration; source read used only to enumerate search keys.'}
 except Exception as e:out={'pass':False,'error':repr(e),'traceback':traceback.format_exc(),'requests':requests,'failed_requests':failed,'documents':documents}
 finally:await h.close();proc.terminate();proc.wait();log.close()
 (E/'supplement-ui.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in out.items() if k not in ['documents','requests']},ensure_ascii=False))
asyncio.run(main())
