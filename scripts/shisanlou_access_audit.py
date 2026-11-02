"""Record recovery evidence; deliberately does not manufacture missing assets."""
from pathlib import Path
import asyncio, hashlib, json, shutil, zipfile
from datetime import datetime, timezone
from playwright.async_api import async_playwright

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'judge/shisanlou-xia/source'
ORIGIN='https://cbe13e960c974eb28565ada57114771e.app.workbuddy.link/'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,data):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
async def main():
    DEST.mkdir(parents=True,exist_ok=True)
    sources={'index.html':'ARG-packs/verify-416/bodies/554.html', 'data.js':'ARG-packs/mirrors-lite/scripts/416/554/0.js', 'game.js':'ARG-packs/mirrors-lite/scripts/416/554/1.js'}
    files=[]
    for name,rel in sources.items():
        p=ROOT/rel; shutil.copyfile(p,DEST/name)
        files.append({'source':rel,'retained_as':f'judge/shisanlou-xia/source/{name}','bytes':p.stat().st_size,'sha256':sha(p)})
    archives=[]
    for p in (ROOT/'ARG-packs').glob('*/*.zip'):
        try:
            with zipfile.ZipFile(p) as z:
                matches=[n for n in z.namelist() if any(s in n.lower() for s in ['scare-normal','scare-burned','shisanlou','shisan-lou'])]
            archives.append({'path':p.relative_to(ROOT).as_posix(),'matches':matches})
        except zipfile.BadZipFile: archives.append({'path':p.relative_to(ROOT).as_posix(),'error':'unreadable/truncated ZIP index; retained'})
    browser_probe={'url':ORIGIN,'timestamp_utc':datetime.now(timezone.utc).isoformat(),'requests_failed':[]}
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,channel="msedge")
        page=await browser.new_page()
        page.on('requestfailed',lambda r:browser_probe['requests_failed'].append({'url':r.url,'failure':r.failure}))
        try:
            response=await page.goto(ORIGIN,wait_until='domcontentloaded',timeout=25000)
            browser_probe.update(status=response.status if response else None,title=await page.title(),text=(await page.locator('body').inner_text())[:2000])
        except Exception as e: browser_probe['error']=str(e)
        await browser.close()
    write(DEST/'access-audit.json',{'record_id':'base664:0554','files':files,'archive_index_checks':archives,'browser_probe':browser_probe,'missing':['style.css','scare-normal.png','scare-burned.png'],'previous_transport_evidence':'judge/shisanlou-xia/preparation-findings.json','this_run_curl_httpx':'prepare_shisanlou_resources.py failed on TLS handshake / SSL UNEXPECTED_EOF_WHILE_READING; no assets downloaded','interpretation':'Current network failure, not proof origin is permanently down. Historical materials do not establish complete appearance or real UI deployment.'})
    print(json.dumps(browser_probe,ensure_ascii=False))
if __name__=='__main__':asyncio.run(main())
