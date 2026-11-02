from pathlib import Path
import urllib.request,re,json
R=Path(__file__).resolve().parents[1];D=R/'judge/yiwu-yuren/source/vendor';D.mkdir(exist_ok=True)
u='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css'
with urllib.request.urlopen(u,timeout=25) as r:b=r.read()
(D/'all.min.css').write_bytes(b)
log=[]
for f in sorted(set(re.findall(r'\.\./webfonts/([^\)]+)',b.decode()))):
 with urllib.request.urlopen('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/webfonts/'+f,timeout=25) as r:q=r.read()
 (D/f).write_bytes(q);log.append([f,len(q)])
print(log)
