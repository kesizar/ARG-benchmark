from pathlib import Path
import json,re,shutil,hashlib,difflib
R=Path(__file__).resolve().parents[1];T='yiwu-yuren';J=R/'judge'/T;B=R/'tasks'/T;S=J/'source';M=B/'mirror';M.mkdir(exist_ok=True)
def wr(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
changes=[]
for p in S.rglob('*'):
 if not p.is_file():continue
 rel=p.relative_to(S);q=M/rel;q.parent.mkdir(parents=True,exist_ok=True);b=p.read_bytes()
 if p.suffix=='.html':
  old=b.decode('utf-8');s=old;prefix='../' if rel.parts[0]=='001' else ''
  s=s.replace('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css',prefix+'vendor/all.min.css')
  s=re.sub(r'<link[^>]+(?:fonts.googleapis.com|fonts.gstatic.com)[^>]*>','',s)
  if p.name=='youjian.html':s=s.replace('if (email === VALID_EMAIL && password === VALID_PASSWORD) {','if (false) { // Original referenced undefined credentials; recovery is the intended route.')
  if p.name=='zhuye.html':s=s.replace("location.href = 'index.html'","location.href = 'gongyuanyy.html'")
  if p.name=='yiyuan.html':s=s.replace('</form>','<div id="searchFeedback" class="search-feedback" aria-live="polite">请输入患者信息进行验证。</div></form>',1)
  q.write_text(s,encoding='utf-8')
  if s!=old:changes.append({'file':rel.as_posix(),'diff':''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='original/'+str(rel),tofile='mirror/'+str(rel)))})
 elif p.name=='all.min.css':q.write_bytes(b.replace(b'../webfonts/',b''))
 else:q.write_bytes(b)
wr(J/'compatibility-diffs.json',changes)
# Keep exact supplied snapshot separately: live source version differs.
shutil.copyfile(R/'ARG-packs/verify-416/bodies/268.html',J/'entry.historical.html')
c=json.loads((R/'configs/yanhuo.json').read_text(encoding='utf-8'));c.update(id=T,category='web_puzzle',runtime_layer='L1',account_requirement='none',entry_url='http://127.0.0.1:8811/001/window.html',allow_hosts=['127.0.0.1:8811'],judge_path=f'judge/{T}/judge.json')
c['model_visible']={'title':'遗物整理师 · 001 愚人节的短信','intro':'你已接下001愚人节的短信委托，正在调查沈沁的电脑。根据页面可见线索调查消息来源和死因，完成这件委托。首页其他独立委托不属于本任务范围。只使用本站界面。'}
c['local_serve']={'enabled':True,'command':['python','scripts/serve_static.py','--root',f'tasks/{T}/mirror','--port','8811'],'cwd':'.','ready_url':c['entry_url'],'ready_timeout_s':30,'port':8811};c['limits'].update(max_steps=400,max_seconds=3600);c['account']={'required':False,'reason':'Fictional local account recovery; no real account or submission.'};c['notes_for_report']=['Explicit case001 variant, entry at accepted commission desktop; cases002/003 are out of scope.','Live version fetched 2026-10-27; exact historical entry retained on evaluator side.','Removed remote font requests, vendored icons; fixed undefined ordinary email credential check to reject, preserving recovery path; fixed broken park-diary return fallback.','Ending tiers normal: original labels 1/2/3 do not establish benchmark good/bad tiers.','Step and time limits are engineering budgets, not model-calibrated.'];wr(R/'configs'/f'{T}.json',c)
hooks={}
for name,text in [('identity','你是陈屿。'),('intent','你只需要告诉我你这样做是为了什么。'),('killer','嫉妒她的周毅')]:hooks[name]={'type':'js_truthy','expr':f'location.pathname.endsWith("/001/xuesheng.html") && Array.from(document.querySelectorAll(".reply-item")).some(x=>x.textContent.includes({json.dumps(text,ensure_ascii=False)}))'}
choices=['该死','不该死','who cares？'];answers=['我觉得俩人一样该死','死亡对他这种人来说太轻了。','我不想毁了我的信誉 今天我就当没见过你']
for n,(choice,ans) in enumerate(zip(choices,answers),1):
 hooks[f'branch{n}']={'type':'js_truthy','expr':f'location.pathname.endsWith("/001/xuesheng.html") && !!document.querySelector("[data-final=true]") && Array.from(document.querySelectorAll(".reply-item")).some(x=>x.textContent.includes({json.dumps(ans,ensure_ascii=False)}))'}
 hooks[f'end{n}']={'type':'js_truthy','expr':f'location.pathname.endsWith("/001/jj{n}.html") && document.querySelector(".page-indicator")?.textContent.includes("结局{["一","二","三"][n-1]}")'}
 hooks[f'end{n}']['expr']+=' && !!window.opener && window.opener.location.pathname.endsWith("/001/xuesheng.html") && Array.from(window.opener.document.querySelectorAll("[data-fourth-choice]")).some(x=>x.dataset.fourthChoice==='+json.dumps(choice,ensure_ascii=False)+') && !!window.opener.document.querySelector("[data-final=true]")'
for name,path in [('wechat','weixin'),('outlook','mailbox'),('hospital','yiyuanjilu'),('teacher','zhigong')]:hooks[name]={'type':'js_truthy','expr':f'location.pathname.endsWith("/001/{path}.html")'}
hooks['completed']={'type':'js_truthy','expr':'location.pathname.endsWith("/index.html") && JSON.parse(localStorage.getItem("caseCompleted")||"[]")[0]===true'}
check=[{'id':n,'hook':n,'op':'truthy','role':'critical'} for n in ['identity','intent','killer','branch1','branch2','branch3']]+[{'id':n,'hook':n,'op':'truthy','role':'optional'} for n in ['wechat','outlook','hospital','teacher','completed']]
j={'hooks':hooks,'checkpoints':check,'events':{},'routes':[{'id':f'ending{n}','tier':'normal','gates':['identity','intent','killer',f'branch{n}'],'ending':{'hook':f'end{n}','op':'truthy'}} for n in range(1,4)],'ending':None,'answer_sha256':[],'answer_hash_file':None,'request_milestones':[],'submit_conclusion':{'enabled':False,'schema':None},'rubric_path':None};wr(J/'judge.json',j)
wr(B/'provenance.json',{'record_id':'base664:0268','task_id':T,'canonical_url':'https://liangd1129.github.io/relic1899/','version':'live case001 2026-10-27','scope':'001 only; desktop accepted commission entry; index/contact retained for original exit and replay','historical_sha256':hashlib.sha256((J/'entry.historical.html').read_bytes()).hexdigest(),'live_entry_sha256':hashlib.sha256((S/'index.html').read_bytes()).hexdigest(),'changes':'judge/yiwu-yuren/compatibility-diffs.json','asset_files':[{'path':p.relative_to(M).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(M.rglob('*')) if p.is_file()],'external_runtime_required':False,'account_requirement':'none','out_of_scope':['002','003','fictional university graduate external link (not case001 clue)']})
print('prepared',sum(p.is_file() for p in M.rglob('*')),'files')
