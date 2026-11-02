import json,pathlib,urllib.request,hashlib,concurrent.futures
r=pathlib.Path('judge/youlun-xia/recovery');out=pathlib.Path('tasks/youlun-xia/media');out.mkdir(parents=True,exist_ok=True)
inv=json.loads((r/'graph-inventory.json').read_text(encoding='utf-8'));log=[]
def download(cid):
 row={'cid':cid};f=out/(str(cid)+'.mp4')
 try:
  if not f.exists():
   req=urllib.request.Request(f'https://api.bilibili.com/x/player/playurl?bvid=BV1bJ411J7v6&cid={cid}&qn=16&fnval=0',headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.bilibili.com/','Accept-Encoding':'identity'})
   with urllib.request.urlopen(req,timeout=25) as x:j=json.load(x)
   if j.get('code')!=0:raise ValueError(str(j))
   urls=j['data'].get('durl',[])
   if len(urls)!=1:raise ValueError('Expected one segment: '+str(len(urls)))
   u=urls[0]['url'];req=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.bilibili.com/'})
   with urllib.request.urlopen(req,timeout=30) as x:b=x.read()
   if b[4:8]!=b'ftyp':raise ValueError('not mp4 header '+b[:20].hex())
   f.write_bytes(b)
  b=f.read_bytes();row.update(status='downloaded',bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
 except Exception as e:row.update(status='failed',error=str(e))
 return row
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for row in pool.map(download,inv['unique_video_cids']):
  log.append(row);(r/'media-download.json').write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'total':len(log),'downloaded':sum(x['status']=='downloaded' for x in log),'bytes':sum(x.get('bytes',0) for x in log),'failed':[x for x in log if x['status']=='failed']}))
