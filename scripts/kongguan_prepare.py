from pathlib import Path
import json,re,shutil,hashlib,difflib
R=Path(__file__).resolve().parents[1];J=R/'judge/kongguan';P=R/'tasks/kongguan';M=P/'mirror';S=J/'source';M.mkdir(parents=True,exist_ok=True)
d=json.loads((S/'resource-inventory.json').read_text(encoding='utf8'));index=(S/'current/index.html').read_bytes();indexhash=hashlib.sha256(index).hexdigest();files=[];diff=[]
for x in d['files']:
 if x.get('status')!=200 or 'path' not in x:continue
 rel=x['path'];f=S/'current'/rel
 if not f.is_file():continue
 raw=f.read_bytes();typ=x.get('type','')
 if rel!='index.html' and hashlib.sha256(raw).hexdigest()==indexhash:continue
 if not rel.endswith('.html') and 'text/html' in typ:continue
 out=raw
 if rel.endswith(('.html','.js','.css')):
  t=raw.decode('utf8');v=re.sub(r'<script[^>]+cloudflareinsights[\s\S]*?</script>','',t)
  if rel=='s1coffin/search/search-data.js':v=v.replace("target: 'https://base64.us/'","target: '/tools/base64/index.html'")
  if t!=v:diff.extend(difflib.unified_diff(t.splitlines(True),v.splitlines(True),fromfile='original/'+rel,tofile='local/'+rel))
  out=v.encode('utf8')
 dest=M/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(out);files.append({'path':rel,'bytes':len(out),'sha256':hashlib.sha256(out).hexdigest()})
tool=M/'tools/base64/index.html';tool.parent.mkdir(parents=True,exist_ok=True);tool.write_text('''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Base64 在线编码解码工具</title><style>body{max-width:900px;margin:60px auto;font:18px system-ui;background:#f5f6f8}textarea{width:100%;height:180px;font:18px monospace}button{padding:12px 30px;margin:15px}</style><h1>Base64 在线编码解码工具</h1><label for="input">输入文本</label><textarea id="input"></textarea><button id="decode">解码</button><button id="encode">编码</button><label for="output">结果</label><textarea id="output" readonly></textarea><script>decode.onclick=()=>{try{output.value=new TextDecoder('utf-8',{fatal:true}).decode(Uint8Array.from(atob(input.value.trim()),c=>c.charCodeAt(0)))}catch(e){output.value='无法解码，请检查输入'}};encode.onclick=()=>{output.value=btoa(String.fromCharCode(...new TextEncoder().encode(input.value)))}</script></html>''',encoding='utf8')
files.append({'path':tool.relative_to(M).as_posix(),'bytes':tool.stat().st_size,'sha256':hashlib.sha256(tool.read_bytes()).hexdigest()})
files=list({x['path']:x for x in files}.values())
(S/'compatibility.diff').write_text(''.join(diff),encoding='utf8');(P/'provenance.json').write_text(json.dumps({'record_id':'base664:0029','origin':'https://duoweishiti.pages.dev/','files':files,'changes':['Removed Cloudflare analytics','External base64.us utility replaced by local UTF-8 Base64 encode/decode helper; original search result and all puzzle logic retained; utility appearance differs'],'source':'judge/kongguan/source/resource-inventory.json'},ensure_ascii=False,indent=2),encoding='utf8')
c=json.loads((R/'configs/kongguan.json').read_text(encoding='utf8'))
if not (S/'original-config.json').exists():shutil.copyfile(R/'configs/kongguan.json',S/'original-config.json');shutil.copyfile(J/'judge.json',S/'original-judge.json')
c.update(runtime_layer='L1',entry_url='http://127.0.0.1:8821/index.html',allow_hosts=['127.0.0.1:8821'],account_requirement='none');c['local_serve']={'enabled':True,'command':['python','scripts/serve_static.py','--root','tasks/kongguan/mirror','--port','8821'],'cwd':'.','ready_url':c['entry_url'],'ready_timeout_s':30,'port':8821};c['viewport']={'width':1920,'height':1080};c['limits'].update(max_steps=2000,max_seconds=10800,max_answer_submits=100);c['notes_for_report']=['Public current version captured 2026-10-27 via Edge; HTTP client 403 does not indicate browser failure.','Authored accounts are fictional local game state, no external login or paid API.','Fresh browser context resets localStorage; game ending review intentionally preserves unlock history.','Normal UI acceptance completed; per-record result records coverage and the Base64 utility adaptation. No model API benchmark was run.'];(R/'configs/kongguan.json').write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf8')
print('prepared',len(files))
