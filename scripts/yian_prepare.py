from pathlib import Path
import hashlib,json,re,zipfile,itertools
R=Path(__file__).resolve().parents[1];T='yian-juanzong'
raw=(R/f'judge/{T}/source/entry.original.html').read_bytes();s=raw.decode('utf-8');start=s.index('  /* ============================================================\n   * 自测入口：');end=s.index('\n})();',start)
s=s[:start]+'  document.addEventListener("DOMContentLoaded", init);'+s[end:]
s=s.replace('mode: "llm",','mode: "demo",').replace('return { ...this.DEFAULTS, ...JSON.parse(raw) };','return { ...this.DEFAULTS, ...JSON.parse(raw), mode: "demo" };')
s=re.sub(r'GATEWAY_KEY: "[^"]*"','GATEWAY_KEY: ""',s);s=re.sub(r'baseUrl: "https://[^"]*"','baseUrl: ""',s)
s=s.replace('<option value="llm">','<option value="llm" disabled>')
s=s.replace('localStorage.removeItem("anyluo_save");','localStorage.removeItem("anyluo_save"); localStorage.removeItem("benchmark_yian_verdict");')
# Evaluator-only submitted result markers, populated solely in original validation branch.
s=s.replace('const grade = score === 100', 'localStorage.setItem("benchmark_yian_verdict", JSON.stringify({murderer:v.murderer === t.murderer,motive:v.motive === t.motive,method:v.method === t.method,score:score}));\n    const grade = score === 100')
(R/f'tasks/{T}/mirror/index.html').write_text(s,encoding='utf-8')
c=json.loads((R/f'configs/{T}.json').read_text(encoding='utf-8'));c.update(runtime_layer='L1',entry_url='http://127.0.0.1:8821/index.html',allow_hosts=['127.0.0.1:8821']);c['local_serve']={'enabled':True,'command':['python','scripts/serve_static.py','--root',f'tasks/{T}/mirror','--port','8821'],'cwd':'.','ready_url':c['entry_url'],'ready_timeout_s':30,'port':8821};c['limits']['max_steps']=350;c['notes_for_report']=['本地离线演示模式，保留确定性证据链、档案、时间线、结案机制。','已移除URL自动通关、网关凭证；仅原始提交评分分支增加私有裁判标记。','300+步预算未经模型校准。'];(R/f'configs/{T}.json').write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf-8')
expr='JSON.parse(localStorage.getItem("anyluo_save")||"{}")';ver='JSON.parse(localStorage.getItem("benchmark_yian_verdict")||"{}")';hooks={};cps=[]
for n in range(1,13):
 k=f't{n:02}';hooks[k]={'type':'js_truthy','expr':f'({expr}.timelineOrder||[])[{n-1}]==="ev_{n:03}"'};cps.append({'id':k,'hook':k,'op':'truthy'})
for name,num in [('王建国',5),('李慧敏',2),('陈晓东',2)]:
 prefix={'王建国':'wang','李慧敏':'li','陈晓东':'chen'}[name]
 for lv in range(1,num+1):
  k=f'{prefix}{lv}';hooks[k]={'type':'js_truthy','expr':f'(({expr}.breakLevel||{{}})["{name}"]||0)>={lv}'};cps.append({'id':k,'hook':k,'op':'truthy'})
for key in ['murderer','motive','method']:hooks[key]={'type':'js_truthy','expr':f'{ver}.{key}===true'};cps.append({'id':key,'hook':key,'op':'truthy'})
hooks['ending']={'type':'js_truthy','expr':f'{ver}.score===100 && document.getElementById("verdict-result").textContent.includes("案件告破")'}
routes=[{'id':'solved','tier':'normal','gates':['murderer','motive','method'],'gate_groups':[{'ids':[f't{n:02}' for n in range(1,13)],'required':10},{'ids':['wang1','li1','chen1'],'required':1}],'ending':{'hook':'ending','op':'truthy'}}]
for cp in cps:
 if cp['id'] in ['wang2','wang3','wang4','wang5','li2','chen2']:cp['role']='optional'
j={'hooks':hooks,'checkpoints':cps,'events':{},'routes':routes,'ending':{'hook':'ending','op':'truthy'},'answer_sha256':[],'answer_hash_file':None,'request_milestones':[],'submit_conclusion':{'enabled':False,'schema':None},'rubric_path':None};(R/f'judge/{T}/judge.json').write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(b):return hashlib.sha256(b).hexdigest()
p={'source_url':'https://dcd887.github.io/anluo-yiyun/','live_sha256':sha(raw),'historical_sha256':sha((R/'ARG-packs/verify-416/bodies/637.html').read_bytes()),'local_sha256':sha(s.encode()),'changes':['Removed URL triggered automatic solution/test runner.','Fixed runtime to original offline demo AI; removed public gateway key and default endpoint.','Added original validation branch submission-result marker; no answers/conditions/gameplay changed.'],'resource_count':1,'account_required':False};(R/f'tasks/{T}/provenance.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
with zipfile.ZipFile(R/f'packs/{T}.resources.zip','w',zipfile.ZIP_DEFLATED) as z:z.write(R/f'tasks/{T}/mirror/index.html','index.html')
(R/f'packs/{T}.resources.manifest.json').write_text(json.dumps({'sha256':sha((R/f'packs/{T}.resources.zip').read_bytes()),'files':[{'path':'index.html','sha256':p['local_sha256']} ]},indent=2),encoding='utf-8')
print('Prepared',len(cps),'points',len(routes),'route alternatives')
