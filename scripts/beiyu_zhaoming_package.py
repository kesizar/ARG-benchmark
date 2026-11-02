from pathlib import Path
import json,hashlib,zipfile,importlib.util,threading,functools,http.server
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];T=R/'tasks/beiyu-zhaoming';O=R/'runs/beiyu-zhaoming';J=R/'judge/beiyu-zhaoming';P=R/'packs'
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 save(T/'provenance.json',{'record_id':'base664:0377','title':'北榆市昭明中学？','entry':'https://starsemmm.github.io/beiyuarg/index.html','repository':'https://github.com/starsemmm/beiyuarg','commit':'050a185439faaaf893f654f4d49b49f0481d2aaa','retrieved':'2026-10-27','upstream_zip_sha256':sha(T/'upstream.zip'),'patches':[],'runtime_layer':'L1','account_requirement':'none','resources_complete':False,'missing':['images/刘子轩.png','images/吴敏教研.png'],'external_dependencies':[]})
 (T/'README.md').write_text('''# 北榆市昭明中学？：原作恢复审计

base664:0377，公开仓库原样保存；不是正式可计分 prepared 数据。需要 Python 3.11、Playwright 及 Edge 或 Chromium。无账号、无付费 API。

从包根执行 `python scripts/serve_static.py --root tasks/beiyu-zhaoming/mirror --port 8821`，打开 http://127.0.0.1:8821/index.html 。仅托管 mirror，不托管 judge/configs/runs。以新浏览器 context 重置 localStorage 的 visited_whr1/visited_zyy1/visited_zjg1 及 sessionStorage 的 visited_monitor/report_case_no。停止方式为结束该服务器进程。

两头像原站404，未臆造补图。含附件及查看说明调用未定义 toggleCipher；保留原始缺陷。原作仅有三人物访问锁和举报非空校验；错误学校及无关教师也能推进同一终局。监控查询按钮无处理，base64 内含 cipher_placeholder，无可验证谜题答案。资料检索、点击展开和逐行叙事仅为诊断，不计推理分。唯一明确“调查结束”在 fugao.html，无原作证据支持好/坏等级。

可见路径：首页导航/人物搜索→环境监测→归档→实验楼→监控→搜索王浩然或李思雨重定向资料汇编→三位人物简介→李思雨逐行叙事→按作者可见文件名手动打开 jiaotiju.html→举报→only_end.html逐行叙事→按作者可见文件名打开 fugao.html。该手动文件名导航是原作操作条件；默认禁用 goto 的评测动作无法覆盖后两跳，恢复配置仅用于工程检查。

ui-evidence.json 保留正常 UI 正负例、最终页前置失败、表单清空、全新context重置。源码仅用于裁判审计，不向玩家提供。独立 audit_judge.py 永远不把访问/终局显示记为推理解谜成功。恢复包的独立目录启动验证不代表跨平台验收或正式完成。
''',encoding='utf8')
 save(J/'checkpoint-spec.json',{'critical_checkpoints':[],'formal_scoring_ready':False,'diagnostics':['searching known/unknown names','monitor visit session redirect','three-profile localStorage visit gate','empty report browser validation','nonempty arbitrary report accepted','author-hinted manual filename navigation','original terminal page'],'branches':{'lsy1/only_end':'missing any of three profile visit flags -> alert and index redirect','report':'empty school/teacher rejected; any nonempty teacher and selected school accepted','ending':'one explicit ending fugao.html; directly accessible without prerequisites'},'defects':['undefined toggleCipher in env_monitor and monitor_archive','inert monitor query controls','clue_dossier search input handler references localStorage visited_monitor whereas other pages use sessionStorage','two portrait paths missing and live404'],'tier':'unclassified'})
 cfg=json.loads((R/'configs/wuluo-cun.json').read_text(encoding='utf8'));cfg.update({'id':'beiyu-zhaoming','model_visible':{'title':'北榆市昭明中学？（恢复检查）','intro':'此恢复版本不用于正式计分。只根据屏幕可见信息探索站点；作者提示具体文件名时可导航同源页面。'},'entry_url':'http://127.0.0.1:8821/index.html','judge_path':'judge/beiyu-zhaoming/judge.json','policy_script':[{'op':'give_up'}],'allow_hosts':['127.0.0.1:8821'],'allow_model_goto':True,'goto_scope':'same_host','account_requirement':'none','notes_for_report':['RESOURCE RECOVERY ONLY; formal scoring ineligible; missing original portraits and no verified answer-validation gates.']});cfg['local_serve'].update({'command':['python','scripts/serve_static.py','--root','tasks/beiyu-zhaoming/mirror','--port','8821'],'ready_url':cfg['entry_url'],'port':8821});cfg['actions_enabled'].append('goto');save(R/'configs/beiyu-zhaoming-recovery.json',cfg)
 save(J/'judge.json',{'hooks':{},'checkpoints':[],'notes':'No ending success hook: raw terminal page is directly accessible and does not prove reasoning. Non-scoring recovery only.'})
 spec=importlib.util.spec_from_file_location('audit',J/'audit_judge.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 cases=[('fresh','/index.html','',{}),('forged-shortcut','/fugao.html','调查结束，你查明了事情的真相，仅此而已',{}),('visited','/fugao.html','调查结束，你查明了事情的真相，仅此而已',{'visited_'+n:'1' for n in ['whr1','zyy1','zjg1']})];judged=[{'case':name,'result':m.evaluate(u,t,s)} for name,u,t,s in cases];assert all(not x['result']['success'] and x['result']['critical_checkpoints_reached']==0 for x in judged);save(O/'judge-tests.json',judged)
 common=[p for p in (T/'mirror').rglob('*') if p.is_file()]+[T/'README.md',T/'provenance.json',R/'scripts/serve_static.py']
 extra=[T/'upstream.zip',R/'configs/beiyu-zhaoming-recovery.json']+[p for p in J.iterdir() if p.is_file()]+[R/'scripts'/s for s in ['beiyu_zhaoming_prepare.py','beiyu_zhaoming_livecheck.py','beiyu_zhaoming_package.py']]+[p for p in O.iterdir() if p.is_file() and p.name not in {'packages.json','deployment.json'}]
 packages=[];P.mkdir(exist_ok=True)
 for kind,files in [('resources-recovery',common),('evidence-recovery',common+extra)]:
  archive=P/f'beiyu-zhaoming.{kind}.zip';manifest=[{'path':p.relative_to(R).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(set(files))]
  with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
   for p in sorted(set(files)):z.write(p,p.relative_to(R).as_posix())
   z.writestr('RECOVERY-STATUS.json',json.dumps({'record_id':'base664:0377','formal_scoring_ready':False,'files':manifest},ensure_ascii=False,indent=2))
  dest=O/('unpacked-'+kind)
  with zipfile.ZipFile(archive) as z:z.extractall(dest)
  for f in manifest:assert sha(dest/f['path'])==f['sha256']
  packages.append({'kind':kind,'path':archive.relative_to(R).as_posix(),'sha256':sha(archive),'bytes':archive.stat().st_size,'unpacked_root':str(dest),'file_hashes_verified':len(manifest)})
 save(O/'packages.json',packages)
 # Two separate extraction roots, new server ports and browser contexts.
 servers=[];smokes=[]
 class Quiet(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*a):pass
 with sync_playwright() as pw:
  browser=pw.chromium.launch(channel='msedge',headless=True)
  for item,port in zip(packages,[8822,8823]):
   root=Path(item['unpacked_root'])/'tasks/beiyu-zhaoming/mirror';server=http.server.ThreadingHTTPServer(('127.0.0.1',port),functools.partial(Quiet,directory=str(root)));threading.Thread(target=server.serve_forever,daemon=True).start();servers.append(server)
   context=browser.new_context();page=context.new_page();page.goto(f'http://127.0.0.1:{port}/index.html');page.locator('#searchInput').fill('线索');page.get_by_role('button',name='搜索',exact=True).click();assert page.url.endswith('clue_dossier.html');page.locator('a[href="whr1.html"]').click();assert '正常反应' in page.locator('body').inner_text();page.screenshot(path=str(O/f'deploy-{port}.png'));smokes.append({'package':item['path'],'port':port,'independent_root':str(root),'new_context':True,'visible_search_and_profile':True});context.close()
  save(O/'deployment.json',smokes);browser.close()
 for s in servers:s.shutdown()
 print('Two recovery packages independently deployed, hashes verified.')
if __name__=='__main__':main()
