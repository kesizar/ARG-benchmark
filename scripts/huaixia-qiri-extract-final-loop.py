"""Copy the final completed retry segment; preserve the original append-only logs."""
import json
from pathlib import Path
source=Path('runs/huaixia-qiri/deploy-check/evaluation/runs/huaixia-qiri/harness-hidden')
target=Path('runs/huaixia-qiri/hidden-loop-final');target.mkdir(exist_ok=True)
for name in ['steps.jsonl','judge.jsonl']:
 rows=[json.loads(x) for x in (source/name).read_text(encoding='utf-8').splitlines() if x.strip()]
 starts=[i for i,x in enumerate(rows) if x.get('step')==1]
 if not starts:raise ValueError('missing first step in '+name)
 (target/name).write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows[starts[-1]:]),encoding='utf-8')
(target/'summary.json').write_bytes((source/'summary.json').read_bytes())
print('last retry extracted')
