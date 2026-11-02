from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];p=R/'configs/yiwu-yuren.json';c=json.loads(p.read_text(encoding='utf-8'));c['notes_for_report'].append('Restored missing hospital searchFeedback container used by original rejection handlers; no answers or match conditions changed.');p.write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf-8')
p=R/'tasks/yiwu-yuren/README.md';s=p.read_text(encoding='utf-8').replace('原件及逐行diff位于','医院原作遗漏searchFeedback元素，补回原脚本需要的可见反馈容器，使空值/错误查询正常显示提示；未添加原作未渲染的样例自动填充按钮。原件及逐行diff位于');p.write_text(s,encoding='utf-8')
p=R/'judge/yiwu-yuren/checkpoint-spec.json';s=json.loads(p.read_text(encoding='utf-8'));s['compatibility_retest']='verification/hospital-compatibility-retest.json';s['judge']+=' Ending hooks additionally require same-origin opener student thread with matching fourth choice and generated final message; direct ending navigation remains unscored.';p.write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')
(R/'judge/yiwu-yuren/review.md').write_text('''# Content and boundary review

Engineering and content readiness are separate. Case001 has two central deductions (impersonator Chen Yu and killer Zhou Yi), account reconstruction subpuzzles, dialogue routing and three labelled endings. Ordinary clue reading, paper-form decoration and moon clicking are not reasoning checkpoints. Explicit routes have four actual accepted dialogue gates; optional evidence pages do not become compulsory gates.

The shared author home contains independent cases002/003. This record is explicitly case001 and starts on its accepted-commission desktop. Those cases and the fictional external graduate-university placeholder are outside scope; no claim of whole-author-site mirroring is made. Case001’s real clue paths and assets are local. The common home is retained for original completion/replay UI.

Original narratives include inconsistent year/date framing, fictional nine-digit telephone numbers and hintable account strings. The hospital accepts 2025-03-01 even though feeder/death context may suggest a different date; do not use this optional lookup as mandatory route gate. Role login/identity recovery are simulated; no real account is used. Neither story-end numbering nor moral judgement establishes a good/bad tier, so all three formal endings are normal.

Source compatibility changes are strictly icon/font localization, undefined ordinary email credential rejection, diary return typo, and missing hospital error-feedback element. The hospital originally threw six nonblocking DOM errors during the material audit; the exact source and diff are retained and an affected-behaviour retest verifies visible rejection plus correct query. The game code is otherwise unchanged. The minigame timed out during an auditor scroll-to-stable wait; the auditor now uses current visible coordinates for the moving moon. It remains a 30-second optional pastime, not an ARG failure or score checkpoint.

No paid API or model playthrough was used. Step/time budgets and difficulty require later model calibration. Browser acceptance reuses installed Windows browser/Python packages; independent extraction is not a clean-OS or cross-platform test.
''',encoding='utf-8')
