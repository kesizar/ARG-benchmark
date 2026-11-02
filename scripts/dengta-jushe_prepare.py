from pathlib import Path
import re,json,difflib,hashlib
R=Path('.');T=R/'tasks/dengta-jushe';J=R/'judge/dengta-jushe';J.mkdir(exist_ok=True);(T/'mirror').mkdir(exist_ok=True)
s=(R/'runs/dengta-jushe/frame-1.html').read_text(encoding='utf8');(T/'original/embedded-game.html').write_text(s,encoding='utf8')
t=re.sub(r'<script[^>]*src="https://static.cloudflareinsights.com/.*?</script>','',s,flags=re.S);(T/'mirror/index.html').write_text(t,encoding='utf8');(T/'compatibility.diff').write_text(''.join(difflib.unified_diff(s.splitlines(True),t.splitlines(True),fromfile='original/embedded-game.html',tofile='mirror/index.html')),encoding='utf8')
c=json.loads((R/'configs/wuluo-cun.json').read_text(encoding='utf8'));c.update(id='dengta-jushe',account_requirement='none',entry_url='http://127.0.0.1:8811/index.html',judge_path='judge/dengta-jushe/judge.json',model_visible={'title':'灯塔剧社戏单档','intro':'选择自力模式，调查缺失的第六场戏单并复原，观看庆生彩排。可选挑战：完成后台对词练习。只根据屏幕与站内材料推理。'},allow_hosts=['127.0.0.1:8811'],notes_for_report=['L1 recovered from live Edge iframe. Challenge mode required; page visits, ticket stamps and clue pins are diagnostic only. One unranked original ending.'])
c['local_serve'].update(command=['python','scripts/serve_static.py','--root','tasks/dengta-jushe/mirror','--port','8811'],port=8811,ready_url=c['entry_url']);(R/'configs/dengta-jushe.json').write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf8')
base='(()=>{try{const s=JSON.parse(localStorage.getItem("lighthouse-theater-save-v1"));return !!s && s.hintMode===false && (%s)}catch{return false}})()'
exprs={'login':'s.backstageUnlocked===true','reconstruction':'s.backstageUnlocked===true && s.reconstructed===true','cue_order':'s.backstageUnlocked===true && s.cueGameDone===true','ending':'s.backstageUnlocked===true && s.reconstructed===true && s.seenEnding===true && document.body.innerText.includes("—— 幕落 · 灯亮着 ——")'}
j={'hooks':{k:{'type':'js_truthy','expr':base%v} for k,v in exprs.items()},'checkpoints':[{'id':'login','hook':'login','op':'truthy'},{'id':'reconstruction','hook':'reconstruction','op':'truthy'},{'id':'cue_order','hook':'cue_order','op':'truthy','role':'optional'}],'routes':[{'id':'birthday-rehearsal','gates':['login','reconstruction'],'ending':{'hook':'ending','op':'truthy'}}],'events':{}}
(J/'judge.json').write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf8')
(J/'audit_judge.py').write_text('''def evaluate(state, text):
    challenge = state.get('hintMode') is False
    login = challenge and state.get('backstageUnlocked') is True
    reconstructed = login and state.get('reconstructed') is True
    return dict(login=login, reconstruction=reconstructed, optional_cue=login and state.get('cueGameDone') is True, success=reconstructed and state.get('seenEnding') is True and '—— 幕落 · 灯亮着 ——' in text)
''',encoding='utf8')
print('prepared')
