"""Freeze workspace-local seven-game snapshot and private finite content inventory."""
import ast,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];TASK='qian-anon';SRC=ROOT/'ARG-packs/verify-416/bodies/521.html'
def write(p,o):
 p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
 raw=SRC.read_bytes();assert hashlib.sha256(raw).hexdigest()=='4065790a81404aa3477332ff1346c1bdf628d44a73e711f738d395973c56c2e0';s=raw.decode('utf-8');base=ROOT/f'tasks/{TASK}';private=ROOT/f'judge/{TASK}'
 (base/'mirror').mkdir(parents=True,exist_ok=True);(private/'source').mkdir(parents=True,exist_ok=True);(private/'source/521.original.html').write_bytes(raw);(base/'mirror/index.html').write_bytes(raw)
 inventory={}
 for name in ['NAZO','H_EVENTS','GAL_SCENES']:
  text=re.search(r'const '+name+r' = (\[[\s\S]*?\n\]);',s).group(1)
  text=re.sub(r'\b(q|a|w|n|t|d|c|r|l|e|face|name|text):',r"'\1':",text)
  inventory[name]=ast.literal_eval(text)
 inventory['WORDS']=sorted(set(re.search(r'const WORD_STR = `([^`]+)`',s).group(1).split()))
 inventory['units']=['quiz','pipa','cross','hunt','surf','maze','gal'];write(f'judge/{TASK}/source-inventory.json',inventory)
 write(f'tasks/{TASK}/provenance.json',{'record_id':'base664:0521','original_record_title':'千早爱音解谜社v1.2','snapshot_version':'v1.4 (latest announcement); seven games','canonical_url':'https://anontokyopuzzleclub.netlify.app/','snapshot_path':SRC.relative_to(ROOT).as_posix(),'original_sha256':hashlib.sha256(raw).hexdigest(),'original_bytes':len(raw),'runtime_sha256':hashlib.sha256(raw).hexdigest(),'required_external_assets':[],'optional_external_links':re.findall(r'href="(https?://[^\"]+)"',s),'compatibility_changes':[]})
 print({name:len(inventory[name]) for name in ['NAZO','H_EVENTS','GAL_SCENES','WORDS']})
if __name__=='__main__':main()
