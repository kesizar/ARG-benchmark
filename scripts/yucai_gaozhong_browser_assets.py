import json,re,hashlib
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'tasks/yucai-gaozhong/mirror';OUT.mkdir(parents=True,exist_ok=True)
BASE='https://senior-high-school.pages.dev/'
log=[]
with sync_playwright() as p:
 b=p.chromium.launch(channel='msedge',headless=True);c=b.new_context();page=c.new_page()
 def save(r):
  if not r.url.startswith(BASE):return
  rel=r.url[len(BASE):].split('?')[0] or 'index.html'
  try:
   body=r.body();f=OUT/rel;f.parent.mkdir(parents=True,exist_ok=True)
   if r.status==200:f.write_bytes(body)
   log.append({'path':rel,'status':r.status,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()})
  except Exception as e:log.append({'path':rel,'error':str(e)})
 page.on('response',save);page.goto(BASE,wait_until='networkidle');page.wait_for_timeout(500)
 refs=set()
 for f in OUT.rglob('*'):
  if f.suffix in ('.html','.js','.css'):
   t=f.read_text(encoding='utf-8');refs.update(re.findall(r'(?:images|audio|assets)/[\w/.-]+\.(?:png|jpg|jpeg|webp|mp3|wav|svg)',t))
 for rel in sorted(refs):
  if not (OUT/rel).exists():
   page.evaluate('async rel => {await fetch(rel).then(r=>r.arrayBuffer())}',rel)
 page.wait_for_timeout(500);b.close()
(ROOT/'judge/yucai-gaozhong/recovery/browser-assets.json').write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'responses':len(log),'errors':[x for x in log if x.get('status')!=200]}))
