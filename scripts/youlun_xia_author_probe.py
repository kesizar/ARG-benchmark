import pathlib,json,urllib.request,urllib.parse,concurrent.futures
R=pathlib.Path('judge/youlun-xia/recovery')
urls=[
('author_search','https://api.bilibili.com/x/space/arc/search?mid=85827007&ps=50&pn=1&keyword='+urllib.parse.quote('邮轮')),
('author_mobile','https://api.bilibili.com/x/space/wbi/arc/search?mid=85827007&ps=50&pn=1&order=pubdate'),
('author_space','https://space.bilibili.com/85827007/upload/video'),
]
def run(pair):
 name,url=pair;row={'name':name,'url':url}
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.bilibili.com/'}),timeout=12) as response:
   b=response.read();(R/(name+'.body')).write_bytes(b);row.update(status=response.status,bytes=len(b))
   try:row['response']=json.loads(b)
   except:pass
 except Exception as e:row['error']=str(e)
 return row
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:rows=list(ex.map(run,urls))
(R/'author-probe.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8');print([{k:v for k,v in r.items() if k!='response'} for r in rows])
