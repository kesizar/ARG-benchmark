"""Preserve blocked source and exact missing dependencies; never claim readiness."""
from pathlib import Path
import hashlib,json,re,shutil,zipfile
R=Path(__file__).resolve().parents[1];T='fengzhi-juanyi';J=R/'judge'/T;P=R/'tasks'/T
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
src=R/'ARG-packs/verify-416/bodies/420.html';text=src.read_text(encoding='utf-8')
(J/'source').mkdir(parents=True,exist_ok=True);(P/'incomplete-source').mkdir(parents=True,exist_ok=True)
shutil.copyfile(src,P/'incomplete-source/index.html')
for path,name in [(R/f'configs/{T}.json','legacy-config.json'),(J/'judge.json','legacy-judge.json')]:
 dst=J/'source'/name
 if path.exists() and not dst.exists():shutil.copyfile(path,dst)
game_text=text[text.index('const GAME ='):text.index('const SAVE_KEY')]
assets=sorted(set(re.findall(r'(?:url|cutout|sprite)\s*:\s*[\"\'](img/[^\"\']+\.(?:jpg|png|jpeg|webp))',game_text)))
assert len(assets)>60
write(J/'resource-check.json',{'record_id':'base664:0420','snapshot_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'required_assets':assets,'required_asset_count':len(assets),'available_required_assets':0,'local_search':'rg --files ARG-packs and tasks matching police_office/chenshuang_home/fengzhi found only source 420.html','public_fetches':[{'url':u,'result':'URLError Errno11001 getaddrinfo failed'} for u in ['https://www.fengzhi.icu/img/police_office.jpg','https://www.fengzhi.icu/img/cutouts/po_report.png','https://fengzhi.icu/img/police_office.jpg','http://www.fengzhi.icu/img/police_office.jpg']],'interpretation':'Current resolver cannot reach host. This is not proof of permanent site death. Complete assets are unavailable locally; no placeholder images substituted.','deployment':'not attempted: knowingly incomplete resources','compatibility_changes':[]})
conclusions=[]
for m in re.finditer(r'(D\d+)\s*:\s*\{\s*id:"([^"]+)",\s*text:"([^"]+)",\s*required:\[([^\]]+)\]',text):
 conclusions.append({'id':m[1],'text':m[3],'required_evidence':re.findall(r'"([^"]+)"',m[4]),'validation':'source_only_not_UI_accepted'})
write(J/'source-audit.json',{'record_id':'base664:0420','status':'partial_static_audit_not_completed','deductions':conclusions,'confrontation_evidence':['E18','E30','E25','E16','E10'],'confrontation':'All five evidence must be presented to sunhao2; early questioning leads to gate_fail retry node. Not independently UI-verified.','chapter_count':16,'ending_source_labels':[{'id':'A','title':'逍遥法外','label':'结局一','source_trigger':'chooseBranch(stop)'},{'id':'B','title':'真相大白','label':'真结局'},{'id':'C','title':'火噬','label':'结局三'}],'debug_risk':'Original ?debug=1 or #debug exposes chapter jump/full evidence/ending triggers. Do not use for UI acceptance. Config disallows model goto; complete packaging must explicitly review debug boundary.','not_yet_verified':['Every mandatory/optional deduction route dependency','All scene hotspots and dialogue branches','Wrong evidence and deduction behaviour','All endings using normal UI','Reset and save recovery','Independent runtime delivery']})
(P/'README.md').write_text('''# 冯止疑案·卷一：资源阻塞，非可运行交付

原始HTML已原样保存于 incomplete-source/index.html。此目录缺少场景与抠图图片，不能作为完整本地任务，也不能宣称已部署验收。详见 judge/fengzhi-juanyi/resource-check.json 精确缺件清单及DNS失败证据。

目前原站 www.fengzhi.icu 和裸域名在本机均解析失败，HTTP/HTTPS公开资源GET均失败；这不证明站点永久失效。没有账号/购买门槛的证据，也没有进行真实账号操作。

恢复方法：从作者/历史副本取得清单内图片，保留原路径；或网络恢复后运行 scripts/fengzhi_fetch_assets.py。只下载公开静态资源，不覆盖已有文件。取得完整资源后需重新制定配置、区分11个组合结论及5证据对峙的门槛、逐条真实UI验收和独立目录打包。在此之前不能使用原旧裁判“一点三路线”充当准备完成。

原作含调试跳关入口（?debug=1/#debug），后续运行包须记录并处理公平性边界，不得以调试跳关替代正常流程。此次没有修改原作。接入包只是恢复材料包，未包含可用评测运行时或已验证裁判。
''',encoding='utf-8')
write(P/'provenance.json',{'record_id':'base664:0420','source_url':'https://www.fengzhi.icu/','snapshot':str(src),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'modifications':[],'status':'incomplete_game_resources'})
pack=R/f'packs/{T}.access.zip'
files=[P/'incomplete-source/index.html',P/'README.md',P/'provenance.json',J/'resource-check.json',J/'source-audit.json',R/'scripts/fengzhi_fetch_assets.py']
with zipfile.ZipFile(pack,'w',compression=zipfile.ZIP_DEFLATED) as z:
 for f in files:z.write(f,f.relative_to(R).as_posix())
assert zipfile.ZipFile(pack).testzip() is None
result={'record_id':'base664:0420','task_id':T,'title':'冯止疑案-卷一','status':'blocked_missing_game_assets','runtime_layer':'unassigned_incomplete_snapshot','ready_for_local_execution':False,'ready_for_formal_scoring':False,'resources_bundle':None,'evaluation_bundle':None,'deployment_evidence':None,'acceptance':None,'recovery_bundle':{'path':pack.relative_to(R).as_posix(),'sha256':hashlib.sha256(pack.read_bytes()).hexdigest(),'bytes':pack.stat().st_size,'type':'incomplete_source_and_resource_recovery_kit_not_runnable'},'blocker':f'{len(assets)} actual image dependencies absent; public host DNS resolution failed on www and apex, HTTP and HTTPS.','evidence':[f'judge/{T}/resource-check.json',f'judge/{T}/source-audit.json',f'tasks/{T}/provenance.json'],'source_only_progress':{'deduction_combinations':len(conclusions),'confrontation_evidence_count':5,'ending_labels':3},'unverified':['Full assets','Runtime integration','All routes and mandatory gates','Independent judge','Real UI positive/negative acceptance','Independent deployment'],'model_api_calls':0}
write(R/'data/preparation/results/base664-0420.json',result)
print('FENGZHI BLOCKED:',len(assets),'missing assets; recovery kit only.')
