from pathlib import Path
import urllib.request,json,hashlib,zipfile,io
r=Path(__file__).resolve().parents[1]; p=r/'tasks/tade-xinhao'; src=p/'source'
u='https://api.github.com/repos/emith233/her-signal/git/trees/main?recursive=1'
d=json.load(urllib.request.urlopen(u,timeout=30));(src/'remote-tree.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
files=[x for x in d['tree'] if x['type']=='blob'];print('files',len(files),'bytes',sum(x.get('size',0) for x in files),'commit',d['sha'],flush=True)
a=urllib.request.urlopen('https://codeload.github.com/emith233/her-signal/zip/'+d['sha'],timeout=90).read();(src/'upstream.zip').write_bytes(a)
z=zipfile.ZipFile(io.BytesIO(a));prefix=z.namelist()[0]
for n in z.namelist():
 rel=n[len(prefix):]
 if not rel or n.endswith('/'):continue
 f=p/'mirror'/rel;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(z.read(n))
print('downloaded',len(a),'extracted',len(files),flush=True)
