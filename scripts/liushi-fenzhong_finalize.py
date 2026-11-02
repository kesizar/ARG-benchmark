from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];T='liushi-fenzhong';J=R/'judge'/T
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
a=read(J/'verification/acceptance.json');e=read(J/'verification/exploration.json');d=read(J/'deployment.json');m=read(R/'packs'/f'{T}.prepared.manifest.json')
assert a['pass'] and e['pass'] and d['pass']
for f in m['archives']:assert hashlib.sha256((R/f['path']).read_bytes()).hexdigest()==f['sha256']
acc={'record_id':'base664:0361','original_acceptance':'judge/liushi-fenzhong/verification/acceptance.json','exploration':'judge/liushi-fenzhong/verification/exploration.json','independent_deployment':'judge/liushi-fenzhong/deployment.json','main_pass':True,'exploration_pass':True,'both_archives_independently_unpacked':True,'private_bundle_verification_pass':True,'resource_bundle_normal_ui_win_and_reload_pass':True,'shared_harness_edited':False,'game_source_edited':False,'clock_accelerated':False,'default_3600second_expiry_tested':False}
write(R/'packs'/f'{T}.acceptance.json',acc)
root=Path(d['deployment_root']);smokes=list((root/'prepared/runs'/T/'B').glob('*/summary.json'));assert smokes
result={'record_id':'base664:0361','task_id':T,'title':'60分钟 再死一次','status':'engineering_ready_content_unsuitable_for_reasoning','runtime_layer':'L1','account_requirement':'none','ready_for_local_execution':True,'ready_for_formal_scoring':False,'full_scope_acceptance_complete':False,'resource_state':'gameplay_complete_optional_donation_image_missing','resources_bundle':f'packs/{T}.resources.zip','evaluation_bundle':f'packs/{T}.prepared.zip','archives':m['archives'],'acceptance':f'packs/{T}.acceptance.json','deployment_evidence':f'judge/{T}/deployment.json','runner_smoke':str(smokes[-1]),'runner_smoke_scope':'documented script policy give_up; no model or complete solving claim','coverage':{'targets_full_five_question_win':18,'nonkiller_win_exploits':17,'wrong_answer_depths':[1,2,3,4,5],'zero_notes_main_list_block':True,'reasoning_gates':5,'normal_ui_character_safe_dialogue_and_first_search':18,'notes_observed':e['notes'],'mislead_rules':e['coverage']['misleads'],'relationship_edges_clicked':sum(x['clicked'] for x in e['coverage']['relation_edges']),'relationship_edges_total':len(e['coverage']['relation_edges']),'relationship_edges_unreached':[x['index'] for x in e['coverage']['relation_edges'] if not x['clicked']],'wechat_chats':5,'terminal_source_completions':1,'post_win_forced_twist':True,'ui_deaths':['stir','alert','timeup in original test mode'],'reset':'fresh context and reload verified','default_clock':e['default_clock'],'timer_test':a['timer_test']},'content_findings':['Five exact answer gates end win without verifying accused identity;17 nonkiller accusations accepted in UI.','Person shortcut starts with2 notes, main accusation list requires5.','Next does not reset in-memory killer/scenario/alert/deadline/_confirmed; second/third scenario definitions not reachable from clean context with correct normal restart.','Peripheral killer delayed chat message undefined; full5-chat coverage conditioned on standard harness seed1 core killer.','3 relationship lines lack exposed sampled hit points; no force/event dispatch used.','Donation image absent in collection, optional and visibly broken.'],'model_api_calls':0,'limitations':['Default60-minute expiry not waited; default clock decrease observed, actual92.328-second expiry uses source-provided?test90-second parameter.','No game state or clock setter used; shared harness standard Math.random seed mechanism retained.','No live-site parity or cross-OS verification.','Private oracle reads source state to select test answers; not a model-solving run.'],'evidence':[f'judge/{T}/flow.json',f'judge/{T}/checkpoint-spec.json',f'judge/{T}/review.md',f'tasks/{T}/resource-audit.json',f'judge/{T}/verification/acceptance.json',f'judge/{T}/verification/exploration.json',f'judge/{T}/deployment.json']}
write(R/'data/preparation/results/base664-0361.json',result)
(R/'tasks'/T/'HANDOFF.md').write_text('''# HANDOFF — base664:0361

沿用旧ID liushi-fenzhong。原HTML80561B字节/哈希未改，L1本地入口8811，无账号、零API。
结果：data/preparation/results/base664-0361.json；双包与manifest/acceptance位于packs/liushi-fenzhong.*。
原目录main24项PASS，18目标五问全对，17非凶手也胜利；5逐题错误只保留此前答对分并锁定；3死亡及胜后反转、next缺陷、刷新重置。
18人安全对话/首次搜查、97笔记、4误导、16/19可点关系线、5微信和真正凶手胜利已验；3关系线几何未触达。
默认60:00→59:57真实2.2秒；原作?test90秒模式真实92.328秒归零死亡。完整3600秒到期未验，不能将90秒或源码等同整小时证据。
两包独立目录/新端口/新context验收，资源包胜利/刷新/私裁判404，评测包quick含5逐题负例、stir/alert死亡与真实90秒超时；另独立运行文档命令runner give_up冒烟。
裁判5门以quizStep锁存，消除旧toast门；忠实保留原作胜利，同时诊断genuine/bypass。原作身份验证、轮回内存、外围凶手微信缺陷使版本不适合正式推理计分。下毒/坠楼仅源码定义，不冒称UI已通。捐款收款码.jpg软缺，保留原引用和坏图证据。
脚本：scripts/liushi-fenzhong_prepare.py、_bundle.py、_deploy.py、_finalize.py；私有验收judge/liushi-fenzhong/verify_sample.py、verify_exploration.py。
不改共享harness/progress；没有推送、购买或付费API。全部服务/浏览器由脚本finally停止。后续若修原作游戏逻辑须作为新版本，保留原件与diff后重新验受影响路径。
''',encoding='utf-8')
print('result0361 + HANDOFF saved')
