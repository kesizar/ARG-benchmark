from urllib.request import urlopen
from urllib.parse import quote
from pathlib import Path
import json
out=[]
for name in ['images/刘子轩.png','images/吴敏教研.png']:
 url='https://starsemmm.github.io/beiyuarg/'+quote(name)
 try:
  r=urlopen(url,timeout=20);out.append({'url':url,'status':r.status,'bytes':len(r.read())})
 except Exception as e:out.append({'url':url,'error':str(e)})
p=Path(__file__).resolve().parents[1]/'runs/beiyu-zhaoming/live-missing-check.json';p.write_text(json.dumps(out,indent=2),encoding='utf-8');print(out)
