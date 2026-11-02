from pathlib import Path
import json,zipfile,hashlib
R=Path('.');T='tade-xinhao';J=R/'judge'/T
note='\n明确接入缺条件：原pk-unzip-hint.html要求外部解压软件；PNG/ZIP混合文件及assets/extract_lsb.py（需ffmpeg）原样保留。当前harness不提供下载后解压/外部工具动作，尚未满足原作文件谜题能力条件。详file-tool-conditions.json。不要把这些文件误报损坏或向模型提供私有答案。\n'
for p in [J/'review.md',J/'HANDOFF.md']:
 with p.open('a',encoding='utf8') as f:f.write(note)
p=R/'data/preparation/results/base664-0312.json';d=json.loads(p.read_text(encoding='utf8'));d['blocked_condition']='Current browser-only action surface lacks original requested external decompression/downloaded-file processing; downloads disabled. Original video helper additionally requires ffmpeg if used.';d['evidence'].append('judge/tade-xinhao/file-tool-conditions.json');d['packaging']['final_metadata_note']='Final README/provenance and package START-HERE clarify external file-tool conditions after UI replay; game/config/judge/harness/QA bytes unchanged from passed runs. Final packages re-extracted and all 225 game files compared byte-for-byte; reuse prior port8832/8833 UI evidence only for unchanged runtime.';p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
z=zipfile.ZipFile('packs/tade-xinhao.prepared.zip');manifest=json.loads(z.read('BUNDLE-MANIFEST.json'))
for x in manifest['files']:assert hashlib.sha256(z.read(x['path'])).hexdigest()==x['sha256']
g=zipfile.ZipFile('packs/tade-xinhao.game.zip');assert not any(n.startswith(('judge/','configs/','harness/')) or 'CLAUDE' in n or '故事大纲' in n for n in g.namelist());assert 'mirror/assets/extract_lsb.py' in g.namelist()
print('Final prepared manifest every file hash PASS; public/private boundary PASS; original player helper retained. HANDOFF saved.')
