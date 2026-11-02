"""Recoverability audit only: cached HTML is cut inside the bundled Three.js."""
from pathlib import Path
import asyncio,hashlib,json,shutil,zipfile
from datetime import datetime,timezone
import httpx
from playwright.async_api import async_playwright
R=Path(__file__).resolve().parents[1];J=R/'judge/shouren-shengcun';S=J/'source';ORIGIN='https://a361d78ee30e54fbe.app.workbuddy.host/'
async def main():
 S.mkdir(parents=True,exist_ok=True);p=R/'ARG-packs/verify-84/bodies/58.html';b=p.read_bytes();shutil.copyfile(p,S/'original-truncated.html')
 d={'record_id':'added84:0058','timestamp_utc':datetime.now(timezone.utc).isoformat(),'snapshot':{'path':p.relative_to(R).as_posix(),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'script_open':b.count(b'<script'),'script_close':b.count(b'</script>'),'has_html_close':b'</html>' in b,'tail':b[-250:].decode('utf-8','replace'),'interpretation':'Cut mid bundled Three.js, before closing script and actual game logic. Not a runnable snapshot.'},'curl_checks':[{'url':ORIGIN,'error':'schannel TLS handshake failed'},{'url':'https://miyeji.cn/games/da-chu-wang','error':'schannel TLS handshake failed'}],'httpx_checks':[],'archive_indexes':[]}
 for url in [ORIGIN,'https://miyeji.cn/games/da-chu-wang']:
  try:
   async with httpx.AsyncClient(timeout=15,follow_redirects=True) as c:
    q=await c.get(url);d['httpx_checks'].append({'url':url,'status':q.status_code,'bytes':len(q.content)});
    if q.status_code==200:(S/('httpx-live.html' if url==ORIGIN else 'httpx-miyeji.html')).write_bytes(q.content)
  except Exception as e:d['httpx_checks'].append({'url':url,'error':repr(e)})
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True,channel='msedge');page=await browser.new_page();d['browser_probe']={'url':ORIGIN,'request_failures':[]};page.on('requestfailed',lambda q:d['browser_probe']['request_failures'].append({'url':q.url,'error':q.failure}))
  try:
   q=await page.goto(ORIGIN,wait_until='domcontentloaded',timeout=25000);d['browser_probe'].update(status=q.status if q else None,title=await page.title());(S/'browser-live.html').write_text(await page.content(),encoding='utf-8')
  except Exception as e:d['browser_probe']['error']=str(e)
  await browser.close()
 for p in (R/'ARG-packs').glob('*/*.zip'):
  try:
   with zipfile.ZipFile(p) as z:names=[n for n in z.namelist() if any(k in n.lower() for k in ['a361d78','shouren','兽人','da-chu-wang'])]
   d['archive_indexes'].append({'path':p.relative_to(R).as_posix(),'matches':names})
  except zipfile.BadZipFile:d['archive_indexes'].append({'path':p.relative_to(R).as_posix(),'error':'truncated/unreadable ZIP index retained'})
 (J/'access-audit.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'snapshot':d['snapshot'],'httpx':d['httpx_checks'],'browser':d['browser_probe']},ensure_ascii=False))
if __name__=='__main__':asyncio.run(main())
