import hashlib,json,zipfile,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];tid='shenhu-nvgao';T=R/'tasks'/tid;O=R/'runs'/tid;P=R/'packs';P.mkdir(exist_ok=True)
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
save(T/'provenance.json',{'record_id':'base664:0260','title':'神户女高神隐事件','entry_url':'https://heiziheizi123.github.io/kobehighschool/','repository':'https://github.com/heiziheizi123/kobehighschool','version':'Public deployed files fetched 2026-10-27, plus repository-only schooldemo.html retained separately in original.zip; see live-fetch.json for exact status/hash.','status':'resource_incomplete','account_requirement':'none','dependencies':['Font Awesome 6.4.0 CDN CSS remains original external link; blocked during local smoke.','Python 3.11 + Playwright + installed msedge for blocker smoke.'],'missing_materials':['puzzle1.jpg','puzzle2.jpg'],'notes':['Both missing images are explicitly labelled puzzle fragments. Their informational content and downstream necessity cannot be established from absent bytes.','Repository main omits ending1.html and endingzz.html; recovered deployed originals are preserved, not reconstructed.','No compatibility patches; no ending tier judgments or scoring claims made.']})
(T/'README.md').write_text('''# 神户女高神隐事件：资源恢复，尚未验收

原记录 base664:0260。此包不是可正式计分的 prepared 数据。
已保存公开部署版本及独立原始仓库快照。源站 puzzle1.jpg / puzzle2.jpg 均 HTTP 404，页面明确显示为拼图碎片，不能推断其内容或用自造图片补齐。两篇原作结局已从实际部署恢复。

仅用于恢复检查：从包根执行 `python scripts/serve_static.py --root tasks/shenhu-nvgao/mirror --port 8811`，访问 http://127.0.0.1:8811/ 。浏览器可用全新 context 重置；游戏资源未发现 local/sessionStorage 持久状态。账号密码均为虚构本地谜题，无真实账号。

仍需补回两碎片、核查完整动态资源与CDN字体、全部推理门/分支/结局、独立裁判、完整UI正负例与重置、正式两包部署。现有 smoke 只验证缺图和两结局按钮，不代表流程通过。原作文本中无已核实好坏等级，后续不得擅自评为好结局。
''',encoding='utf-8')
# Avoid serving a repository-only demo that is absent from the actual deployment.
if (T/'mirror/schooldemo.html').exists():shutil.move(str(T/'mirror/schooldemo.html'),str(O/'repository-only-schooldemo.html'))
shutil.copyfile(R/'ARG-packs/verify-416/bodies/260.html',O/'historical-260.html')
common=[p for p in T.rglob('*') if p.is_file()]+[R/'scripts/serve_static.py']
evidence=[p for p in O.rglob('*') if p.is_file() and 'unpacked' not in str(p)]+[R/'scripts'/n for n in ['shenhu_nvgao_resource_audit.py','shenhu_nvgao_fetch.py','shenhu_nvgao_smoke.py','shenhu_nvgao_recovery_pack.py']]
rows=[]
for suffix,files in [('resources-recovery',common),('evidence-recovery',common+evidence)]:
 path=P/f'{tid}.{suffix}.zip'
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  for f in sorted(set(files)):z.write(f,f.relative_to(R).as_posix())
  z.writestr('RECOVERY-STATUS.json',json.dumps({'record_id':'base664:0260','status':'blocked_missing_puzzle_materials','formal_scoring_ready':False,'manifest':[{'path':f.relative_to(R).as_posix(),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted(set(files))]},ensure_ascii=False,indent=2))
 dest=O/('unpacked-'+suffix);dest.mkdir(exist_ok=True)
 with zipfile.ZipFile(path) as z:z.extractall(dest)
 rows.append({'path':path.relative_to(R).as_posix(),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'extracted_root':str(dest)})
save(O/'recovery-packages.json',rows);print(json.dumps(rows,ensure_ascii=True))
