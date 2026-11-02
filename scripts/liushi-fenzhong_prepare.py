from pathlib import Path
import json,hashlib,shutil,re
R=Path(__file__).resolve().parents[1];T='liushi-fenzhong';P=R/'tasks'/T;J=R/'judge'/T
(P/'mirror').mkdir(parents=True,exist_ok=True);(J/'source').mkdir(parents=True,exist_ok=True)
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
for p,n in [(R/f'configs/{T}.json','legacy-config.json'),(J/'judge.json','legacy-judge.json')]:
 if p.exists() and not (J/'source'/n).exists():shutil.copyfile(p,J/'source'/n)
src=R/'ARG-packs/verify-416/bodies/361.html';shutil.copyfile(src,P/'mirror/index.html')
s=src.read_text(encoding='utf-8');refs=re.findall(r'''(?:src|href)=["']([^"']+)''',s)
write(P/'resource-audit.json',{'html_bytes':src.stat().st_size,'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'static_refs':refs,'external_urls':re.findall(r'''https?://[^\s<>"']+''',s),'fetch_calls':bool(re.search(r'fetch\s*\(',s)),'source_unchanged':src.read_bytes()==(P/'mirror/index.html').read_bytes(),'missing_files':[x for x in refs if not x.startswith(('#','data:','http')) and not (P/'mirror'/x).exists()],'account_requirement':'none','missing_impact':'only optional donation QR image; source and reference retained'})
c=json.loads((R/f'configs/{T}.json').read_text(encoding='utf-8'));base=json.loads((R/'configs/baoya.json').read_text(encoding='utf-8'))
c.update(runtime_layer='L1',account_requirement='none',entry_url='http://127.0.0.1:8811/index.html',local_serve=base['local_serve'],allow_hosts=['127.0.0.1:8811'])
c['local_serve']['command'][3]=f'tasks/{T}/mirror';c['limits'].update(max_steps=350,max_seconds=3900,max_answer_submits=30)
c['notes_for_report']=['原样冻结；原作五问通过不验证被指认者身份，next不重置内存角色/警觉/截止时间，正式计分暂不推荐。','默认60分钟；?test为原作90秒诊断模式，绝非60分钟实际等待证据。','捐款图片收款码.jpg未获取，非谜题资源；保留原始引用。'];write(R/f'configs/{T}.json',c)
def hk(e):return {'type':'js_truthy','expr':e}
hooks={}
for i,name in enumerate(['motive','method','time','place','flaw'],1):hooks[name]=hk(f"quizTarget !== null && quizStep >= {i} && document.querySelector('#endTitle')?.textContent !== '凶手，不止一人'")
hooks.update(caught=hk("document.querySelector('#screenEnd')?.style.display==='block' && document.querySelector('#endTag')?.textContent==='🏆 通关' && quizStep===5"),genuine=hk("document.querySelector('#endTag')?.textContent==='🏆 通关' && quizTarget===state.killer && quizStep===5"),bypass=hk("document.querySelector('#endTag')?.textContent==='🏆 通关' && quizTarget!==state.killer && quizStep===5"),twist=hk("document.querySelector('#screenEnd')?.style.display==='block' && document.querySelector('#endTitle')?.textContent==='凶手，不止一人'"),failed=hk("state.lockedAccuse.length>0"))
for reason,text in [('timeup','倒计时归零的那一刻'),('stir','死因：打草惊蛇'),('alert','死因：警觉值爆表')]:hooks[reason]=hk("document.querySelector('#screenEnd')?.style.display==='block' && document.querySelector('#endTag')?.textContent==='💀 死亡' && document.querySelector('#endBody')?.textContent.includes("+json.dumps(text,ensure_ascii=False)+")")
write(J/'judge.json',{'hooks':hooks,'checkpoints':[{'id':n,'hook':n,'op':'truthy'} for n in ['motive','method','time','place','flaw']],'events':{k:{'hook':k,'op':'truthy'} for k in ['genuine','bypass','twist','failed','timeup','stir','alert']},'routes':[{'id':'caught','gates':['motive','method','time','place','flaw'],'ending':{'hook':'caught','op':'truthy'}}]})
write(J/'checkpoint-spec.json',{'critical_reasoning_points':['motive','method','time','place','flaw'],'conditions':'Five consecutive exact-text choices in quizFor target. Each locks when quizStep advances; failure does not increment. No collection or toast points. Prior correct answers remain latched on later failure.','route':'caught is original formal win, no tier invented. genuine/bypass separate diagnostic events. twist is post-win forced death continuation.','known_exploit':'answerQuiz never verifies target===killer. Person panel allows accusation with 2 notes while main list requires 5. This task is not approved for formal reasoning scoring.','not_observable':'die default wrong accusation branch has no caller in original; cannot claim UI coverage.'})
write(J/'flow.json',{'characters':18,'random':'uniform killer and different ally, shuffled choices; runtime seeding not injected','scenarios':['电梯事故','下毒','坠楼'],'scene_items':7,'mislead_rules':4,'timed_chat_triggers':['after40seconds','remaining30min','remaining10min'],'failures':['quiz wrong => distrust+lock; game continues','killer hot question => stir death','alert 5 => alert death','timeout => death','post-win confirmation => twist death'],'reset':'reload/new context starts round1; next button only removes disabled localStorage keys and fails to reset in-memory killer/scenario/alert/deadline. Consecutive rounds are defective.','unreachable_branch':'die(reason default) no UI caller; no terminal voluntary exit except harness give_up','modes':{'default_seconds':3600,'source_test_seconds':90}})
write(P/'provenance.json',{'record_id':'base664:0361','task_id':T,'source_url':c['model_visible']['title'] and 'https://8a065c332599425bb494a9444eebdccb.app.workbuddy.link/','source_snapshot':'ARG-packs/verify-416/bodies/361.html','source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'mirror_sha256':hashlib.sha256((P/'mirror/index.html').read_bytes()).hexdigest(),'modifications':[],'external_dependencies':[],'missing_soft_asset':{'path':'收款码.jpg','purpose':'optional donation dialog; not game clue','retained_reference':True},'account_requirement':'none','live_parity':'not verified'})
(P/'README.md').write_text('''# 60分钟 再死一次

原样冻结 base664:0361，无账号。仅托管 tasks/liushi-fenzhong/mirror。
Python3.11+，requirements.txt依赖，Playwright Chromium或已安装Edge/Chrome为外部运行环境。
手动：python scripts/serve_static.py --root tasks/liushi-fenzhong/mirror --port 8811
入口 http://127.0.0.1:8811/index.html；Ctrl+C停止；刷新或新context完全重置。
脚本冒烟：python scripts/run_one.py --config configs/liushi-fenzhong.json --policy script
私有验收：python judge/liushi-fenzhong/verify_sample.py --port 8812
原作?test将每轮3600秒改90秒，实时时钟不加速；测试报告明确区分。游戏源码不改动。
完整评测包包含私有裁判，不可托管包根。资源包只含原作HTML。捐款收款码图片缺失，不影响游戏逻辑。
五问全对即可通关而不验证嫌疑人，且next重启内存不完整，故工程验证与正式适用性分开；不推荐正式推理计分。
''',encoding='utf-8')
print('prepared',T)
