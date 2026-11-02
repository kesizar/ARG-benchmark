"""Prepare an offline revision, preserving puzzle decisions."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
PUB=ROOT/'tasks/baoya/mirror'; PRIVATE=ROOT/'judge/baoya/source'
PRIVATE.mkdir(parents=True,exist_ok=True)
changes=[]
for p in sorted(PUB.iterdir()):
    if not p.is_file() or p.suffix not in ['.html','.css','.js','.pdf','.md']:continue
    original=PRIVATE/p.name
    if not original.exists():original.write_bytes(p.read_bytes())
    if p.suffix not in ['.html','.css']:continue
    text=original.read_text(encoding='utf-8')
    text,n=re.subn(r'<link\b[^>]*https://fonts\.googleapis\.com[^>]*>','<!-- Offline typography uses the original CSS fallback fonts. -->',text,flags=re.I)
    if n:changes.append({'file':p.name,'type':'external_font_stylesheet_removed','count':n,'effect':'Uses existing CSS fallback fonts; puzzle text unchanged'})
    text,n=re.subn(r"@import\s+url\((['\"])https://fonts\.googleapis\.com[^'\"]+\1\)\s*;",'',text)
    if n:changes.append({'file':p.name,'type':'external_font_import_removed','count':n})
    if p.name=='index.html':
        text,n=re.subn(r'<script async src="https://www\.googletagmanager\.com[^>]*></script>\s*<script>.*?</script>','',text,flags=re.S)
        text,k=re.subn(r'<img src="https://visitor-badge\.laobi\.icu[^>]*>','<!-- External visitor badge omitted from the offline revision. -->',text)
        changes.append({'file':p.name,'type':'analytics_and_visitor_badge_removed','count':n+k})
    if p.name=='junjunnainai.html':
        old='downloadBtn.addEventListener("click", downloadPDF);'
        assert old in text
        text=text.replace(old,'if (downloadBtn && typeof downloadPDF === "function") downloadBtn.addEventListener("click", downloadPDF);')
        changes.append({'file':p.name,'type':'guard_missing_legacy_download_button','effect':'Prevents exception after invitation renders; no new clue invented'})
    p.write_text(text,encoding='utf-8',newline='\n')
files=[{'path':p.relative_to(PUB).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(PUB.rglob('*')) if p.is_file()]
(ROOT/'tasks/baoya/provenance.json').write_text(json.dumps({'record_id':'base664:0032','source_url':'https://wanwuyongyuan.github.io/baoya/','existing_material_origin':'Existing local snapshot attributed to public repository wanwuyongyuan/baoya; no claim of live revision equality','changes':changes,'files':files,'account_requirement':'none; logins are fictional client-side puzzle controls','notes':['Unlinked wushan.js, alert-timer.js and prototype files are retained source artifacts, not active game logic.','Originals under judge/baoya/source are not served.']},ensure_ascii=False,indent=2),encoding='utf-8')
p=ROOT/'configs/baoya.json';c=json.loads(p.read_text(encoding='utf-8'));c['entry_url']='http://127.0.0.1:8811/index.html';c['allow_hosts']=['127.0.0.1:8811'];c['local_serve'].update(port=8811,ready_url=c['entry_url']);c['local_serve']['command'][-1]='8811';c['account_requirement']='none';c['actions_enabled']+=['switch_tab','close_tab'];c['actions_enabled']=list(dict.fromkeys(c['actions_enabled']));c['limits']['max_steps']=240;c['settle_ms']=350;c['notes_for_report']=['本地虚构账号解谜，无真实账号依赖。打开页面、普通收集和QTE照抄仅记事件；两条结局均记录，暂不擅自评好坏。'];p.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
hooks={}
def page(id,name,selector):hooks[id]={'type':'js_truthy','expr':f"location.pathname.endsWith('/{name}') && !!document.querySelector('{selector}')"}
for id,name in [('customer_login','junjunnainai.html'),('tian_login','stafftian.html'),('yu_login','staffyu.html'),('xu_login','staffxu.html'),('boss_login','emailwangbaoya.html')]:page(id,name,'h2' if id=='customer_login' else 'h1')
hooks['secret_login']={'type':'js_truthy','expr':"location.pathname.endsWith('/staffyujiamiyouxiang.html') && !!document.querySelector('.email-item')"}
hooks['code_sequence']={'type':'js_truthy','expr':"location.pathname.endsWith('/game1.html') && document.querySelector('#hintBox')?.textContent.includes('验证通过')"}
hooks['caesar_key']={'type':'dom_regex','pattern':'成功登入，欢迎回来。'}
hooks['qte_copy']={'type':'dom_regex','pattern':'判定成功！'}
page('dawn','choice2.html','h1');page('sacrifice','choice1.html','h1')
critical=['boss_login','code_sequence'];optional=['customer_login','tian_login','yu_login','xu_login','secret_login','caesar_key']
j={'hooks':hooks,'checkpoints':[{'id':id,'hook':id,'op':'truthy','role':'critical' if id in critical else 'optional'} for id in critical+optional],'events':{'qte_copy':{'hook':'qte_copy','op':'truthy'}},'routes':[{'id':id,'tier':'normal','gates':critical,'ending':{'hook':id,'op':'truthy'}} for id in ['dawn','sacrifice']],'ending':None,'answer_hash_file':None,'request_milestones':[],'submit_conclusion':{'enabled':False,'schema':None},'rubric_path':None}
(ROOT/'judge/baoya/judge.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('prepared_files',len(files),'points',len(critical+optional))
