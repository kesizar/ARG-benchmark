from pathlib import Path
import re,json,asyncio,base64,hashlib
from urllib.parse import urljoin,urlparse,unquote
from playwright.async_api import async_playwright
R=Path(__file__).resolve().parents[1];S=R/'judge/kongguan/source/current';S.mkdir(parents=True,exist_ok=True)
ROOT='https://duoweishiti.pages.dev/'
async def main():
 report=[];seen=set();hashes=set();queue=[ROOT,ROOT+'s1coffin/desktop/index-hanxiu.html']
 old=S.parent/'resource-inventory.json'
 if old.exists():
  prior=json.loads(old.read_text(encoding='utf8'));queue += [x['url'] for x in prior['files'] if x.get('status')==200 and x.get('path','').count('s1coffin')<2]+prior.get('pending',[])
 async with async_playwright() as p:
  b=await p.chromium.launch(channel='msedge',headless=True);page=await b.new_page();await page.goto(ROOT,wait_until='domcontentloaded')
  while queue and len(seen)<1200:
   batch=[u for u in queue[:12] if u not in seen];queue=queue[12:];seen.update(batch)
   for u in batch:
    try:
     d=await page.evaluate('''async u=>{const r=await fetch(u);const a=new Uint8Array(await r.arrayBuffer());let s='';for(let i=0;i<a.length;i+=32768)s+=String.fromCharCode(...a.subarray(i,i+32768));return {status:r.status,type:r.headers.get('content-type'),b64:btoa(s)}}''',u)
     raw=base64.b64decode(d.pop('b64'));rel=unquote(urlparse(u).path.lstrip('/')) or 'index.html';f=S/rel;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(raw);report.append(dict(url=u,path=rel,bytes=len(raw),**d))
     digest=hashlib.sha256(raw).hexdigest();duplicate=digest in hashes;hashes.add(digest);report[-1]['sha256']=digest;report[-1]['duplicate_body']=duplicate
     if d['status']==200 and not duplicate and (rel.endswith(('.html','.css','.js','.json'))):
      t=raw.decode('utf8','replace');refs=re.findall(r'''["'`(]([^"'`\s<>()[\]{}]+\.(?:html|js|css|json|png|jpe?g|webp|gif|svg|ico|mp3|wav|ogg|mp4|pdf|woff2?)(?:\?[^"'`\s<>)]*)?)["'`)]''',t,re.I)
      for ref in refs:
       bases=[u]
       if rel.endswith('.js') and '/js/' in u:bases.append(u.split('/js/')[0]+'/')
       if rel.endswith('.js') and '/data/' in u:bases.append(u.split('/data/')[0]+'/')
       for base in bases:
        v=urljoin(base,ref).split('#')[0]
        if urlparse(v).netloc==urlparse(ROOT).netloc and v not in seen and v not in queue:queue.append(v)
    except Exception as e:report.append({'url':u,'error':str(e)})
   (S.parent/'resource-inventory.json').write_text(json.dumps({'files':report,'pending':queue},ensure_ascii=False,indent=2),encoding='utf8');print('captured',len(report),'pending',len(queue),flush=True)
  await b.close()
if __name__=='__main__':asyncio.run(main())
