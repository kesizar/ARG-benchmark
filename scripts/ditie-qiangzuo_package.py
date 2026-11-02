from pathlib import Path
import zipfile,json,hashlib,subprocess,sys
R=Path(__file__).resolve().parents[1];T=R/'tasks/ditie-qiangzuo';A=T/'audit'
subprocess.run([sys.executable,str(R/'scripts/build_prepared_bundle.py'),'--task','ditie-qiangzuo'],check=True)
p=R/'packs/ditie-qiangzuo.resources.zip'
with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
 for f in (T/'mirror').rglob('*'):
  if f.is_file():z.write(f,f.relative_to(T/'mirror').as_posix())
for kind in ['prepared','resources']:
 target=A/('unpacked-'+kind);target.mkdir(exist_ok=True)
 with zipfile.ZipFile(R/f'packs/ditie-qiangzuo.{kind}.zip') as z:z.extractall(target)
 prepared=A/'unpacked-prepared';c=json.loads((prepared/'configs/ditie-qiangzuo.json').read_text(encoding='utf-8'))
 # Preserve delivered config byte-for-byte; relocated acceptance config is separate.
 c['entry_url']='http://127.0.0.1:8832/';c['allow_hosts']=['127.0.0.1:8832'];c['local_serve']['ready_url']=c['entry_url'];c['local_serve']['port']=8832;c['local_serve']['command'][-1]='8832'
 (prepared/'configs/ditie-qiangzuo-acceptance.json').write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf-8')
print('packages extracted')
