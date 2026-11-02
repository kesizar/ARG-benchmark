import httpx,re,json,hashlib
from pathlib import Path
from urllib.parse import urljoin,urlsplit
base="https://forever-summer.pages.dev/";root=Path("judge/yongyuan-xiatian/source/site");root.mkdir(parents=True,exist_ok=True);queue=[base];seen=set();out=[]
with httpx.Client(timeout=30,follow_redirects=True) as c:
 while queue and len(seen)<120:
  u=queue.pop(0)
  if u in seen:continue
  seen.add(u)
  try:
   r=c.get(u);rel=urlsplit(u).path.lstrip("/") or "index.html";p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(r.content);rec={"url":u,"status":r.status_code,"bytes":len(r.content),"sha256":hashlib.sha256(r.content).hexdigest(),"path":str(p)};out.append(rec);print(rel,r.status_code,len(r.content),flush=True)
   if r.status_code!=200:continue
   if "text/" in r.headers.get("content-type","") or rel.endswith((".html",".js",".css")):
    s=r.text;refs=set(re.findall(r"[\"']([^\"'\s<>]{1,180}\.(?:html?|js|css|png|jpe?g|webp|gif|svg|mp3|ogg|wav|mp4|webm|woff2?)(?:[?#][^\"'\s<>]*)?)[\"']",s,re.I))
    for ref in refs:
     v=urljoin(u,ref).split("?")[0].split("#")[0]
     if urlsplit(v).netloc==urlsplit(base).netloc and v not in seen:queue.append(v)
  except Exception as e:out.append({"url":u,"error":str(e)})
Path("judge/yongyuan-xiatian/source/crawl.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
