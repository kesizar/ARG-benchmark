import urllib.request,zipfile,io,json,hashlib
from pathlib import Path
root=Path('tasks/mingde-zhuilou')
sha='d37e2bc982605485645f39e7a2df6320e23d5876'
u=f'https://codeload.github.com/ternuraerrr/mingde_case_game/zip/{sha}'
b=urllib.request.urlopen(u,timeout=40).read();(root/'original/upstream.zip').write_bytes(b)
z=zipfile.ZipFile(io.BytesIO(b));files=[]
for n in z.namelist():
 if not n.endswith('/'):
  rel='/'.join(n.split('/')[1:]);data=z.read(n);p=root/'mirror'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);files.append({'path':rel,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
(root/'provenance.json').write_text(json.dumps({'record_id':'base664:0153','source':u,'revision':sha,'original_zip_sha256':hashlib.sha256(b).hexdigest(),'files':files},ensure_ascii=False,indent=2),encoding='utf-8')
print(len(files),'files',sum(x['bytes'] for x in files),'bytes')
