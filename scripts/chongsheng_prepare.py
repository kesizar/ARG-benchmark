"""Produce explicitly incomplete, non-scoring recovery artifacts for base664:0386."""
from pathlib import Path
import json,hashlib,shutil,zipfile,re,threading,functools,http.server,platform
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];T=R/'tasks/chongsheng';M=T/'mirror';J=R/'judge/chongsheng';O=R/'runs/chongsheng';P=R/'packs'
def save(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 for d in [M,J,O,P]:d.mkdir(parents=True,exist_ok=True)
 shutil.copy2(R/'ARG-packs/verify-416/bodies/386.html',M/'index.html');(M/'assets').mkdir(exist_ok=True)
 shutil.copy2(R/'ARG-packs/mirrors-lite/scripts/416/386/0.js',M/'assets/index-MdzLVmuf.js')
 s=(M/'index.html').read_text(encoding='utf8');engine=(M/'assets/index-MdzLVmuf.js').read_text(encoding='utf8')
 refs=sorted(set(re.findall(r'(?:href|src)="(\./[^"<>]+)"',s)))
 refs += ['./game/config.txt','./game/scene/start.txt','./game/userStyleSheet.css']
 rows=[{'path':v,'exists':(M/v.removeprefix('./')).is_file()} for v in refs]
 snippets=[{'needle':n,'position':engine.find(n),'excerpt':engine[max(0,engine.find(n)-90):engine.find(n)+160]} for n in ['game/config.txt','game/scene/','start.txt']]
 save(O/'resource-audit.json',{'record_id':'base664:0386','references':rows,'engine_evidence':snippets,'closure_complete':False,'scenario_files_present':False,'missing_semantics':'No game/config.txt or scene scripts; generic engine cannot establish puzzle gates, narrative, failure branches or endings.','source_files':[{'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in M.rglob('*') if p.is_file()]})
 save(T/'provenance.json',{'record_id':'base664:0386','title':'重生','entry':'https://be-reborn.pages.dev/','retrieved_snapshot':'2026-10-23','snapshot_sha256':sha(M/'index.html'),'engine_sha256':sha(M/'assets/index-MdzLVmuf.js'),'patches':[],'resources_complete':False,'account_requirement':'unknown','network_evidence':'runs/chongsheng/network-recovery.json'})
 (T/'README.md').write_text('''# 重生：不完整恢复材料

base664:0386；原入口 https://be-reborn.pages.dev/ 。本包只保留历史 HTML 和 WebGAL 引擎，不含故事脚本、配置、样式和媒体，不是可玩的完整作品。2026-10-27 当前公开入口及关键资源请求返回403；不判断站点永久失效。不得使用引擎通用按钮、空白舞台、源码参数或伪造状态作为解谜成功。

恢复待办：从作者或可用原站取得 assets/index-CkOq6uhz.css、game/config.txt、game/scene/start.txt 及所有递归场景/媒体引用；确认访问及账号条件；再梳理真实推理点、全部流程/失败/支线/结局并独立实现裁判。未知结局不分好坏。

工程诊断：Python 3.11；python scripts/serve_static.py --root tasks/chongsheng/mirror --port 8831，浏览器打开 http://127.0.0.1:8831/index.html 。停止服务器进程即可；新浏览器 context 是恢复诊断的重置方式，实际原作重置未验收。仅托管 mirror，严禁托管 judge/configs/runs。正常界面目前不能进入有内容游戏。

资源恢复包只含原作已知资源与说明。证据恢复包另含配置、零分裁判、共享 harness 快照、审计和恢复脚本；它不是正式评测包。基础 Python/Playwright/Edge 环境另行安装，不随包附带。两份包分别解压启动验证资源缺失仍可复现，不代表全流程通过。无付费 API、无个人账号。
''',encoding='utf8')
 save(J/'judge.json',{'hooks':{},'checkpoints':[],'notes':'Non-scoring incomplete recovery: no recovered scenario, verified puzzle, or ending.'})
 (J/'audit_judge.py').write_text('def evaluate(*args, **kwargs):\n    return {"success": False, "critical_checkpoints_reached": 0, "ending": None, "reason": "missing original scenario; scoring disabled"}\n',encoding='utf8')
 save(J/'checkpoint-spec.json',{'formal_scoring_ready':False,'critical_checkpoints':[],'verified_endings':[],'ending_default_when_recovered':'normal absent source evidence','content_status':'unknown_missing_game_scenario','full_flow_and_failure_branches':'not_verifiable','negative_policy':'No URL, text, engine variable, or source credential is accepted as puzzle completion.'})
 cfg=json.loads((R/'configs/wuluo-cun.json').read_text(encoding='utf8'));cfg.update({'id':'chongsheng','model_visible':{'title':'重生（资源不完整诊断）','intro':'当前材料缺失剧情，只用于资源恢复诊断，不可正式计分。'},'entry_url':'http://127.0.0.1:8831/index.html','allow_hosts':['127.0.0.1:8831'],'judge_path':'judge/chongsheng/judge.json','account_requirement':'unknown','policy_script':[{'op':'give_up'}],'notes_for_report':['INCOMPLETE RECOVERY ONLY; no formal scoring or playable flow validated.']});cfg['local_serve'].update({'command':['python','scripts/serve_static.py','--root','tasks/chongsheng/mirror','--port','8831'],'port':8831,'ready_url':cfg['entry_url']});save(R/'configs/chongsheng-recovery.json',cfg)
 import importlib.util
 spec=importlib.util.spec_from_file_location('audit',J/'audit_judge.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 save(O/'judge-tests.json',[{'case':case,'result':mod.evaluate(case)} for case in ['fresh','forged success text','direct ending URL','forged engine state','reset']])
 common=[p for p in M.rglob('*') if p.is_file()]+[T/'README.md',T/'provenance.json',R/'scripts/serve_static.py']
 extra=[R/'configs/chongsheng-recovery.json']+[p for p in J.rglob('*') if p.is_file() and '__pycache__' not in str(p)]+[p for p in (R/'harness').rglob('*') if p.is_file() and '__pycache__' not in str(p)]+[R/'scripts/chongsheng_recover.py',R/'scripts/chongsheng_prepare.py',O/'network-recovery.json',O/'resource-audit.json',O/'judge-tests.json']
 packages=[]
 for kind,files in [('resources-recovery',common),('evaluation-recovery',common+extra)]:
  archive=P/f'chongsheng.{kind}.zip';manifest=[{'path':p.relative_to(R).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(set(files))]
  with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
   for p in sorted(set(files)):z.write(p,p.relative_to(R).as_posix())
   z.writestr('RECOVERY-STATUS.json',json.dumps({'record_id':'base664:0386','ready_for_local_execution':False,'ready_for_formal_scoring':False,'files':manifest},indent=2))
  dest=O/('unpacked-'+kind)
  with zipfile.ZipFile(archive) as z:assert z.testzip() is None;z.extractall(dest)
  assert all(sha(dest/f['path'])==f['sha256'] for f in manifest)
  packages.append({'kind':kind,'path':archive.relative_to(R).as_posix(),'sha256':sha(archive),'bytes':archive.stat().st_size,'unpacked_root':str(dest),'verified_files':len(manifest)})
 save(O/'packages.json',packages)
 deployments=[]
 class Quiet(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*a):pass
 with sync_playwright() as pw:
  browser=pw.chromium.launch(channel='msedge',headless=True)
  for package,port in zip(packages,[8832,8833]):
   root=Path(package['unpacked_root'])/'tasks/chongsheng/mirror';server=http.server.ThreadingHTTPServer(('127.0.0.1',port),functools.partial(Quiet,directory=str(root)));threading.Thread(target=server.serve_forever,daemon=True).start()
   context=browser.new_context(viewport={'width':1366,'height':900});page=context.new_page();errors=[];responses=[]
   page.on('pageerror',lambda e:errors.append(str(e)));page.on('response',lambda r:responses.append({'url':r.url,'status':r.status}))
   page.goto(f'http://127.0.0.1:{port}/index.html');page.wait_for_timeout(2000)
   body=page.locator('body').inner_text();buttons=page.get_by_role('button').all_text_contents();actions=[]
   page.mouse.click(683,450);page.wait_for_timeout(600);actions.append('click visible initial screen')
   for label in ['简体中文','开始游戏']:
    try:
     page.get_by_text(label,exact=True).first.click(timeout=1500);page.wait_for_timeout(500);actions.append('clicked '+label)
    except Exception as exc:actions.append({'attempt':label,'error':str(exc)[:250]})
   page.screenshot(path=str(O/f'deploy-{port}.png'))
   before={'initial_text':body,'initial_buttons':buttons,'normal_ui_actions':actions,'after_start_text':page.locator('body').inner_text()};page.reload();page.wait_for_timeout(500)
   deployments.append({'package':package['path'],'port':port,'root':str(root),'new_context':True,'server_only_mirror':True,'visible':before,'http_errors':[r for r in responses if r['status']>=400],'page_errors':errors,'reload_attempted':True,'actual_game_reset_verified':False,'full_flow_passed':False})
   context.close();server.shutdown()
  browser.close()
 save(O/'deployment.json',deployments)
 save(O/'acceptance.json',{'status':'blocked_resource_closure','ready_for_local_execution':False,'ready_for_formal_scoring':False,'package_hashes_crc_and_extraction_verified':True,'two_independent_diagnostic_deployments_verified':True,'game_flow_success':False,'negative_judge_tests':5,'actual_game_reset':'not_reachable','python':platform.python_version(),'browser':'installed Edge via Playwright','dependencies_not_bundled':True,'no_paid_api':True})
 save(R/'data/preparation/results/base664-0386.json',{'record_id':'base664:0386','task_id':'chongsheng','title':'重生','status':'HANDOFF_resource_blocked','runtime_layer':'L1','account_requirement':'unknown','ready_for_local_execution':False,'ready_for_formal_scoring':False,'resource_status':'incomplete_html_and_engine_only; critical_config_scene_css_media_unrecovered; origin_403','integration_status':'diagnostic_config_only; not_playable','flow_status':'unverified_no_original_scene_scripts','judge_status':'independent_zero_score_recovery_guard; no_puzzle_points_invented','delivery_status':'two_recovery_packages_independent_diagnostic_deployments_hash_verified','content_status':'blocked_story_puzzles_routes_endings_unknown','resources_bundle':'packs/chongsheng.resources-recovery.zip','evaluation_bundle':'packs/chongsheng.evaluation-recovery.zip','deployment_evidence':'runs/chongsheng/deployment.json','acceptance':'runs/chongsheng/acceptance.json','resource_audit':'runs/chongsheng/resource-audit.json','network_evidence':'runs/chongsheng/network-recovery.json','provenance':'tasks/chongsheng/provenance.json','checkpoint_spec':'judge/chongsheng/checkpoint-spec.json','model_api_used':False,'limitations':['403 indicates current access failure, not proven permanent site death.','No verified story, reasoning gates, full UI routes, endings, failure branches or original reset.','Bundles preserve recovery evidence only; neither is a complete playable game.','Installed Windows Python/Edge used; no clean OS installation verified.'],'next_action':'Recover original game config/start scene plus recursive assets from author/accessible origin, then audit content and implement actual judge before full acceptance.'})
 print('HANDOFF: base664-0386 resource-blocked; two recovery bundles and deployment evidence saved.')
if __name__=='__main__':main()
