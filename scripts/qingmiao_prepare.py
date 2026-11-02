from pathlib import Path
import concurrent.futures, hashlib, json, re, time, urllib.request, urllib.parse

ROOT=Path(__file__).resolve().parents[1]
TASK=ROOT/'tasks/qingmiao-zhongxue'
EV=TASK/'evidence'; EV.mkdir(parents=True,exist_ok=True)
BASE='https://qingmiaomiddleschool.github.io/'
SEEDS=[BASE+x+'/' for x in ['Start-Game-','404-ymail.com','Official-Site','Lin-You-s-Blog','Hospital-Ingenium']]
def main():
    queue=set(SEEDS); seen={}; content={}
    def fetch(u):
        part=urllib.parse.urlsplit(u); rel=part.netloc+part.path
        if rel.endswith('/'):rel+='index.html'
        saved=TASK/'original'/rel
        if saved.is_file():
            b=saved.read_bytes();return u,dict(status=200,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),final_url=u,cache=True),b
        try:
            r=urllib.request.urlopen(u,timeout=30); b=r.read()
            return u,dict(status=r.status,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),final_url=r.url),b
        except Exception as e:return u,dict(error=repr(e)),None
    for depth in range(5):
        todo=sorted(queue-set(seen));queue=set()
        if not todo:break
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            for u,info,b in pool.map(fetch,todo):
                seen[u]=info
                if b is None:continue
                part=urllib.parse.urlsplit(u)
                rel=part.netloc+part.path
                if rel.endswith('/'):rel+='index.html'
                out=TASK/'original'/rel;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(b)
                info['local_path']=out.relative_to(ROOT).as_posix()
                if not (b.lstrip().startswith(b'<') or u.endswith(('.css','.js'))):continue
                t=b.decode('utf-8',errors='replace');content[u]=t
                refs=set(re.findall(r'''(?:src|href)\s*=\s*["']([^"'<>]+)["']|url\(["']?([^\)"']+)|["']((?:https?://|images/)[^\s"'<>]+)["']|(https://qingmiaomiddleschool\.github\.io/[a-zA-Z0-9_./-]+)''',t))
                for row in refs:
                    s=next((x for x in row if x),'').strip()
                    if s.startswith(('data:','javascript:','#','mailto:')) or '${' in s:continue
                    v=urllib.parse.urljoin(u,s).split('#')[0]
                    if urllib.parse.urlsplit(v).netloc in ['qingmiaomiddleschool.github.io','i.ibb.co','i.postimg.cc','cdnjs.cloudflare.com','fonts.googleapis.com','fonts.gstatic.com']:
                        queue.add(v)
    (EV/'resource-probe.json').write_text(json.dumps({'time':time.time(),'seed_urls':SEEDS,'resources':seen,'unfetched_candidates':sorted(queue-set(seen))},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'resources':len(seen),'bytes':sum(v.get('bytes',0) for v in seen.values()),'failures':{k:v for k,v in seen.items() if 'error' in v},'remaining':len(queue-set(seen))},ensure_ascii=False))
if __name__=='__main__':main()
