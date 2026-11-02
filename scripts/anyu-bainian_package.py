"""Recovery bundles, explicitly incomplete; never mark prepared/accepted."""
from pathlib import Path
import asyncio,hashlib,importlib.util,json,sys,zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import importlib
audit=importlib.import_module('anyu-bainian_audit')
OUT=ROOT/'runs/anyu-bainian'
task=ROOT/'tasks/anyu-bainian'
cfg=json.loads((task/'original/config.json').read_text(encoding='utf-8'))
cfg.update(runtime_layer='L1',account_requirement='none',entry_url='http://127.0.0.1:8831/index.html',allow_hosts=['127.0.0.1:8831'],judge_path='judge/anyu-bainian/candidate-judge.json')
cfg['local_serve']={'enabled':True,'command':['python','scripts/serve_static.py','--root','tasks/anyu-bainian/mirror','--port','8831'],'cwd':'.','ready_url':cfg['entry_url'],'ready_timeout_s':30,'port':8831}
cfg['notes_for_report']=['RECOVERY ONLY: six referenced images missing, source unreachable, no full puzzle acceptance.','Normal UI search bypasses every puzzle and opens three endings. This version is unsuitable for formal reasoning evaluation.']
audit.dump(ROOT/'configs/anyu-bainian-recovery.json',cfg)
(task/'README.md').write_text('''# 暗语百年：序幕 / 最後一句傳話（0365）恢复材料

此包不是已准备完成的正式任务。29 页流程加隐藏第 30 页在单 HTML 内，六张引用图片缺失；原站和图片复探遇 TLS EOF，仅说明当前连接失败，不宣布站点失效。外部字体为 feishu，原 CSS 有本机字体回退；未删除或伪造资源。

资源服只托管 `tasks/anyu-bainian/mirror`。Python 3.11+、Playwright 与已安装 Edge 为验收基础环境，未打包。无需真实账户；Web Audio 在浏览器本地合成。正常任务新建浏览器 context 重置，不能复用存档。原作界面 restart 清除 S，完整全局变量重置覆盖待验。

诊断启动：`python scripts/serve_static.py --root tasks/anyu-bainian/mirror --port 8831`。恢复配置 `configs/anyu-bainian-recovery.json` 只供诊断，不进入正式评测。原线上配置与旧裁判保留未改。

独立候选裁判记录 1–28 页为可选状态、30 页为可选访问；三结局同为 normal。没有必经推理门，因为原作站内搜索可直接到最终选择页，不解题即可获得全部结局。候选裁判不凭空把四个旧门补成必经。正常 UI 已验证错密码不计状态、关灯/电脑/开盒顺序成功、三个跳关结局和新 context 重置；没有宣称全 28 题可解。

恢复后续：补齐六张原图并核验其内容；逐题覆盖 2–28 的正确、错误、提示、音频视觉替代、失败支线与重置；先决定保留原作搜索捷径且排除正式评测，还是取得作者认可的修订版本。不得将源码答案回放报告为模型可解。
''',encoding='utf-8')
gamefiles=list((task/'mirror').rglob('*'))
evalfiles=gamefiles+[ROOT/'configs/anyu-bainian-recovery.json',ROOT/'judge/anyu-bainian/candidate-judge.json',ROOT/'judge/anyu-bainian/checkpoint-spec.json',ROOT/'scripts/serve_static.py',ROOT/'scripts/anyu-bainian_audit.py',task/'README.md',task/'provenance.json']+list((ROOT/'harness').glob('*.py'))
deploy=[]
for kind,files,port in [('game-recovery',gamefiles,8832),('evaluation-recovery',evalfiles,8833)]:
    archive=ROOT/'packs'/f'anyu-bainian.{kind}.zip'
    entries=[]
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(set(files)):
            if not p.is_file() or p.name.startswith('test_'):continue
            name=p.relative_to(task/'mirror').as_posix() if kind=='game-recovery' else p.relative_to(ROOT).as_posix()
            z.write(p,name);entries.append({'path':name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
        z.writestr('RECOVERY-NOT-ACCEPTED.txt','Six referenced JPEG images absent. No full puzzle flow acceptance. Original search shortcut bypasses all puzzle gates. Base environment: Python 3.11+, Playwright, Edge. No secrets or model policies included.')
    audit.dump(ROOT/'packs'/f'anyu-bainian.{kind}.manifest.json',{'status':'recovery_only_not_accepted','record_id':'base664:0365','sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'files':entries})
    target=OUT/f'deployment-{kind}'
    target.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as z:z.extractall(target)
    logs=OUT/f'deployment-{kind}-evidence';logs.mkdir(exist_ok=True)
    if kind=='game-recovery':module=audit;game_root=target
    else:
        spec=importlib.util.spec_from_file_location('anyu_independent',target/'scripts/anyu-bainian_audit.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        module.ROOT=target
        game_root=target/'tasks/anyu-bainian/mirror'
        # Use this extraction's harness, not a previously imported checkout module.
        for key in list(sys.modules):
            if key=='harness' or key.startswith('harness.'):del sys.modules[key]
    asyncio.run(module.ui(game_root,port,logs))
    deploy.append({'kind':kind,'port':port,'target':str(target),'evidence':str(logs/'ui-diagnostics.json'),'passed':'diagnostic_subset_only'})
audit.dump(OUT/'recovery-deployments.json',deploy)
print('Two recovery packages deployed on independent roots/ports; both diagnostic subsets passed, neither accepted.')
