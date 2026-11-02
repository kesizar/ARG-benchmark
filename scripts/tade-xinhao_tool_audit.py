from pathlib import Path
import json,zipfile
R=Path('.');T='tade-xinhao';P=R/'tasks'/T;J=R/'judge'/T
extra='''\n补充能力边界：玩家资源原样保留上游 assets/extract_lsb.py（未被页面链接的通用LSB视频提取助手），若使用它需额外Python及ffmpeg；并非私有裁判。页面pk-unzip-hint.html明确要求解压文件、建议其他解压软件，assets/CAESAR3vhdufkSN.zip是PNG头/ZIP混合文件，cache-e7a4.zip是PNG头且Python zipfile不识别。未将其误报下载损坏，也未修写谜题文件。当前浏览器动作不提供下载后解压、外部工具调用，属于正式接入待解决的真实能力条件。\n'''
with (P/'README.md').open('a',encoding='utf8') as f:f.write(extra)
with (J/'review.md').open('a',encoding='utf8') as f:f.write(extra)
d=json.loads((P/'provenance.json').read_text(encoding='utf8'));d['additional_tool_conditions']={'original_asset_helper':'assets/extract_lsb.py requires Python + external ffmpeg if used','file_puzzle':'pk-unzip-hint explicitly asks external decompressor; PNG/ZIP polyglot retained unchanged','current_harness_gap':'no model-facing filesystem/decompress/upload actions; accept_downloads=False'};(P/'provenance.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
a=[]
for p in (P/'mirror/assets').glob('*.zip'):
 item={'path':str(p),'magic':p.read_bytes()[:8].hex(),'python_zipfile_recognized':zipfile.is_zipfile(p)}
 if item['python_zipfile_recognized']:
  with zipfile.ZipFile(p) as z:item['members']=[{'path':i.filename,'bytes':i.file_size,'encrypted':bool(i.flag_bits&1)} for i in z.infolist()]
 a.append(item)
(J/'file-tool-conditions.json').write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf8')
p=R/'scripts/tade-xinhao_package.py';s=p.read_text(encoding='utf8');s=s.replace('no backend, paid API or real account.', 'no backend, paid API or real account. Original file puzzles ask external decompression; current browser-only candidate does not provide those tools. Original assets/extract_lsb.py requires ffmpeg if used.');p.write_text(s,encoding='utf8')
print('tool conditions recorded; game source unchanged')
