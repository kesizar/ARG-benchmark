"""Task-specific additions to the shared local browser bundle format."""
from pathlib import Path
import hashlib,json,subprocess,sys,zipfile
R=Path(__file__).resolve().parents[1];T='shenjia-yichan'
def main():
 subprocess.run([sys.executable,str(R/'scripts/build_prepared_bundle.py'),'--task',T],check=True,cwd=R)
 path=R/'packs'/f'{T}.prepared.zip'
 with zipfile.ZipFile(path) as z:entries={n:z.read(n) for n in z.namelist()}
 manifest=json.loads(entries.pop('BUNDLE-MANIFEST.json'))
 extra=['private-members.json','verify_auxiliary.py','verify_media.py','verify_failure_hint.py','relationship-evidence.json','resource-check.json','source-defects.json','review.md']
 for name in extra:
  f=R/'judge'/T/name;data=f.read_bytes();rel=f.relative_to(R).as_posix();entries[rel]=data;manifest['files'].append({'path':rel,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
 manifest['readiness']='Engineering acceptance required.35 supported relationship candidates plus3 diagnostic unsupported spouse mechanics; content not approved.'
 entries['BUNDLE-MANIFEST.json']=json.dumps(manifest,ensure_ascii=False,indent=2).encode('utf-8')
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  for name,data in entries.items():z.writestr(name,data)
 manifest['archive']=path.relative_to(R).as_posix();manifest['archive_sha256']=hashlib.sha256(path.read_bytes()).hexdigest();(R/'packs'/f'{T}.prepared.manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 print(manifest['archive_sha256'])
if __name__=='__main__':main()
