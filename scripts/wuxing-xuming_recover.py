from pathlib import Path
import re,json,httpx,hashlib,zipfile
R=Path(__file__).resolve().parents[1];S=R/'judge/wuxing-xuming/source'; O='https://wuxing-altar.pages.dev/'
d={'requests':[],'archive_matches':[]}; seen=set();todo=['']
with httpx.Client(timeout=18,follow_redirects=True) as c:
 while todo:
  p=todo.pop(0)
  if p in seen:continue
  seen.add(p)
  try:
   q=c.get(O+p); item={'path':p or 'index.html','url':str(q.url),'status':q.status_code,'bytes':len(q.content),'sha256':hashlib.sha256(q.content).hexdigest(),'content_type':q.headers.get('content-type')};d['requests'].append(item)
   if q.status_code!=200:continue
   f=S/'recovered'/(p or 'index.html');f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(q.content)
   if 'text/html' in q.headers.get('content-type',''):
    refs=re.findall(r'''(?:src|href)=["']([^"'#]+)["']|["']([^"']+\.(?:png|jpg|jpeg|mp4|html|webp))["']''',q.text)
    for pair in refs:
     a=next((x for x in pair if x),'')
     if a and not re.match(r'(?:https?:|data:|javascript:|mailto:|/)',a) and '..' not in a:todo.append(a)
  except Exception as e:d['requests'].append({'path':p or 'index.html','error':repr(e)})
for zpath in (R/'ARG-packs').rglob('*.zip'):
 try:
  with zipfile.ZipFile(zpath) as z:
   ns=[n for n in z.namelist() if any(k in n.lower() for k in ['wuxing','续命','vhs_wide','vhs_closeup'])]
  if ns:d['archive_matches'].append({'archive':str(zpath.relative_to(R)),'names':ns})
 except Exception as e:d['archive_matches'].append({'archive':str(zpath.relative_to(R)),'error':str(e)})
(S.parent/'recovery-audit.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(d,ensure_ascii=False))
