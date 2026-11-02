import hashlib,json,re,urllib.parse,urllib.request,urllib.error
from pathlib import Path
R=Path(__file__).resolve().parents[1]; T=R/'tasks/shenhu-nvgao'; M=T/'mirror'; O=R/'runs/shenhu-nvgao'
refs=[]
for p in sorted(M.glob('*.html')):
 s=p.read_text(encoding='utf-8')
 for pattern in [r'(?:href|src)\s*=\s*[\"\']([^\"\']+)',r'(?:location\.href\s*=|(?:link|links|redirect)\s*:)\s*[\"\']([^\"\']+)']:
  for m in re.finditer(pattern,s):
   u=m.group(1); path=urllib.parse.urlsplit(u).path
   if u.startswith(('#','javascript:','mailto:')) or '${' in u or not path:continue
   refs.append({'file':p.name,'line':s[:m.start()].count('\n')+1,'target':u,'external':bool(urllib.parse.urlsplit(u).netloc),'exists':(M/path).exists()})
missing=[r for r in refs if not r['external'] and not r['exists']]
result={'record_id':'base664:0260','repository_tree_sha':json.loads((O/'tree.json').read_text())['sha'],'files':[{'path':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(M.iterdir()) if p.is_file()],'references':refs,'missing':missing,'external':[r for r in refs if r['external']]}
if '--network' in __import__('sys').argv:
 result['remote_missing_checks']=[]
 for target in sorted({r['target'] for r in missing}):
  u='https://heiziheizi123.github.io/kobehighschool/'+target
  try:
   with urllib.request.urlopen(u,timeout=30) as x:b=x.read(); status=x.status
  except urllib.error.HTTPError as e:b=e.read();status=e.code
  except Exception as e:result['remote_missing_checks'].append({'url':u,'error':repr(e)});continue
  (O/('remote-'+target.replace('/','_')+'.body')).write_bytes(b)
  result['remote_missing_checks'].append({'url':u,'status':status,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
(O/'resource-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'files':len(result['files']),'missing':missing,'external':result['external'],'remote':result.get('remote_missing_checks')},ensure_ascii=True))
