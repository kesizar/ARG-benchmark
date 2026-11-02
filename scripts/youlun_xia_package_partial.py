import pathlib,zipfile,json,hashlib,sys,platform,importlib.metadata
root=pathlib.Path.cwd();out=root/'packs';out.mkdir(exist_ok=True)
provenance_path=root/'tasks/youlun-xia/provenance.json';provenance=json.loads(provenance_path.read_text(encoding='utf-8'))
provenance.update(local_adapter_status='partial_not_prepared',runtime_layer_candidate='L1 local adaptation; original L3 separately observed',local_account_requirement='none',compatibility_changes=['Declared replacement HTML video player with standard byte-range server, original branch graph and videos, accessible progress seeking and reset. Not asserted original-player-equivalent.'])
provenance_path.write_text(json.dumps(provenance,ensure_ascii=False,indent=2),encoding='utf-8')
resource=[p for p in (root/'tasks/youlun-xia').rglob('*') if p.is_file()]
extra=[root/f'judge/youlun-xia/{x}' for x in ['serve.py','evaluate.py','test_local.py','PARTIAL_README.md','CONTENT_AUDIT.md','recovery/audit-graph.json','recovery/media-validation.json','recovery/media-download.json']]
records=[]
for label,paths in [('resources',resource),('evaluation',resource+extra)]:
 p=out/f'youlun-xia.{label}.partial.zip'
 with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
  for f in paths:z.write(f,f.relative_to(root).as_posix())
 records.append({'type':label,'path':str(p.relative_to(root)),'files':len(paths),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
target=root/'judge/youlun-xia/independent-evaluation'
target.mkdir(exist_ok=True)
with zipfile.ZipFile(out/'youlun-xia.evaluation.partial.zip') as z:z.extractall(target)
resource_target=root/'judge/youlun-xia/independent-resources';resource_target.mkdir(exist_ok=True)
with zipfile.ZipFile(out/'youlun-xia.resources.partial.zip') as z:z.extractall(resource_target)
record={'status':'partial_not_prepared','packages':records,'independent_root':str(target),'python':sys.version,'platform':platform.platform(),'playwright':importlib.metadata.version('playwright'),'acceptance':'pending'}
(root/'judge/youlun-xia/recovery/partial-packages.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print({'packages':[{k:v for k,v in r.items() if k!='sha256'} for r in records],'extracted':str(target)})
