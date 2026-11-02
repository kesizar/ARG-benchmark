"""Prepare the existing public mirror without changing puzzle acceptance rules."""
from pathlib import Path
import hashlib,json,re,subprocess
ROOT=Path(__file__).resolve().parents[1]
PUB=ROOT/'tasks/gongwei-404/mirror'
PRIVATE=ROOT/'judge/gongwei-404/source'

def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    PRIVATE.mkdir(parents=True,exist_ok=True)
    changes=[]
    def edit(name,fn,reason):
        p=PUB/name; original=PRIVATE/name
        if not original.exists():original.write_bytes(p.read_bytes())
        before=original.read_text(encoding='utf-8');after=fn(before)
        p.write_text(after,encoding='utf-8',newline='\n')
        changes.append({'file':name,'reason':reason,'original_sha256':sha(original.read_bytes()),'prepared_sha256':sha(p.read_bytes())})
    def telemetry(s):
        return re.sub(r'\s*fetch\("https://script\.google\.com/.*?\.catch\(err => console\.error\("记录失败:", err\)\);','\n    // Offline: author analytics request removed; search logic is unchanged.',s,flags=re.S)
    edit('desk.html',telemetry,'Remove non-gameplay external search telemetry; preserve exact search lookup logic')
    edit('index.html',lambda s:re.sub(r'<script[^>]+src=["\'][^"\']*busuanzi[^"\']*["\'][^>]*>\s*</script>','',s,flags=re.I),'Remove external page-view analytics only')
    edit('bank.html',lambda s:re.sub(r'<img\b[^>]*src=["\']placeholder_ad\.jpg["\'][^>]*>','',s,flags=re.I),'Remove missing decorative advertisement image; no puzzle content')
    edits={
      'mailbox.html':('if (email === CORRECT_EMAIL && password === CORRECT_PASSWORD) {','mailbox_login'),
      'weibo.html':('if (enteredUsername === correctUsername && enteredPassword === correctPassword) {','weibo_login'),
      'wangpan.html':('if (enteredPassword === correctPassword) {','recording_unlock'),
      'qyskoa.html':('if (enteredUsername === correctUsername && enteredPassword === correctPassword) {','oa_login'),
      'changyuan.html':('if (name === CORRECT_NAME && card === CORRECT_CARD_LAST_FOUR) {','financial_unlock')}
    for name,(needle,ident) in edits.items():
        def patch(s,needle=needle,ident=ident):
            assert s.count(needle)==1,(name,needle)
            return s.replace(needle,needle+f'\n                try {{ localStorage.setItem("benchmark_gongwei_{ident}", "1"); }} catch (_) {{}}',1)
        edit(name,patch,'Add evaluator-only success marker inside existing successful validation branch; no acceptance, navigation or UI changes')
    css=PUB/'assets/fontawesome/css/all.min.css';css.parent.mkdir(parents=True,exist_ok=True)
    base='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/'
    def get(url,dest):
        dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists():return
        r=subprocess.run(['curl.exe','--fail','--location','--silent','--show-error','--max-time','30','--output',str(dest),url],capture_output=True,text=True)
        if r.returncode:raise RuntimeError(r.stderr[:200])
    get(base+'css/all.min.css',css)
    asset_sources=[{'file':str(css.relative_to(PUB)),'source_url':base+'css/all.min.css'}]
    for rel in sorted(set(re.findall(r'url\(["\']?([^\)"\']+)',css.read_text(encoding='utf-8')))):
        if rel.startswith('data:'):continue
        dest=(css.parent/rel).resolve();assert dest.is_relative_to(PUB.resolve())
        suffix='webfonts/'+dest.name;get(base+suffix,dest)
        asset_sources.append({'file':str(dest.relative_to(PUB)),'source_url':base+suffix})
    edit('changyuan.html',lambda s:s.replace('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css','assets/fontawesome/css/all.min.css').replace('if (name === CORRECT_NAME && card === CORRECT_CARD_LAST_FOUR) {','if (name === CORRECT_NAME && card === CORRECT_CARD_LAST_FOUR) {\n                try { localStorage.setItem("benchmark_gongwei_financial_unlock", "1"); } catch (_) {}',1),'Localize unchanged FontAwesome stylesheet and preserve success marker')
    edit('intro.html',lambda s:s.replace('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css','assets/fontawesome/css/all.min.css'),'Localize unchanged FontAwesome stylesheet in school-information page')
    files=[{'file':str(p.relative_to(PUB)),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(PUB.rglob('*')) if p.is_file() and p.name!='.DS_Store']
    (ROOT/'tasks/gongwei-404/provenance.json').write_text(json.dumps({'record_id':'base664:0003','source_url':'https://xsn1204.github.io/qmgame/','input_revision':'Existing repository mirror; upstream revision not established; changed original files preserved under judge/gongwei-404/source','changes':changes,'downloaded_assets':asset_sources,'files':files},ensure_ascii=False,indent=2),encoding='utf-8')
    cpath=ROOT/'configs/gongwei-404.json';c=json.loads(cpath.read_text(encoding='utf-8'));c['entry_url']='http://127.0.0.1:8821/index.html';c['allow_hosts']=['127.0.0.1:8821'];c['local_serve'].update({'port':8821,'ready_url':c['entry_url']});cmd=c['local_serve']['command'];cmd[cmd.index('--port')+1]='8821';c['allow_model_goto']=True;c['goto_scope']='same_host';c['actions_enabled']=list(dict.fromkeys(c['actions_enabled']+['goto']));c['account_requirement']='none';c['limits']['max_steps']=160;c['notes_for_report']=['游戏账号是本地剧情谜题，不是真实服务账号。笔记含字面网址，允许站内地址栏导航。外部搜索遥测已移除；解锁成功分支添加仅供裁判读取的标记。'];cpath.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('prepared_files',len(files),'font_assets',len(asset_sources))
if __name__=='__main__':main()
