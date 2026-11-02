"""Public original-entry access audit. No alternate host or access bypass."""
from pathlib import Path
import json,hashlib,urllib.request,urllib.error,re,shutil
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1]; O=R/'runs/guangying-she'; T=R/'tasks/guangying-she'; J=R/'judge/guangying-she'
U='https://01a07249-04b2-78c6-a3d9-afac55849ee5.arena.site/'
def save(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
def main():
 O.mkdir(parents=True,exist_ok=True);T.mkdir(parents=True,exist_ok=True);J.mkdir(parents=True,exist_ok=True)
 source=R/'ARG-packs/verify-416/bodies/425.html';shutil.copyfile(source,T/'historical-wrapper.html');raw=source.read_bytes();s=raw.decode('utf8')
 report={'record_id':'base664:0425','task_id':'guangying-she','entry':U,'historical':{'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'iframe_src':re.findall(r'<iframe[\s\S]*?src="([^"]+)"',s),'script_src':re.findall(r'<script[^>]*src="([^"]+)"',s)},'http':[]}
 for rel,label in [('', 'root'),('?embed=true','embed')]:
  try:
   with urllib.request.urlopen(U+rel,timeout=25) as resp:b=resp.read();status=resp.status
  except urllib.error.HTTPError as e:b=e.read();status=e.code
  except Exception as e:report['http'].append({'url':U+rel,'error':repr(e)});continue
  (O/f'http-{label}.html').write_bytes(b);report['http'].append({'url':U+rel,'status':status,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
 save(O/'access-audit.json',report)
 with sync_playwright() as pw:
  b=pw.chromium.launch(channel='msedge',headless=True);c=b.new_context();p=c.new_page();edge={'fresh_process':True,'fresh_context':True,'version':b.version,'responses':[]}
  p.on('response',lambda r:edge['responses'].append({'url':r.url,'status':r.status}))
  try:
   resp=p.goto(U,wait_until='domcontentloaded',timeout=30000);p.wait_for_timeout(1000);edge.update({'status':resp.status if resp else None,'final_url':p.url,'title':p.title(),'body':p.locator('body').inner_text(),'frames':[{'url':f.url,'body':f.locator('body').inner_text()[:4000]} for f in p.frames]});p.screenshot(path=str(O/'fresh-edge.png'),full_page=True);(O/'fresh-edge.html').write_text(p.content(),encoding='utf8')
  except Exception as e:edge['error']=str(e)
  save(O/'fresh-edge.json',edge);b.close()
 print(json.dumps({'http':report['http'],'edge':{k:v for k,v in edge.items() if k not in ('responses','frames')}},ensure_ascii=True))
if __name__=='__main__':main()
