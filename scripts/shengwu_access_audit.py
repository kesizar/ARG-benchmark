"""Audit original public game access without presenting a partial page as ready."""
from pathlib import Path
import asyncio, hashlib, json, re, shutil, zipfile
from datetime import datetime, timezone
import httpx
from playwright.async_api import async_playwright

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'judge/shengwu/source'
ORIGIN='https://z6gdps8gwz.page.coze.site/'

def write(p,data):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

async def main():
    DEST.mkdir(parents=True,exist_ok=True)
    source=ROOT/'ARG-packs/verify-416/bodies/28.html'
    shutil.copyfile(source,DEST/'original-index.html')
    raw=source.read_text(encoding='utf-8')
    refs=sorted(set(re.findall(r'[\"\x27]([^\"\x27<>\s]+\.(?:html|mp3|js|css|png|jpg))[\"\x27]',raw)))
    audit={'record_id':'base664:0028','task_id':'shengwu','timestamp_utc':datetime.now(timezone.utc).isoformat(),'snapshot':{'path':str(source.relative_to(ROOT)),'bytes':source.stat().st_size,'sha256':hashlib.sha256(source.read_bytes()).hexdigest()},'referenced_resources':refs,'http':[],'browser':[],'archive_matches':[]}
    for p in (ROOT/'ARG-packs').glob('*/*.zip'):
        try:
            with zipfile.ZipFile(p) as z:
                matches=[n for n in z.namelist() if any(v in n.lower() for v in ['shengwu','meng-letter.html','ch6-room.html','theme-song.mp3'])]
            if matches:audit['archive_matches'].append({'path':p.relative_to(ROOT).as_posix(),'matches':matches})
        except zipfile.BadZipFile:audit['archive_matches'].append({'path':p.relative_to(ROOT).as_posix(),'error':'BadZipFile'})
    write(DEST/'access-audit.json',audit)
    async with httpx.AsyncClient(timeout=25,follow_redirects=True) as client:
        for rel in ['', 'arc.html']:
            rec={'url':ORIGIN+rel}
            try:
                r=await client.get(rec['url']);rec.update(status=r.status_code,bytes=len(r.content),content_type=r.headers.get('content-type'))
                if r.status_code==200:(DEST/('live-'+(rel or 'index.html'))).write_bytes(r.content)
            except Exception as e:rec['error']=repr(e)
            audit['http'].append(rec);write(DEST/'access-audit.json',audit)
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,channel='msedge')
        for rel in ['', 'arc.html']:
            context=await browser.new_context();page=await context.new_page();rec={'url':ORIGIN+rel,'failures':[]}
            page.on('requestfailed',lambda r,rec=rec:rec['failures'].append({'url':r.url,'failure':r.failure}))
            try:
                response=await page.goto(rec['url'],wait_until='domcontentloaded',timeout=25000)
                rec.update(status=response.status if response else None,title=await page.title(),text=(await page.locator('body').inner_text())[:1500])
                await page.screenshot(path=str(DEST/('live-'+('arc' if rel else 'index')+'.png')))
            except Exception as e:rec['error']=str(e)
            audit['browser'].append(rec);write(DEST/'access-audit.json',audit);await context.close()
        await browser.close()
    print(json.dumps({'http':audit['http'],'browser':audit['browser'],'archive_matches':audit['archive_matches']},ensure_ascii=False))

if __name__=='__main__':asyncio.run(main())
