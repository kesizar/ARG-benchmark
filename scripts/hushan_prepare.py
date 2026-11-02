"""Freeze collection source and generate private source inventory/configuration."""
import ast,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TASK='hushan-xiangcheng'
SRC=Path('D:/HuaweiMoveData/Users/17669/Desktop/ARG-packs/verify-416/bodies/445.html')
def write(path,obj):
 p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
 raw=SRC.read_bytes();s=raw.decode('utf-8');base=ROOT/'tasks'/TASK;private=ROOT/'judge'/TASK
 (base/'mirror').mkdir(parents=True,exist_ok=True);(private/'source').mkdir(parents=True,exist_ok=True)
 (base/'mirror/index.html').write_bytes(raw);(private/'source/445.original.html').write_bytes(raw)
 pools={}
 for key,name in [('ids','IDS'),('radical','RAD'),('family','FAM'),('tone','TONE')]:
  chunk=re.search(r'const '+name+r'_POOL = (\[[\s\S]*?\n\]);',s).group(1)
  chunk=re.sub(r'\b(q|opts|a|ex):',r"'\1':",chunk)
  pool=ast.literal_eval(chunk)
  ranks=ast.literal_eval(re.search(r'const '+name+r'_RANKS = (\[[\s\S]*?\n\]);',s).group(1))
  pools[key]={'questions':[dict(id=f'{key}-{i+1:02}',**q) for i,q in enumerate(pool)],'ranks':ranks,'round_size':10,'selection':'pool.slice().sort(random-.5).slice(0,10); not uniform shuffle'}
 write(f'judge/{TASK}/question-pools.json',pools)
 write(f'tasks/{TASK}/provenance.json',{'original_record':'base664:0445','source_snapshot':str(SRC),'canonical_url':'https://kirakiradokidoki.netlify.app/','original_sha256':hashlib.sha256(raw).hexdigest(),'original_bytes':len(raw),'compatibility_changes':[],'optional_external_links':re.findall(r'href="(https?://[^"]+)"',s),'external_required_resources':[]})
 print({k:len(v['questions']) for k,v in pools.items()})
if __name__=='__main__':main()
