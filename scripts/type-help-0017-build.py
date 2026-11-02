import json, shutil, re, hashlib, zipfile, difflib
from pathlib import Path
root=Path('.')
task='type-help-william-rous-0017'
mirror=root/'tasks'/task/'mirror'; mirror.mkdir(parents=True,exist_ok=True)
judge_dir=root/'judge'/task; judge_dir.mkdir(parents=True,exist_ok=True)
original=(root/'data/preparation/type-help-0017/original.html').read_text(encoding='utf8')
localized=original.replace('<script defer src="https://static.itch.io/htmlgame.js" type="text/javascript"></script>','')
assert localized!=original
(mirror/'index.html').write_text(localized,encoding='utf8',newline='')
(root/'data/preparation/type-help-0017/compatibility.diff').write_text(''.join(difflib.unified_diff(original.splitlines(keepends=True),localized.splitlines(keepends=True),fromfile='original.html',tofile='index.html')),encoding='utf8')
graph=json.loads((root/'data/preparation/type-help-0017/scene-graph.json').read_text(encoding='utf8'))
given={'01-QU-1-11','02-EN-1-6-7-10','03-LI-1-4-5-6-7-8-9'}
names=sorted(x['name'] for x in graph['scene_data'] if re.match(r'^(0[1-9]|1[0-9]|2[0-5])-',x['name']) and x['name'] not in given)
hooks={}; checkpoints=[]
for i,name in enumerate(names):
    ident=f'file_{i+1:02}'
    hooks[ident]={'type':'js_truthy','expr':f'!!(window.SugarCube && SugarCube.State.variables.cache && SugarCube.State.variables.cache.includes({json.dumps(name)}))'}
    checkpoints.append({'id':ident,'hook':ident,'op':'truthy'})
hooks['ending']={'type':'js_truthy','expr':'!!(window.SugarCube && SugarCube.State.passage === "End" && document.querySelector("#passages .passage"))'}
hooks['complete']={'type':'js_truthy','expr':'!!(window.SugarCube && SugarCube.State.variables.is_complete)'}
judge={'hooks':hooks,'checkpoints':checkpoints,'events':{'full_cache':{'hook':'complete','op':'truthy'}},'routes':[{'id':'end','tier':'normal','gates':[],'ending':{'hook':'ending','op':'truthy'}}], 'terminal_failures':[], 'ending':None,'answer_sha256':[],'answer_hash_file':None,'request_milestones':[],'submit_conclusion':{'enabled':False,'schema':None},'rubric_path':None}
(judge_dir/'judge.json').write_text(json.dumps(judge,indent=2),encoding='utf8')
(judge_dir/'checkpoint-spec.json').write_text(json.dumps({'source':'original SugarCube cache', 'critical_candidates':dict(zip((f'file_{i+1:02}' for i in range(len(names))),names)),'excluded_given':sorted(given),'caveat':'File names encode time, location and occupants. Valid guesses enter cache without prerequisites. A cached file is an observable discovery, not proof of reasoning; suitability for formal scoring requires calibration. No individual file is a mandatory ending gate. The directly accessible ending is not proof of completion.'},indent=2),encoding='utf8')
cfg=json.loads((root/'configs/samples/wuluo-cun-api-smoke.json').read_text(encoding='utf8'))
cfg.update({'id':task,'category':'web_puzzle','runtime_layer':'L1','account_requirement':'none','entry_url':'http://127.0.0.1:8851/index.html','local_serve':{'enabled':True,'command':['python','scripts/serve_static.py','--root',f'tasks/{task}/mirror','--port','8851'],'cwd':'.','ready_url':'http://127.0.0.1:8851/index.html','ready_timeout_s':30,'port':8851},'allow_hosts':['127.0.0.1:8851'],'judge_path':f'judge/{task}/judge.json','model_visible':{'title':'Type Help','intro':'Investigate the mystery using the game interface and the evidence it provides.'},'locale':'en-US','timezone':'UTC','limits':{'max_steps':1000,'max_seconds':7200,'max_answer_submits':5},'require_images':False,'notes_for_report':['Source-assisted engineering verification is not a model reasoning evaluation.']})
(root/'configs'/f'{task}.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf8')
(root/'tasks'/task/'README.md').write_text('Type Help by William Rous. Public itch HTML captured from https://html-classic.itch.zone/html/18831707/index.html?v=1786900908. The external itch integration script is removed for offline use; original and diff retained in preparation evidence. Start with python scripts/serve_static.py --root tasks/type-help-william-rous-0017/mirror --port 8851. Fresh browser context resets session; clear site storage for a reused context. The game includes an optional external YouTube link, which is blocked in L1.\n',encoding='utf8')
with zipfile.ZipFile(root/'packs'/f'{task}.resources.zip','w',zipfile.ZIP_DEFLATED) as z:
    z.write(mirror/'index.html','index.html')
print('candidate discovery points',len(names),'localized sha256',hashlib.sha256((mirror/'index.html').read_bytes()).hexdigest())
