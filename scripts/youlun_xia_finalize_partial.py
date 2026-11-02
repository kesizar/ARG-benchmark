import pathlib,json,hashlib,shutil,zipfile
R=pathlib.Path('judge/youlun-xia/recovery');meta=json.loads((R/'partial-packages.json').read_text(encoding='utf-8'))
ind=pathlib.Path('judge/youlun-xia/independent-evaluation');res=pathlib.Path('judge/youlun-xia/independent-resources')
shutil.copyfile(ind/'judge/youlun-xia/recovery/local-ui.json',R/'independent-resources-ui.json')
checks=[]
for name in ['independent-evaluation-ui.json','independent-resources-ui.json']:
 j=json.loads((R/name).read_text(encoding='utf-8'));assert len(j['runs'])==6 and not j['errors']
 assert [r['verdict']['score'] for r in j['runs']]==[0,0,0,0,0,1]
 assert j['reset']['edge']==1 and len(j['reset']['events'])==1
 checks.append({'evidence':str(R/name),'runs':6,'scores':[0,0,0,0,0,1],'reset':True,'port':j['port'],'browser':j['browser']})
for p in meta['packages']:
 archive=pathlib.Path(p['path']);assert hashlib.sha256(archive.read_bytes()).hexdigest()==p['sha256']
 target=ind if p['type']=='evaluation' else res
 with zipfile.ZipFile(archive) as z:
  if p['type']=='resources':assert all(n.startswith('tasks/youlun-xia/') for n in z.namelist())
  for name in z.namelist():
   payload=z.read(name);assert payload==(target/name).read_bytes()==pathlib.Path(name).read_bytes(),name
 p['all_source_zip_and_extracted_bytes_equal']=True
meta.update(acceptance='six terminal sample UI routes independently passed per partial package; not full formal acceptance',checks=checks,resource_judge_boundary=True)
(R/'partial-packages.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
p=pathlib.Path('data/preparation/results/base664-0647.json');j=json.loads(p.read_text(encoding='utf-8'))
j.update(status='partial_local_adaptation_not_prepared',runtime_layer='L1',original_runtime_layer='L3',account_requirement='none for local adaptation; original further account requirement unknown',integration_status='declared_local_player_and_range_server; shared_harness_config_pending',flow_status='49-video 4-second contact sheets reviewed; six terminal sample UI routes passed; full161 UI coverage pending',judge_status='independent_provisional_terminal_only; formal_reasoning_checkpoints_pending',delivery_status='partial_resource_and_evaluation_zips_independently_tested; not_formal_prepared',content_status='lower_episode_plot_and_terminal_classification_audited_by_sampling; upper_episode_clue_sufficiency_unverified',resources_bundle='packs/youlun-xia.resources.partial.zip',evaluation_bundle='packs/youlun-xia.evaluation.partial.zip')
j['terminal_video_classification']={'success':[142813414],'failure':[142802675,142802702,142802726,142803151],'achievement_without_success':[142802705]}
j['checks'].update(normal_branch_click_verified=True,reset_verified=True,score_positive_negative_verified=True,independent_partial_bundle_acceptance=True,independent_bundle_acceptance=False)
j['limits']=['Upper episode missing; catalogue no upper record, author search -799/WBI412, not proof of unavailability.','49 videos visually reviewed through466 samples at ~4-second spacing, not full audio or frame-by-frame transcription.','Original anonymous initial playback and real canvas choice work; original full routes/account conditions unverified.','Declared local player adaptation and byte-range server; original-player equivalence not asserted.','Six terminal sample routes passed UI, not all161 nodes/transitions. Independent evaluator scores explicit success leaf only; reasoning checkpoints and shared harness pending.','Both ZIPs are partial, independently extracted/tested on this Windows environment, not formally prepared or cross-OS certified.']
j['evidence']+=[x for x in [str(R/'audit-graph.json'),str(R/'frame-review-index.json'),str(R/'original-branch.json'),str(R/'author-probe.json'),str(R/'local-ui.json'),str(R/'partial-packages.json'),'judge/youlun-xia/CONTENT_AUDIT.md'] if x not in j['evidence']]
p.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
print({'status':j['status'],'packages_verified':2,'independent_six_route_runs':2})
