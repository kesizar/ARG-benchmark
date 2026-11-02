from pathlib import Path
import json,hashlib,zipfile
R=Path(__file__).resolve().parents[1];T='binjiang-lanwei';J=R/'judge'/T;P=R/'tasks'/T;D=R/'runs'/T/'deployment/evaluation'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def put(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
ev=load(J/'verification/evaluation-acceptance.json');res=load(J/'verification/resources-acceptance.json');assert ev['passed'] and res['passed'];assert ev['gates']==res['gates'] and ev['endings']==res['endings']
for report in [ev,res]:
 assert len(report['page_errors'])==1 and 'at updateProgress' in report['page_errors'][0]['stack'] and 'at restartGame' in report['page_errors'][0]['stack']
 assert not report['http_errors'] and not report['blocked_requests'] and report['camera_gate_bypass_demonstrated']
checks=[]
for kind in ['resources','prepared']:
 p=R/'packs'/f'{T}.{kind}.zip'
 with zipfile.ZipFile(p) as z:
  assert z.testzip() is None
  if kind=='resources':assert not any(n.startswith(('judge/','harness/','configs/')) for n in z.namelist())
  else:
   manifest=json.loads(z.read('BUNDLE-MANIFEST.json'))
   for f in manifest['files']:assert hashlib.sha256(z.read(f['path'])).hexdigest()==f['sha256']
 checks.append({'kind':kind,'crc_pass':True,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
summaries=sorted((D/f'runs/{T}/B').glob('*/summary.json'));sm=load(summaries[-1]);assert sm['steps']==2 and sm['ended_reason']=='give_up' and sm['blocked_requests']==0 and sm['tokens']['total']==0
log=(D/'cli-smoke-final.log').read_text(encoding='utf-8',errors='replace');assert '"result": "ok"' in log
put(J/'verification/cli-smoke.json',{'passed':True,'summary':str(summaries[-1].relative_to(R)).replace('\\','/'),'steps':2,'actions':['wait250ms:ok','give_up'],'runtime_layer':'L1','model_api_calls':0,'config_delta':'Only local port8831->8832 in extracted smoke config; final production policy_script uses valid wait+give_up.','source':str((D/'cli-smoke-final.log').relative_to(R)).replace('\\','/')})
put(J/'package-validation.json',{'passed':True,'archives':checks,'prepared_manifest_all_file_hashes_match':True,'resources_has_no_private_evaluator':True})
put(R/'data/preparation/results/base664-0159.json',{
 'record_id':'base664:0159','task_id':T,'title':'滨江新城烂尾楼案','status':'engineering_replay_verified_entry_clue_review_required','category':'web_puzzle','runtime_layer':'L1','account_requirement':'none','ready_for_local_execution':True,'ready_for_formal_scoring':False,
 'resource_status':'19 fixed public files including18 HTML; original16575B snapshot preserved; normalized original/current entry equal; one unreachable monitor.html dead mapping; no reachable HTTP errors or external requests',
 'integration_status':'callable config, standard CLI smoke, Windows Edge+Python3.11.15+Playwright1.63; fresh context reset required',
 'flow_status':'all18HTML via entry/desktop/apps/search;14 keywords;10 WeChat contacts;17 mails;13 Raven messages;8 optional password gates;3 endings;wrong inputs,report errors,reload andfresh reset;source-assisted only',
 'judge_status':'independent DOM judge;0 mandatory password gates,8 optional candidates,3 authored route endings;ordinary search/reading no credit;wrong/blank/gate-reload negative tested;formal disabled',
 'config':f'configs/{T}.json','judge':f'judge/{T}/judge.json','resources_bundle':f'packs/{T}.resources.zip','evaluation_bundle':f'packs/{T}.prepared.zip','archives':load(J/'deployment.json')['archives'],
 'acceptance':f'judge/{T}/verification/evaluation-acceptance.json','resource_acceptance':f'judge/{T}/verification/resources-acceptance.json','deployment_evidence':f'judge/{T}/deployment.json','checkpoint_spec':f'judge/{T}/checkpoint-spec.json','review':f'judge/{T}/review.md','provenance':f'tasks/{T}/provenance.json',
 'coverage':{'html_pages':18,'document_keywords':14,'wechat_contacts':10,'mail_messages':17,'raven_messages':13,'optional_reasoning_candidates':8,'formal_endings':3,'UI_actions_per_independent_full_run':209,'negative_checks_per_full_run':len(ev['negatives']),'two_independent_full_runs':True,'camera_unlock_bypass_demonstrated':True,'known_runtime_errors_per_full_run':1,'http_errors':0,'blocked_requests':0,'final_equivalent_runtime_files':44,'standard_CLI_smoke_steps':2},
 'source_assisted':True,'model_solving_claim':False,'model_api_calls':0,'game_modifications':['Removed decorative FontAwesome CDN link; preserved original anddiff.'],'shared_harness_modifications':[],
 'limitations':['Entry police badge not provided before lock; downstream badge/source credential never added to model prompt.','Camera symbol mapping andserver Biblical02 ambiguity need content review; explicit-source engineering answers are not independent solves.','Good ending accepts searched监控 selected without opening/decrypting footage; all document password gates optional.','Original third-ending menu retry throws null.textContent inupdateProgress after wrongSuspectContent replaced; both packages reproduce. Fresh context fullreset verified.','Original notebook minimized transform not restored byopen; refresh desk recovers. Save click opens SaveAs dialog; no claim of complete text-editor or filesystem save acceptance.','Sourcecurrent entry normalized equal; childhistorical snapshot parity unavailable.','Finaldocs andvalid CLI policy update reuse fullUI evidence after44 byte-identical runtime files; standard CLI smoke repeated onfinal extracted evaluation.','SameWindows machine independent dirs; no crossOS ormodelAPI validation.'],
 'evidence':[f'judge/{T}/{n}' for n in ['resource-check.json','flow.json','checkpoint-spec.json','review.md','compatibility.diff','verification/evaluation-acceptance.json','verification/resources-acceptance.json','verification/cli-smoke.json','final-equivalence.json','package-validation.json','deployment.json']]})
(J/'HANDOFF.md').write_text('''# base664:0159 handoff

结果：data/preparation/results/base664-0159.json。工程全流程与两份ZIP独立完整UI验收通过，formal=false。18HTML、8可绕过密码门、3结局；每份209UI动作，普通搜集不计分。源码辅助输入只在私有回放，不是模型可解证明。

入口警号缺初始线索、监控图案映射不充分、02语义歧义及原作直接监控关键词绕过须正式内容复核。第三结局菜单重开原作null.textContent和记事本最小化不能还原均保留、明确记录，fresh context是完整重置。无共享harness改动，无模型API，无push。

主要证据verification/evaluation-acceptance.json、resources-acceptance.json、cli-smoke.json；两包packs/binjiang-lanwei.resources.zip和.prepared.zip。最终文档及有效CLI policy改动后44个游戏/裁判/harness/回放文件字节一致，完整回放证据可复用，最终CLI另验。端口8831–8833，测试结束不保留服务器。下一步只处理内容复核条件，无需重复资源下载和全流程工程测试。
''',encoding='utf-8')
print('finalized base664:0159; engineering verified, formal false')
