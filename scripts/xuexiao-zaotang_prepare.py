from pathlib import Path
import json,hashlib,zipfile,re,shutil
R=Path(__file__).resolve().parents[1];T='xuexiao-zaotang';B=R/'tasks'/T;J=R/'judge'/T
J.mkdir(exist_ok=True);(J/'source').mkdir(exist_ok=True)
def wr(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
src=R/'ARG-packs/verify-84/bodies/75.html';raw=src.read_bytes();s=raw.decode('utf-8');shutil.copyfile(src,J/'source/index.original.html')
for n in ['judge.json']:
 p=J/n
 if not (J/('source/'+n+'.legacy')).exists():shutil.copyfile(p,J/('source/'+n+'.legacy'))
p=R/'configs'/f'{T}.json'
if not (J/'source/config.legacy.json').exists():shutil.copyfile(p,J/'source/config.legacy.json')
c=json.loads(p.read_text(encoding='utf-8'));c['account_requirement']='unknown';c['notes_for_report']=['BLOCKED added84:0075: archived entry is incomplete; profile.html and start.html are required and unavailable. Live TLS fails on 2026-10-27. Legacy ending-only judge is unvalidated; do not use for formal scoring.'];wr(p,c)
sample=json.loads(json.dumps(c));sample.update(runtime_layer='L1',entry_url='http://127.0.0.1:8831/index.html',allow_hosts=['127.0.0.1:8831']);sample['local_serve']={'enabled':True,'command':['python','scripts/serve_static.py','--root',f'tasks/{T}/mirror','--port','8831'],'cwd':'.','ready_url':'http://127.0.0.1:8831/index.html','port':8831,'ready_timeout_s':30};sample['model_visible']['intro']='资源不完整的阻塞诊断快照，仅供恢复与入口验收，不可用于正式评测。';wr(R/f'configs/samples/{T}-blocked.json',sample)
wr(B/'provenance.json',{'record_id':'added84:0075','task_id':T,'canonical_url':c['entry_url'],'snapshot_path':str(src.relative_to(R)).replace('\\','/'),'original_bytes':len(raw),'original_sha256':sha(src),'runtime_sha256':sha(B/'mirror/index.html'),'required_missing_files':['profile.html','start.html'],'inline_css_js':True,'external_asset_urls':re.findall(r'(?:src|href)=["\'](https?://[^"\']+)',s),'game_changes':[],'resource_status':'incomplete','account_requirement':'unknown','live_probe':'tasks/'+T+'/evidence/live-probe.json'})
wr(J/'checkpoint-spec.json',{'status':'blocked_unmapped','observed_actions':['toggle only original poster/all replies','open author profile (missing)','resume start.html conditional on argUser (missing)'],'entry_writes':{'argStep':'1 on every entry load; previous higher step overwritten before resume test'},'reasoning_checkpoints':[],'reasoning_checkpoint_status':'cannot determine without profile and later game pages','legacy_judge':{'ending_quote':'那个声音，从来就不是水。','evidence':'legacy configuration only; source and successful UI unavailable','formal_scoring_approved':False},'endings':'unknown','failures':'unknown','blocked_resources':['profile.html','start.html']})
(B/'README.md').write_text('''# 学校澡堂的水声 — 阻塞恢复包

原始记录 added84:0075，沿用 xuexiao-zaotang。非完整游戏、非正式计分包。入口快照 21620 bytes，未修改。必要 profile.html、start.html 缺失，后续依赖与结局仍未知。原站 index/profile/start 均在 2026-10-27 TLS EOF；不能据此断言永久失效。

原有 configs/xuexiao-zaotang.json 保留 L3 真实入口并标注阻塞，账号需求 unknown。仅诊断本地运行：`python scripts/run_one.py --config configs/samples/xuexiao-zaotang-blocked.json --policy script`。Python 3.11+，安装 requirements.txt 并 `python -m playwright install chromium`；Windows 可使用已安装 Edge。静态根目录仅 tasks/xuexiao-zaotang/mirror。启动：`python scripts/serve_static.py --root tasks/xuexiao-zaotang/mirror --port 8831`；Ctrl+C 停止。重置必须新浏览器 context，清除 localStorage；首页会覆盖 argStep=1，不能视作完整游戏重置。

恢复：使用 scripts/xuexiao-zaotang_probe.py 重查原站，获取原始 profile.html/start.html 并递归获取全部真实链接、脚本与素材；记录版本哈希。之后重新映射所有谜题、结局、失败和退出，对独立裁判及正常UI逐路径验收，再制作正式资源包和评测包。旧裁判仅通过终局句判定，未被原作后续源码/实机证明，无推理点，不能作为完成依据。

资源恢复 ZIP 只含玩家可见入口；recovery ZIP 包含评测侧配置/旧裁判/版本运行时及证据，不可作为网页根目录托管。解包验收只验证入口、缺页和裁判零分，不代表完整流程通过。未调用付费模型API。
''',encoding='utf-8')
print(json.dumps({'task':T,'bytes':len(raw),'sha256':sha(src),'missing':['profile.html','start.html']}))
