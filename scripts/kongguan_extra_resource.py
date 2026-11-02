from pathlib import Path
import asyncio,json,base64,hashlib
from playwright.async_api import async_playwright
R=Path(__file__).resolve().parents[1];S=R/'judge/kongguan/source'
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(channel='msedge',headless=True);page=await b.new_page();await page.goto('https://duoweishiti.pages.dev/');u='https://duoweishiti.pages.dev/music/end01.mp3';d=await page.evaluate('''async u=>{const r=await fetch(u);const a=new Uint8Array(await r.arrayBuffer());let s='';for(let i=0;i<a.length;i+=32768)s+=String.fromCharCode(...a.subarray(i,i+32768));return {status:r.status,type:r.headers.get('content-type'),b64:btoa(s)}}''',u);raw=base64.b64decode(d.pop('b64'));assert d['status']==200 and 'audio' in d['type'];(S/'current/music/end01.mp3').write_bytes(raw);inv=json.loads((S/'resource-inventory.json').read_text(encoding='utf8'));inv['files'].append(dict(url=u,path='music/end01.mp3',bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),dynamic_reference_evidence='e3funeral.html MusicManager.start(end01) + load(name)',**d));(S/'resource-inventory.json').write_text(json.dumps(inv,ensure_ascii=False,indent=2),encoding='utf8');await b.close();print('captured dynamic funeral audio',len(raw))
if __name__=='__main__':asyncio.run(main())
