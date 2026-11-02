import urllib.request,urllib.error,json,pathlib,hashlib,datetime
out=pathlib.Path('judge/youlun-xia/recovery');out.mkdir(parents=True,exist_ok=True)
urls={'graph':'https://api.bilibili.com/x/stein/edgeinfo_v2?bvid=BV1bJ411J7v6&graph_version=128506&edge_id=0','playurl':'https://api.bilibili.com/x/player/playurl?bvid=BV1bJ411J7v6&cid=142802415&qn=16&fnval=0','player':'https://api.bilibili.com/x/player/v2?bvid=BV1bJ411J7v6&cid=142802415','detail':'https://api.bilibili.com/x/web-interface/view/detail?bvid=BV1bJ411J7v6','page':'https://www.bilibili.com/video/BV1bJ411J7v6/','view':'https://api.bilibili.com/x/web-interface/view?bvid=BV1bJ411J7v6','pagelist':'https://api.bilibili.com/x/player/pagelist?bvid=BV1bJ411J7v6&jsonp=jsonp'}
r=[]
for k,u in urls.items():
 row={'name':k,'url':u}
 try:
  req=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.bilibili.com/','Accept-Encoding':'identity'})
  with urllib.request.urlopen(req,timeout=25) as x: b=x.read();row.update(status=x.status,headers=dict(x.headers),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
  (out/(k+'.body')).write_bytes(b)
  try: row['json']=json.loads(b)
  except: pass
 except Exception as e:
  row['error']=str(e)
  if isinstance(e,urllib.error.HTTPError):
   b=e.read(); (out/(k+'.error.body')).write_bytes(b);row.update(status=e.code,headers=dict(e.headers),bytes=len(b))
 r.append(row)
(out/'http-probe.json').write_text(json.dumps({'time':datetime.datetime.now().isoformat(),'requests':r},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps([{k:v for k,v in x.items() if k in ['name','status','bytes','error']} for x in r],ensure_ascii=True))
