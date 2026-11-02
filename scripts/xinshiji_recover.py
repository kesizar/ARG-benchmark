import urllib.request,json,pathlib,hashlib
root=pathlib.Path('tasks/xinshiji/original');audit=pathlib.Path('judge/xinshiji/recovery');rows=[]
for path in ['', 'main.html','wangzhan/shizong.jpg','wangzhan/chuandan.jpg']:
 url='https://xinshijileyuan.pages.dev/'+path
 try:
  with urllib.request.urlopen(url,timeout=25) as r:b=r.read();status=r.status
  out=root/(path or 'index.html');out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(b)
  row={'url':url,'status':status,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'path':str(out)}
 except Exception as e:row={'url':url,'error':str(e)}
 rows.append(row)
(audit/'network-probe.json').write_text(json.dumps(rows,indent=2),encoding='utf8');print(json.dumps(rows,indent=2))
