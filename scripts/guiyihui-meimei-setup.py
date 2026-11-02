from pathlib import Path
import json
root=Path('.'); task='guiyihui-meimei'; output=root/'judge'/task
base=json.loads((root/'configs/wuluo-cun.json').read_text(encoding='utf-8'))
base.update(id=task,category='arg',runtime_layer='L1',account_requirement='none',entry_url='http://127.0.0.1:8821/index.html',allow_hosts=['127.0.0.1:8821'],judge_path=f'judge/{task}/judge.json',model_visible={'title':'归一会：妹妹的升华日记','intro':'调查妹妹留下的平板，探索线索与结局。'},notes_for_report=['原作可跳关、提示和直接跳过；路线无必经谜题。独立裁判仅将有推理或互动证据的指定关卡记为计分点但不作结局必经，并排除提示及自动跳过。第10关自相矛盾，第47关设定存疑，均不计分。'])
base['local_serve'].update(command=['python','scripts/serve_static.py','--root',f'tasks/{task}/mirror','--port','8821'],ready_url=base['entry_url'],port=8821)
base['limits']={'max_steps':1500,'max_seconds':10800,'max_answer_submits':5}; (root/'configs'/f'{task}.json').write_text(json.dumps(base,ensure_ascii=False,indent=2),encoding='utf-8')
setup="""(()=>{if(!document.querySelector('#panel-level-indicator'))return false;if(!window.__benchGuiyi){const s=window.__benchGuiyi={solved:{},hints:{},skips:{},jumps:0,photo:false};document.addEventListener('click',e=>{if(!e.isTrusted)return;const b=e.target.closest('button');if(!b)return;const n=parseInt(document.querySelector('#panel-level-indicator').textContent);const a=b.getAttribute('onclick')||'';if(a.includes('toggleHint'))s.hints[n]=true;if(a.includes('skipLevelEpiphany'))s.skips[n]=true;if(b.closest('#levels-quick-nav'))s.jumps++;if(b.id==='btn-validate'){const before=n;setTimeout(()=>{let now=parseInt(document.querySelector('#panel-level-indicator').textContent);if(now===before+1&&!s.hints[before]&&!s.skips[before]&&(![21,22].includes(before)||s.photo))s.solved[before]=true;},0)}},true)}if(!document.querySelector("#win-photos").classList.contains("hidden") && document.querySelector("#hidden-rune-text").classList.contains("opacity-100"))window.__benchGuiyi.photo=true;return true})()"""
points={11:'十诫藏头',13:'等差时间推算',21:'照片滤镜显影',22:'符印序列',33:'GPS里程累加'}
hooks={'init':{'type':'js_truthy','expr':setup}}
for n in points: hooks[f'p{n}']={'type':'js_truthy','expr':f'!!window.__benchGuiyi?.solved[{n}]'}
for e in 'ABCD': hooks['ending_'+e]={'type':'js_truthy','expr':f"!document.querySelector('#ending-overlay').classList.contains('hidden') && document.querySelector('#ending-title').textContent.includes('结局 {e}')"}
hooks['hint']={'type':'js_truthy','expr':'!!window.__benchGuiyi && Object.keys(window.__benchGuiyi.hints).length>0'}
hooks['skip']={'type':'js_truthy','expr':'!!window.__benchGuiyi && Object.keys(window.__benchGuiyi.skips).length>0'}
hooks['jump']={'type':'js_truthy','expr':'!!window.__benchGuiyi && window.__benchGuiyi.jumps>0'}
judge={'hooks':hooks,'checkpoints':[{'id':f'p{n}','hook':f'p{n}','op':'truthy','description':v} for n,v in points.items()],'events':{x:{'hook':x,'op':'truthy'} for x in ['hint','skip','jump']},'terminal_failures':[{'id':'failure_timeout_A','hook':'ending_A','op':'truthy','tier':'bad','description':'倒计时耗尽，妹妹未获救；失败，不算通关'}],'routes':[{'id':'ending_'+e,'tier':'normal','gates':[],'ending':{'hook':'ending_'+e,'op':'truthy'}} for e in 'BCD']}
(output/'judge.json').write_text(json.dumps(judge,ensure_ascii=False,indent=2),encoding='utf-8')
(output/'checkpoint-spec.json').write_text(json.dumps({'selected_optional':points,'rationale':'原作允许跳关，非必经；选择仅为候选，需人工审题复核。提示或跳过本关后不予计分。','excluded':{'10':'题干和答案自相矛盾','47':'题设报警号码缺乏依据','choices':'叙事分支非推理门','other':'直接提取或翻译为主，尚未纳入候选'}},ensure_ascii=False,indent=2),encoding='utf-8')
print('created',task)
