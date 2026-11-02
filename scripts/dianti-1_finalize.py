from pathlib import Path
import hashlib,json,zipfile
R=Path(__file__).resolve().parents[1];T=R/'tasks/dianti-1';A=T/'audit'
def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
zpath=R/'packs/dianti-1.prepared.zip'
with zipfile.ZipFile(zpath) as z:payload={n:z.read(n) for n in z.namelist()}
m=json.loads(payload['BUNDLE-MANIFEST.json']);extra='scripts/dianti-1_accept.py';payload[extra]=(R/extra).read_bytes();m['files']=[x for x in m['files'] if x['path']!=extra]+[{'path':extra,'bytes':len(payload[extra]),'sha256':sha(payload[extra])}];payload['BUNDLE-MANIFEST.json']=json.dumps(m,ensure_ascii=False,indent=2).encode()
with zipfile.ZipFile(zpath,'w',compression=zipfile.ZIP_DEFLATED) as z:
 for name,b in payload.items():z.writestr(name,b)
m['archive']='packs/dianti-1.prepared.zip';m['archive_sha256']=sha(zpath.read_bytes());save(R/'packs/dianti-1.prepared.manifest.json',m)
with zipfile.ZipFile(zpath) as z:
 for f in m['files']:assert sha(z.read(f['path']))==f['sha256'],f['path']
resource=R/'packs/dianti-1.resources.zip'
with zipfile.ZipFile(resource) as z:assert z.namelist()==['index.html'];assert z.read('index.html')==(T/'mirror/index.html').read_bytes()
extracted=A/'unpacked-prepared'
for f in m['files']:assert sha((extracted/f['path']).read_bytes())==f['sha256'],f['path']
checks={k:json.loads((A/f'{k}-summary.json').read_text(encoding='utf-8')) for k in ['workspace','prepared','resources']};assert all(x['passed'] for x in checks.values())
result={'record_id':'base664:0322','task_id':'dianti-1','title':'逃离电梯 第一章','runtime_layer':'L1','account_requirement':'none','status':'engineering_complete_content_caveats','resource_status':'complete','integration_status':'complete','content_status':'all_source_branches_and_29_UI_stages_verified','judge_status':'complete','ui_status':'passed_workspace_and_both_independent_extracts','delivery_status':'passed','formal_scoring_suitability':'needs_review_low_difficulty_public_egg_direct_answer_bypass_unsanitized_terminal','evidence':{'readme':'tasks/dianti-1/README.md','spec':'judge/dianti-1/checkpoint-spec.json','source_audit':'tasks/dianti-1/audit/static-audit.json','diff':'tasks/dianti-1/audit/localization.diff','ui_summaries':[f'tasks/dianti-1/audit/{k}-summary.json' for k in checks],'ui_traces':[f'tasks/dianti-1/audit/{k}-ui-trace.json' for k in checks],'harness_smoke':'tasks/dianti-1/audit/unpacked-prepared/runs/dianti-1/B/20261027_011754/summary.json'},'packages':[{'path':f'packs/dianti-1.{kind}.zip','sha256':sha((R/f'packs/dianti-1.{kind}.zip').read_bytes())} for kind in ['resources','prepared']],'independent_acceptance':checks,'limits':['Windows+installed Edge only; not cross-OS tested','No paid API or model calls','Ordinary and egg endings normal, fall bad; no good ending invented','connect gate optional to escape route; final password bypasses clue chain','egg listed in help, no reasoning; hex/decrypt automatic','Original log modal and board placeholder never populated; main screen shows ASCII','Terminal raw innerHTML is native injection risk; no hardening applied'],'all_required_dimensions_complete':True,'formal_benchmark_ready':False}
save(R/'data/preparation/results/base664-0322.json',result)
print('result and both manifests verified; formal_ready=False')
