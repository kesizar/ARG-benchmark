import json,pathlib,urllib.request,urllib.error,datetime,time
root=pathlib.Path('judge/youlun-xia/recovery');d=root/'graph';d.mkdir(exist_ok=True)
queue=[1];seen=set();errors=[]
while queue and len(seen)<250:
 edge=queue.pop(0)
 if edge in seen:continue
 seen.add(edge);p=d/(str(edge)+'.json')
 try:
  if p.exists():j=json.loads(p.read_bytes())
  else:
   u=f'https://api.bilibili.com/x/stein/edgeinfo_v2?bvid=BV1bJ411J7v6&graph_version=128506&edge_id={edge}'
   req=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.bilibili.com/','Accept-Encoding':'identity'})
   with urllib.request.urlopen(req,timeout=20) as r:b=r.read()
   j=json.loads(b);p.write_bytes(b)
  if j.get('code')!=0:errors.append({'edge':edge,'response':j});continue
  for q in j['data'].get('edges',{}).get('questions',[]):
   for c in q.get('choices',[]):
    if c['id'] not in seen:queue.append(c['id'])
 except Exception as e:errors.append({'edge':edge,'error':str(e)})
summary={'visited':len(seen),'queue_remaining':queue,'errors':errors,'edges':sorted(seen)}
(root/'graph-crawl.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(summary,ensure_ascii=True))
