import hashlib, json, sys, zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
unpacked = root / 'runs/mingde-zhuilou/closeout-unpacked'
sys.path.insert(0, str(unpacked))
from harness.summary import build_summary

read = lambda p: json.loads((root / p).read_text(encoding='utf-8'))
trace = read('runs/mingde-zhuilou/closeout-ui/acceptance.json')
assert trace['passed']
records = [x for x in trace['trace'] if x.get('score', {}).get('ending_reached')]
assert {x['score']['route_id'] for x in records} == {'silent', 'late-justice', 'bright-trial'}
for item in records:
    score = item['score']
    assert score['checkpoints_total'] == 0 and score['checkpoints_reached'] == 0
    s = build_summary({'id': 'mingde-zhuilou'}, model={}, ended_reason='ending', steps=1, seconds=1, score=score, blocked=[], tokens={})
    assert s['progress'] is None and s['reasoning_progress'] is None and s['route_progress'] == 1.0
archive = root / 'packs/mingde-zhuilou.prepared.zip'
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    manifest = json.loads(z.read('BUNDLE-MANIFEST.json'))
    for f in manifest['files']:
        assert hashlib.sha256(z.read(f['path'])).hexdigest() == f['sha256']
sha = hashlib.sha256(archive.read_bytes()).hexdigest()
result_path = root / 'data/preparation/results/base664-0153.json'
result = json.loads(result_path.read_text(encoding='utf-8'))
prepared = next(x for x in result['archives'] if x['kind'] == 'prepared')
prepared.update(sha256=sha, bytes=archive.stat().st_size, extraction='runs/mingde-zhuilou/closeout-unpacked', previous_archive='packs/mingde-zhuilou.prepared.before-closeout.zip', previous_sha256='c96e8c5386c309fd7747cbc786a8a7aa95ffb0638436380e6acf6425c9762c21')
result['coverage'].update(critical_reasoning_checkpoints=0, diagnostic_checkpoints=12)
result['review_closeout'] = 'data/preparation/reviews/base664-0153-closeout.json'
result['content_finding'] = 'Author identity needed for entry is absent; document passwords are direct lookups and report selections can bypass documents and be guessed with ending feedback. No objective reasoning checkpoint is defined; all 12 retained as diagnostics.'
result['evidence'].extend(['judge/mingde-zhuilou/closeout.diff', 'runs/mingde-zhuilou/closeout-ui/acceptance.json'])
result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
review = {
 'record_id':'base664:0153', 'title':'明德中学坠楼案', 'status':'engineering_ready_formal_reasoning_hold', 'ready_for_formal_scoring':False,
 'conclusion':'已有材料不能构造客观可评分的推理题。入口要求作者姓名首字母而提供材料缺作者身份；文档密码为日期、卡号、姓名等明示信息的直接读取；报告选项可绕开全部文档，且结局反馈提示缺失证据，可反复猜测。',
 'entry_condition':'入口原作要求作者姓名八位首字母；作者身份在现有材料未发现。界面测试使用源码已知值仅验证机制，不证明玩家可解。',
 'reasoning_points':{'critical':0,'diagnostic':12,'classification':'开机、六个主线密码、三个孤立页面密码及报告的赔偿协议和李阳选择均作诊断，不作为推理得分。检索结果明确标注关键证人；不能证明选择来源于独立推理。'},
 'endings_and_failures':{'silent':'无声的悲鸣：无赔偿协议，原作悲剧叙事结局','late-justice':'迟来的正义：选择赔偿协议但不选李阳，普通结局','bright-trial':'光明的审判：两者均选择，好结局','terminal_failure':'源码及界面未发现独立终局失败；空报告不可提交，错误密码可重试，账号五次错误短暂锁定且可刷新重置。'},
 'reset':'各结局重启清除报告选择；新浏览器上下文及新 Judge 验证全部状态重置。报告内重启不等同于所有页面及裁判状态重置。',
 'evidence_scope':'14 项主线文档可经检索打开；三个额外密码门位于无主线入口的页面，仅直接导航审计。原游戏包与旧独立评测包的原始 UI/独立部署实测保留；修订评测包重新解包，用其自身裁判验证 14 文档、主线及孤立密码正负、三种结局、锁定与重置。',
 'scoring_semantics':'所有结局在 Judge 中可有 route_progress=1 表示路线完成；新包 summary 对 0/0 返回 progress=null 和 reasoning_progress=null，不视为满分。',
 'preserved':{'old_judge':'judge/mingde-zhuilou/closeout-before/','diff':'judge/mingde-zhuilou/closeout.diff','old_prepared_bundle':'packs/mingde-zhuilou.prepared.before-closeout.zip','game_patch':'tasks/mingde-zhuilou/evidence/locked-mail-syntax.diff'},
 'validation':{'independent_ui':'runs/mingde-zhuilou/closeout-ui/acceptance.json','script':'scripts/mingde_zhuilou_closeout.py','summary':'all three ending scores checked with extracted package build_summary','archive':'CRC and manifest SHA-256 verified','prepared_sha256':sha,'source_proof':'runs/mingde-zhuilou/minimal-route-proof.json','prior_independent':'runs/mingde-zhuilou/independent-harness.json'},
 'limitations':['源码已知答案仅用于工程验证，不是模型成绩或可解性证明。','重复报告与反馈允许猜测；不衡量独立推理。','仅 Windows/Edge 实测；远程 CDN 图标请求被阻断。','修订包的独立 UI 测试使用本地回环；不涉及付费模型或账号。']}
out = root / 'data/preparation/reviews/base664-0153-closeout.json'
out.write_text(json.dumps(review, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print('PASS:', len(records), 'ending snapshots, summary, bundle', sha)
