from pathlib import Path
import json,hashlib,zipfile,importlib.metadata,sys
R=Path(__file__).resolve().parents[1];T=R/'tasks/guangying-she';J=R/'judge/guangying-she';O=R/'runs/guangying-she';P=R/'packs'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
versions={k:importlib.metadata.version(k) for k in ['playwright','httpx','jsonschema','python-dotenv']}
save(T/'provenance.json',{'record_id':'base664:0425','task_id':'guangying-she','entry':'https://01a07249-04b2-78c6-a3d9-afac55849ee5.arena.site/','retrieved_date':'2026-10-27','historical_wrapper':{'bytes':(T/'historical-wrapper.html').stat().st_size,'sha256':sha(T/'historical-wrapper.html')},'original_game':{'bytes':(T/'document-2.html').stat().st_size,'sha256':sha(T/'document-2.html'),'evidence':'runs/guangying-she/documents.json','recovery_method':'Unmodified HTTP response body from actual iframe loaded by normal fresh Edge; no alternate host, authentication or access bypass.'},'local_game':{'bytes':(T/'mirror/index.html').stat().st_size,'sha256':sha(T/'mirror/index.html')},'patches':['Remove external font/favicon link tags and Cloudflare analytics script only; original 422120-byte document and unified diff retained evaluator-side. Inline React logic, CSS, SVG art and content unchanged.'],'runtime_layer':'L1','account_requirement':'none','resources_complete':True,'runtime_external_dependencies':[],'platform':'Windows / Python 3.11 / Edge 156.0.4314.42','packages':versions})
(T/'README.md').write_text('''# 光影摄影社 · 相册驿站

base664:0425；本地 L1，无账号。游戏是单一自包含 React HTML，所有照片为内联 SVG 绘制；附件名是游戏内索引文本，不是缺失 JPEG。Python 3.11+，Playwright，Edge/Chromium；依赖版本见 provenance 或 requirements。没有 API 密钥或付费调用。

资源包：运行 `python -m http.server 8813 --bind 0.0.0.0 --directory tasks/guangying-she/mirror`，打开 http://127.0.0.1:8813/index.html 。评测包：运行 `python scripts/run_one.py --config configs/guangying-she.json --policy script`；脚本策略仅放弃用于工程烟测，完整正常界面验收证据在主仓库 runs/guangying-she/acceptance.json。模型评测另设外部 API 环境，不属于资源依赖。

只托管 mirror 目录。原始源码、裁判、配置、日志不能作为静态根。停止服务使用 Ctrl+C 或停止启动进程。全新 browser context 是每局重置；页脚重置本站进度也清除谜题、留言、证书、钉夹和模式，只保留访问计数。开幕的再排一次展墙只重置主墙。

正式候选采用全自助观展（off）。向导模式可逐级给出完整排序，因此裁判排除 on。唯一关键推理门是八图时间线排序；暗房口令是可选线索检索门，不能当作必经。钉夹、浏览、留言、证书落款、打印不计推理分。未满八张时核对按钮禁用；完整错误排序显示逐格对错；正确排序后打开开幕之夜构成唯一原作结局，无好坏等级。

资源恢复与完整准备证据由主代理最终复核。暗房备忘直接列完整时间和标题，且错误核对提供逐格反馈，难度偏低；不应冒称高难推理。平台外壳历史快照不含游戏内容，本次为2026-10-27实际iframe版本，不能宣称与历史游戏版本等价。独立解包是在同一Windows环境，非跨平台证明。
''',encoding='utf8')
common=[T/'mirror/index.html',T/'README.md',T/'provenance.json']
evalfiles=common+[R/'configs/guangying-she.json',R/'configs/schema/task.schema.json',R/'scripts/run_one.py',R/'scripts/serve_static.py',R/'scripts/validate_config.py',R/'scripts/guangying_she_accept.py',R/'scripts/guangying_she_judge_tests.py']+[p for p in (R/'harness').glob('*.py') if not p.name.startswith('test_')]+[p for p in J.iterdir() if p.is_file()]+[T/'document-2.html',T/'localization.diff']
packages=[]
for kind,files in [('resources',common),('prepared',evalfiles)]:
 archive=P/f'guangying-she.{kind}.zip';manifest=[{'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(set(files)):z.write(p,p.relative_to(R).as_posix())
  z.writestr('BUNDLE-MANIFEST.json',json.dumps({'record_id':'base664:0425','task_id':'guangying-she','kind':kind,'runtime_layer':'L1','files':manifest,'prerequisites':{'python':'3.11+','browser':'Edge or Playwright Chromium','packages':versions}},ensure_ascii=False,indent=2))
  if kind=='prepared':z.writestr('requirements.txt','\n'.join(f'{k}=={v}' for k,v in versions.items())+'\n')
 dest=O/f'unpacked-{kind}'
 with zipfile.ZipFile(archive) as z:z.extractall(dest)
 for f in manifest:assert sha(dest/f['path'])==f['sha256']
 packages.append({'kind':kind,'archive':archive.relative_to(R).as_posix(),'sha256':sha(archive),'bytes':archive.stat().st_size,'unpacked_root':str(dest),'member_hashes_verified':len(manifest)})
save(O/'packages.json',packages)
print(json.dumps(packages,ensure_ascii=True))
