from pathlib import Path
import json,re,os
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];O=R/'runs/guangying-she';T=R/'tasks/guangying-she';U='https://01a07249-04b2-78c6-a3d9-afac55849ee5.arena.site/?embed=true'
with sync_playwright() as pw:
 b=pw.chromium.launch(channel='msedge',headless=True);c=b.new_context();p=c.new_page();docs=[]
 def capture(r):
  if r.request.resource_type=='document':
   try:
    raw=r.body();name=f'document-{len(docs)}.html';(T/name).write_bytes(raw);docs.append({'url':r.url,'status':r.status,'bytes':len(raw),'file':name})
   except Exception as e:docs.append({'url':r.url,'error':str(e)})
 p.on('response',capture);r=p.goto(U,wait_until='domcontentloaded',timeout=30000);p.wait_for_timeout(2000)
 raw=r.body();(T/'original-game.html').write_bytes(raw);(O/'game-dom.html').write_text(p.content(),encoding='utf8');(O/'game-text.txt').write_text(p.locator('body').inner_text(),encoding='utf8')
 for i,f in enumerate(p.frames):(T/f'frame-{i}.html').write_text(f.content(),encoding='utf8')
 (O/'documents.json').write_text(json.dumps(docs,indent=2),encoding='utf8')
 print(json.dumps({'documents':docs,'frames':len(p.frames)},ensure_ascii=True),flush=True)
 os._exit(0)
