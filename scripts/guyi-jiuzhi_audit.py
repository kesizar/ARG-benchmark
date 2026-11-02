from pathlib import Path
import hashlib,json,re,zipfile
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
ROOT=Path(__file__).resolve().parents[1]
TASK=ROOT/'tasks/guyi-jiuzhi'
SITE=TASK/'mirror'
OUT=ROOT/'judge/guyi-jiuzhi'
OUT.mkdir(parents=True,exist_ok=True)
class Links(HTMLParser):
    def __init__(self): super().__init__();self.refs=[]
    def handle_starttag(self,tag,attrs):
        for k,v in attrs:
            if k in ('href','src','action','poster') and v:self.refs.append((k,v))
refs=[]
for p in sorted(SITE.rglob('*.html')):
    t=p.read_text(encoding='utf-8'); h=Links();h.feed(t)
    h.refs += [('js',v) for v in re.findall(r'''(?:location\.href\s*=|location\.(?:assign|replace)\s*\()\s*['"]([^'"]+)''',t)]
    for kind,v in h.refs:
        u=urlsplit(v)
        if u.scheme in ('data','javascript','mailto','tel') or v.startswith('#'):continue
        rel=unquote(u.path)
        refs.append({'source':p.relative_to(SITE).as_posix(),'kind':kind,'target':v,'external':bool(u.netloc),'exists':None if u.netloc else (p.parent/rel).is_file() if rel else True})
files=[{'path':p.relative_to(SITE).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(SITE.rglob('*')) if p.is_file()]
report={'commit':'1462fe8bf43b67c00e2ba45d7db11ed775c10754','file_count':len(files),'bytes':sum(x['bytes'] for x in files),'files':files,'references':refs,'missing':[r for r in refs if r['exists'] is False],'external':[r for r in refs if r['external']]}
(OUT/'resource-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'files':len(files),'missing_targets':sorted(set(x['target'] for x in report['missing'])),'external':sorted(set(x['target'] for x in report['external']))},ensure_ascii=False))
