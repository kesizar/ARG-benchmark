from pathlib import Path
import json,zipfile,hashlib
R=Path(__file__).resolve().parents[1];T='tade-xinhao';M=R/'tasks'/T/'mirror';O=R/'runs'/T/'deployments';O.mkdir(parents=True,exist_ok=True)
f=[x for x in M.rglob('*') if x.is_file()];manifest={'status':'RESOURCE RECOVERY ONLY; full acceptance pending','record_id':'base664:0312','files':[{'path':'mirror/'+x.relative_to(M).as_posix(),'sha256':hashlib.sha256(x.read_bytes()).hexdigest(),'bytes':x.stat().st_size} for x in f]}
p=R/'packs'/f'{T}.game.zip'
with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
 for x in f:z.write(x,'mirror/'+x.relative_to(M).as_posix())
 z.writestr('GAME-MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2));z.writestr('START-HERE.txt','RESOURCE RECOVERY ONLY. Full routes/scoring NOT ACCEPTED. Serve only mirror/. Fresh browser context required. Python 3.11+ static HTTP server or equivalent; no backend, paid API or real account. Original file puzzles ask external decompression; current browser-only candidate does not provide those tools. Original assets/extract_lsb.py requires ffmpeg if used.\n')
for name,zpath in [('game',p),('prepared',R/'packs'/f'{T}.prepared.zip')]:
 dest=O/name
 with zipfile.ZipFile(zpath) as z:z.extractall(dest)
 root=dest/'mirror' if name=='game' else dest/'tasks'/T/'mirror'
 assert all((root/x.relative_to(M)).read_bytes()==x.read_bytes() for x in f)
 print(name,'files byte-equal',len(f),'archive',zpath.stat().st_size,'sha256',hashlib.sha256(zpath.read_bytes()).hexdigest())
(R/'packs'/f'{T}.game.manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
