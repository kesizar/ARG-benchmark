from pathlib import Path
import json, re, hashlib, difflib, urllib.request, datetime

ROOT=Path(__file__).resolve().parents[1]
T=ROOT/'tasks/disan-zhongxue'; A=T/'audit'; J=ROOT/'judge/disan-zhongxue'
for p in (T/'mirror',T/'upstream',A,J):p.mkdir(parents=True,exist_ok=True)
def dump(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
u='https://devfile.vip/preview/y4ds28e1'
try:
    with urllib.request.urlopen(u,timeout=30) as r:
        b=r.read(); (A/'live.html').write_bytes(b)
        dump(A/'fetch.json',{'url':u,'status':r.status,'bytes':len(b),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
except Exception as e:dump(A/'fetch.json',{'url':u,'error':repr(e),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
raw=(T/'upstream/snapshot.html').read_text(encoding='utf-8')
# Hosting infrastructure is not gameplay. Keep the original and an exact patch.
local=re.sub(r'<base href="/preview/y4ds28e1/">','',raw)
local=local.split('<script src="/devfile.js"></script>')[0]+'</body>\n</html>\n'
(T/'mirror/index.html').write_text(local,encoding='utf-8')
(A/'localization.diff').write_text(''.join(difflib.unified_diff(raw.splitlines(True),local.splitlines(True),fromfile='upstream/snapshot.html',tofile='mirror/index.html')),encoding='utf-8')
keys=json.loads('['+re.search(r'const ALL_KEYS = \[(.*?)\];',raw,re.S)[1]+']')
dump(A/'structure.json',{'keys':keys,'functions':re.findall(r'function (\w+)\(',raw),'external_script':['/devfile.js'],'external_game_resources':[],'has_closing_script':True,'has_closing_html':raw.rstrip().endswith('</html>')})
cfg=json.loads((ROOT/'configs/disan-zhongxue.json').read_text(encoding='utf-8'))
dump(A/'config.previous.json',cfg)
cfg.update(runtime_layer='L1',account_requirement='none',entry_url='http://127.0.0.1:8821/index.html',allow_hosts=['127.0.0.1:8821'])
cfg['local_serve']={'enabled':True,'command':['python','scripts/serve_static.py','--root','tasks/disan-zhongxue/mirror','--port','8821'],'cwd':'.','ready_url':cfg['entry_url'],'ready_timeout_s':30,'port':8821}
cfg['notes_for_report']=['Snapshot-derived local edition. No scored reasoning checkpoints: 25 exact-match lookups are collection diagnostics; direct final lookup unlocks all three narrative choices. Engineering readiness is separate from formal scoring suitability.','No model API used. Source-auditor UI acceptance is not a model score.']
dump(ROOT/'configs/disan-zhongxue.json',cfg)
dump(A/'judge.previous.json',json.loads((J/'judge.json').read_text(encoding='utf-8')))
hooks={}; cps=[]
for n,k in enumerate(keys,1):
    ident=f'd{n:02d}'; hooks[ident]={'type':'js_truthy','expr':f"(() => {{const e=document.querySelector('#resultPage');return !!e && e.getClientRects().length>0 && e.querySelector('h4')?.textContent==={json.dumps('校内文档：'+k,ensure_ascii=False)};}})()"}
    cps.append({'id':ident,'hook':ident,'op':'truthy','role':'diagnostic'})
routes=[]
for ident,label in [('truth','真相公示'),('silence','永久封存'),('shard','碎片留存')]:
    hooks[ident]={'type':'js_truthy','expr':f"(() => {{const e=document.querySelector('#fullEndPage'); return !!e && e.getClientRects().length>0 && e.innerText.includes({json.dumps('【结局归档：'+label+'】',ensure_ascii=False)});}})()"}
    routes.append({'id':ident,'tier':'normal','gates':[],'ending':{'hook':ident,'op':'truthy'}})
dump(J/'judge.json',{'hooks':hooks,'checkpoints':cps,'events':{},'routes':routes,'answer_sha256':[],'submit_conclusion':{'enabled':False,'schema':None}})
dump(J/'checkpoint-spec.json',{'record_id':'base664:0398','reasoning_gates':[],'scored_checkpoints':0,'diagnostic_lookup_keys':keys,'unlock':'Search 删除日志 then scroll resultPage to its bottom. No other document prerequisite.','routes':routes,'failures':['Unknown exact keyword: 未检索到相关校内文档; no state change.','Partial keyword and Enter do not search.','No death/timer/failure ending. Give-up is evaluator exit, not an authored ending.'],'latching':'Judge diagnostics/endings latch for one episode; in-game reset clears game visited/UI only; a new Judge instance/new context is required to reset evaluation.','classification':'All three authored archives are formal narrative endings. Normal means completion only; no source-defined earned good/bad score.','source':'tasks/disan-zhongxue/upstream/snapshot.html'})
dump(T/'provenance.json',{'record_id':'base664:0398','entry_url':u,'source':'ARG-packs/verify-416/bodies/398.html','source_sha256':hashlib.sha256((T/'upstream/snapshot.html').read_bytes()).hexdigest(),'source_bytes':(T/'upstream/snapshot.html').stat().st_size,'local_sha256':hashlib.sha256((T/'mirror/index.html').read_bytes()).hexdigest(),'changes':'Remove hosting base and devfile.js/badge injection only. Game script unchanged.','patch':'tasks/disan-zhongxue/audit/localization.diff','runtime':'L1; Python 3.11+, Playwright Chromium/Edge; no game network/API/account dependency','live_check':'tasks/disan-zhongxue/audit/fetch.json'})
print('prepared',len(keys),'diagnostics; 0 reasoning gates')
