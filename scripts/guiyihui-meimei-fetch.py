import re,urllib.request,pathlib,json,hashlib
p=pathlib.Path('data/preparation/results/base664-0431-embed.html'); html=p.read_text(encoding='utf-8')
urls=sorted(set(re.findall(r'https://images\.pexels\.com/[^\s\'"`<>]+|https://cdn\.jsdelivr\.net/npm/@tailwindcss/browser@4',html)))
out=pathlib.Path('judge/guiyihui-meimei/assets');out.mkdir(parents=True,exist_ok=True)
items=[]
for i,url in enumerate(urls):
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=30) as r: data=r.read(); status=r.status
  name=('tailwind.js' if 'jsdelivr' in url else f'image-{i}.jpg'); (out/name).write_bytes(data)
  items.append(dict(url=url,file=str(out/name),status=status,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
 except Exception as e: items.append(dict(url=url,error=str(e)))
pathlib.Path('judge/guiyihui-meimei/resource-inventory.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(items,ensure_ascii=False,indent=2))
