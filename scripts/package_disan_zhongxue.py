"""Build task-specific resource and evaluator bundles; verify extraction hashes."""
from pathlib import Path
import hashlib,json,zipfile,subprocess,sys
R=Path(__file__).resolve().parents[1]; T=R/'tasks/disan-zhongxue'; A=T/'audit'; P=R/'packs'
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),'utf-8')
subprocess.run([sys.executable,str(R/'scripts/build_prepared_bundle.py'),'--task','disan-zhongxue'],check=True)
prepared=P/'disan-zhongxue.prepared.zip'
with zipfile.ZipFile(prepared) as z: data={n:z.read(n) for n in z.namelist()}
m=json.loads(data['BUNDLE-MANIFEST.json'])
extras=['judge/disan-zhongxue/review.md','configs/samples/disan-zhongxue-ui-replay.json','tasks/disan-zhongxue/upstream/snapshot.html','tasks/disan-zhongxue/audit/localization.diff','tasks/disan-zhongxue/audit/structure.json','tasks/disan-zhongxue/audit/fetch.json','tasks/disan-zhongxue/audit/live-vs-snapshot.diff']
for n in extras:
    data[n]=(R/n).read_bytes();m['files'].append({'path':n,'sha256':sha(data[n]),'bytes':len(data[n])})
m['engineering_ready']=True;m['formal_scoring_ready']=False
data['BUNDLE-MANIFEST.json']=json.dumps(m,ensure_ascii=False,indent=2).encode()
with zipfile.ZipFile(prepared,'w',zipfile.ZIP_DEFLATED) as z:
    for n,b in data.items():z.writestr(n,b)
external=dict(m,archive=prepared.relative_to(R).as_posix(),archive_sha256=sha(prepared.read_bytes()));dump(P/'disan-zhongxue.prepared.manifest.json',external)
resource=P/'disan-zhongxue.resources.zip'
with zipfile.ZipFile(resource,'w',zipfile.ZIP_DEFLATED) as z:z.write(T/'mirror/index.html','index.html')
rm={'task_id':'disan-zhongxue','boundary':'player-visible game resources only; no judge, config or solution','files':[{'path':'index.html','sha256':sha((T/'mirror/index.html').read_bytes()),'bytes':(T/'mirror/index.html').stat().st_size}],'archive':resource.relative_to(R).as_posix(),'archive_sha256':sha(resource.read_bytes())};dump(P/'disan-zhongxue.resources.manifest.json',rm)
dest=A/'deployed';dest.mkdir(exist_ok=True)
for file,kind,manifest in [(prepared,'evaluation',m),(resource,'resources',rm)]:
    target=dest/kind
    if target.exists():raise RuntimeError(f'Fresh destination already exists: {target}')
    target.mkdir()
    with zipfile.ZipFile(file) as z:
        assert z.testzip() is None
        assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist())
        z.extractall(target)
    for f in manifest['files']:assert sha((target/f['path']).read_bytes())==f['sha256'],f
dump(A/'bundle-checks.json',{'passed':True,'zip_crc':True,'all_manifest_file_hashes':True,'fresh_extraction':True,'evaluation_root':str(dest/'evaluation'),'resource_root':str(dest/'resources'),'resource_archive_files':['index.html']})
print('both bundles built; hashes/CRC/extraction passed')
