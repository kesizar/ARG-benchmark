import urllib.request,pathlib,re,json,hashlib
p=pathlib.Path('judge/guiyihui-meimei/font.css'); css=p.read_text(encoding='utf-8'); records=[]
for i,u in enumerate(sorted(set(re.findall(r'https://fonts.gstatic.com/[^)]+',css)))):
 try:
  with urllib.request.urlopen(u,timeout=60) as r: b=r.read(); status=r.status
  name=f'font-{i}.ttf'; pathlib.Path('judge/guiyihui-meimei/assets',name).write_bytes(b); css=css.replace(u,'assets/'+name); records.append({'url':u,'file':name,'status':status,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
 except Exception as e: records.append({'url':u,'error':str(e)})
p.with_name('font-local.css').write_text(css,encoding='utf-8');p.with_name('font-inventory.json').write_text(json.dumps(records,indent=2),encoding='utf-8');print(json.dumps(records,indent=2))
