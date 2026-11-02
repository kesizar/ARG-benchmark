"""Public-resource preflight; no authentication, proxy, or access-control bypass."""
import hashlib,json,re,urllib.request,urllib.error
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'judge/yucai-gaozhong/recovery'
OUT.mkdir(parents=True,exist_ok=True)
URL='https://senior-high-school.pages.dev/'
snapshot=ROOT/'ARG-packs/verify-416/bodies/408.html'
raw=snapshot.read_bytes();html=raw.decode('utf-8')
refs=sorted(set(re.findall(r'(?:src|href)=[\"\']([^\"\']+)',html)))
assets=[s for s in refs if not s.startswith(('#','http','javascript:'))]
report={'source':str(snapshot.relative_to(ROOT)),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'asset_refs':assets,'inline_script_count':len(re.findall('<script',html)),'http':[]}
for rel in ['','game.js','game.css']:
    url=URL+rel
    try:
        with urllib.request.urlopen(url,timeout=25) as r:
            b=r.read();report['http'].append({'url':url,'status':r.status,'bytes':len(b)})
            (OUT/('original-index.html' if not rel else rel)).write_bytes(b)
    except urllib.error.HTTPError as e:
        b=e.read();name='http-'+('index' if not rel else rel)+'.txt';(OUT/name).write_bytes(b)
        report['http'].append({'url':url,'status':e.code,'bytes':len(b),'body':name})
    except Exception as e:report['http'].append({'url':url,'error':str(e)})
(OUT/'preflight.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
# Exactly one fresh Edge process/context cross-check after HTTP access denial.
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True)
    context=browser.new_context();page=context.new_page();responses=[]
    page.on('response',lambda r:responses.append({'url':r.url,'status':r.status}))
    edge={'browser':browser.version,'fresh_context':True,'responses':responses}
    try:
        r=page.goto(URL,wait_until='networkidle',timeout=35000)
        edge.update({'status':r.status if r else None,'url':page.url,'title':page.title(),'body':page.locator('body').inner_text()[:8000]})
        page.screenshot(path=str(OUT/'edge.png'),full_page=True)
    except Exception as e:edge['error']=str(e)
    (OUT/'edge.json').write_text(json.dumps(edge,ensure_ascii=False,indent=2),encoding='utf-8')
    browser.close()
print(json.dumps({'http':report['http'],'edge':{k:v for k,v in edge.items() if k not in ('body','responses')}},ensure_ascii=False))
