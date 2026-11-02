from pathlib import Path
import hashlib,json,re,zipfile
R=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
raw=(R/'judge/yanhuo/source/entry.original.html').read_bytes();s=raw.decode('utf-8')
start=s.index('/* ---- 以下为 #auto=full');end=s.index('/* ============================================================ 启动：',start)
s=s[:start]+s[end:]
(R/'tasks/yanhuo/mirror/index.html').write_text(s,encoding='utf-8')
c=json.loads((R/'configs/yanhuo.json').read_text(encoding='utf-8'));c.update(runtime_layer='L1',entry_url='http://127.0.0.1:8821/index.html',allow_hosts=['127.0.0.1:8821'])
c['local_serve']={'enabled':True,'command':['python','scripts/serve_static.py','--root','tasks/yanhuo/mirror','--port','8821'],'cwd':'.','ready_url':c['entry_url'],'ready_timeout_s':30,'port':8821};c['limits']['max_steps']=300;c['notes_for_report']=['完整单文件本地游戏；移除源站URL触发自动通关测试脚本，保留全部正常游戏逻辑。','七个结论只在实际落判后评分。预算未由模型校准。'];c['account']={'required':False,'reason':'Local fictional case, no external account.'}
(R/'configs/yanhuo.json').write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf-8')
j=json.loads((R/'judge/yanhuo/judge.json').read_text(encoding='utf-8'))
j['hooks']['verdict']={'type':'js_truthy','expr':'S && S.scr === "scr-verdict" && document.getElementById("scr-verdict").classList.contains("active") && SLOTS.every(function(s){return slotCorrect(s.id)}) && document.getElementById("v-stat").textContent.length>0'}
for n in range(1,8):j['hooks']['s'+str(n)]={'type':'js_truthy','expr':f'S && S.scr === "scr-verdict" && slotCorrect("s{n}")'}
for rt in j['routes']:rt['tier']='normal'
(R/'judge/yanhuo/judge.json').write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
old=(R/'ARG-packs/verify-416/bodies/630.html').read_bytes()
p={'source_url':'https://dcd887.github.io/classics-emergence/','historical_snapshot_sha256':sha(old),'live_snapshot_sha256':sha(raw),'historical_equals_live':old==raw,'resource_count':1,'account_required':False,'changes':[{'kind':'benchmark_isolation','detail':'Removed only URL-hash auto=full automated solution/test runner. Original game initialization and gameplay retained.','removed_characters':end-start}],'local_sha256':sha(s.encode('utf-8'))}
(R/'tasks/yanhuo/provenance.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
with zipfile.ZipFile(R/'packs/yanhuo.resources.zip','w',zipfile.ZIP_DEFLATED) as z:z.write(R/'tasks/yanhuo/mirror/index.html','index.html')
(R/'packs/yanhuo.resources.manifest.json').write_text(json.dumps({'archive_sha256':sha((R/'packs/yanhuo.resources.zip').read_bytes()),'files':[{'path':'index.html','sha256':p['local_sha256']} ]},indent=2),encoding='utf-8')
print(json.dumps(p,ensure_ascii=False))
