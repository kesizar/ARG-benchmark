from pathlib import Path
import json,shutil,difflib,hashlib
R=Path(__file__).resolve().parents[1];T='qingmiao-zhongxue';D=R/'tasks'/T; E=D/'evidence'
probe=json.loads((E/'resource-probe.json').read_text(encoding='utf-8'))
changes=[]
for p in (D/'original').rglob('*'):
 if not p.is_file():continue
 rel=p.relative_to(D/'original');dst=D/'mirror'/rel;dst.parent.mkdir(parents=True,exist_ok=True)
 b=p.read_bytes()
 if p.suffix in ['.html','.css','.js'] or p.name=='css2':
  before=b.decode('utf-8');after=before
  for host in ['qingmiaomiddleschool.github.io','i.ibb.co','i.postimg.cc','cdnjs.cloudflare.com','fonts.googleapis.com','fonts.gstatic.com']:
   after=after.replace('https://'+host+'/', '/'+host+'/')
  if rel.as_posix()=='qingmiaomiddleschool.github.io/404-ymail.com/index.html':
   # Original URLs are text-only; normal browser users copy them to another tab.
   # Preserve that navigation affordance for the bounded action interface.
   after=after.replace('content.innerHTML = contentText;', '''contentText = contentText.replace(/(\\/qingmiaomiddleschool\\.github\\.io\\/[A-Za-z0-9_.\\/-]+)/g, '<a href="$1" target="_blank">$1</a>');
            content.innerHTML = contentText;''')
  if rel.as_posix()=='qingmiaomiddleschool.github.io/Official-Site/index.html':
   link='/qingmiaomiddleschool.github.io/Hospital-Ingenium/'
   after=after.replace('校医院官网链接：'+link, '校医院官网链接：<a href="'+link+'" target="_blank">'+link+'</a>')
  if rel.as_posix()=='qingmiaomiddleschool.github.io/Lin-You-s-Blog/index.html':
   # Original malformed avatar path appends a label to an existing asset.
   import re
   after=re.sub(r'images/tx\.png=[^\"\'<>]+', 'images/tx.png', after)
  if before!=after:changes.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='original/'+rel.as_posix(),tofile='mirror/'+rel.as_posix()))
  b=after.encode('utf-8')
 dst.write_bytes(b)
(E/'localization.diff').write_text(''.join(changes),encoding='utf-8')
cfgpath=R/'configs'/f'{T}.json'
if not (E/'legacy-config.json').exists():shutil.copy2(cfgpath,E/'legacy-config.json');shutil.copy2(R/'judge'/T/'judge.json',E/'legacy-judge.json')
c=json.loads(cfgpath.read_text(encoding='utf-8'));c.update(runtime_layer='L1',account_requirement='none',entry_url='http://127.0.0.1:8811/qingmiaomiddleschool.github.io/Start-Game-/',allow_hosts=['127.0.0.1:8811'],actions_enabled=['click','dblclick','type','key','scroll','drag','back','wait','dialog','switch_tab','close_tab','give_up'],limits={'max_steps':650,'max_seconds':7200,'max_answer_submits':20})
c['local_serve']={'enabled':True,'command':['python','scripts/serve_static.py','--root',f'tasks/{T}/mirror','--port','8811'],'cwd':'.','ready_url':c['entry_url'],'ready_timeout_s':30,'port':8811}
c['notes_for_report']=['原始无账号静态作品，本地化五站页面与图像/字体。仅把原文字URL改为可点击新标签链接；答案、验证、动画及状态逻辑保持原作。','源码存在结局短语绕过前序流程；两个原作结局按画面记录，研究准备结论独立于通关。裁判另记提交后锁存的可选推理点。']
cfgpath.write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf-8')
manifest=[]
for p in sorted((D/'mirror').rglob('*')):
 if p.is_file():manifest.append({'path':p.relative_to(D/'mirror').as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(D/'provenance.json').write_text(json.dumps({'record_id':'base664:0057','original_entry':'https://qingmiaomiddleschool.github.io/Start-Game-/','account_requirement':'none','changes':'evidence/localization.diff','files':manifest},ensure_ascii=False,indent=2),encoding='utf-8')
print(len(manifest),'files localized')
