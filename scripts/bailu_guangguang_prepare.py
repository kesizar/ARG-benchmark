from pathlib import Path
import re,json,hashlib,difflib
T=Path('tasks/bailu-guangguang');(T/'mirror').mkdir(exist_ok=True)
s=Path('runs/bailu-guangguang/frame-1.html').read_text(encoding='utf8');(T/'original/embedded-game.html').write_text(s,encoding='utf8')
t=re.sub(r'<script[^>]*src="https://static.cloudflareinsights.com/.*?</script>','',s,flags=re.S)
# Remove deployed analytics beacon only; inline game, styles and data images untouched.
(T/'mirror/index.html').write_text(t,encoding='utf8')
(T/'compatibility.diff').write_text(''.join(difflib.unified_diff(s.splitlines(True),t.splitlines(True),fromfile='original/embedded-game.html',tofile='mirror/index.html')),encoding='utf8')
c=json.load(open('configs/wuluo-cun.json',encoding='utf8'));c.update(id='bailu-guangguang',account_requirement='none',entry_url='http://127.0.0.1:8811/index.html',judge_path='judge/bailu-guangguang/judge.json',model_visible={'title':'白鹭观光局','intro':'选择不添加提示挑战模式，修复缺失路线，收集五枚彩蛋路标并发布志工感谢信。只根据界面与站内提供的查看源代码功能推理。'},allow_hosts=['127.0.0.1:8811'],policy_script=[{'op':'give_up'}],notes_for_report=['Original game recovered from live Arena iframe 2026-10-27. No paid model API used.'])
c['local_serve'].update(command=['python','scripts/serve_static.py','--root','tasks/bailu-guangguang/mirror','--port','8811'],port=8811,ready_url=c['entry_url']);Path('configs/bailu-guangguang.json').write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf8')
D=Path('judge/bailu-guangguang');D.mkdir(exist_ok=True)
exprs={'login':'s.loggedIn===true','republish':'s.republished===true',**{f'marker_{n}':f's.markers.includes("Y-{n}")' for n in range(1,6)},'ending':'s.ended===true && s.republished===true && s.loggedIn===true && [1,2,3,4,5].every(n=>s.markers.includes("Y-"+n))'}
hooks={k:{'type':'js_truthy','expr':'(()=>{try{const s=JSON.parse(localStorage.getItem("egret_bureau_save_v1"));return !!s && s.hintMode === \"off\" && ('+e+')}catch{return false}})()'} for k,e in exprs.items()}
j={'hooks':hooks,'checkpoints':[{'id':k,'hook':k,'op':'truthy'} for k in exprs if k!='ending'],'events':{},'routes':[{'id':'thank-you-letter','tier':'normal','gates':[k for k in exprs if k!='ending'],'ending':{'hook':'ending','op':'truthy'}}]}
j['checkpoints']=[dict(x,role='diagnostic') if x['id']=='republish' else x for x in j['checkpoints']]
j['routes'][0]['gates'].remove('republish')
for x in j['hooks'].values():
 x['expr']=x['expr'].replace('!!s && (','!!s && s.hintMode === \"off\" && (')
(D/'judge.json').write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf8')
print('mirror',len(t),'diff',s!=t)
