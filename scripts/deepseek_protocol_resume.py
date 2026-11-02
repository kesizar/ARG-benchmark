"""Resume the isolated frozen validation at repetitions 2 and 3."""
import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.env import load_env
from harness.loop import _model_link_down, run
from harness.protocol_report import report

OUT = ROOT / 'data/pilot/protocol-validation-rerun-20261028'
load_env(ROOT)
key = os.environ.get('AGENT_API_KEY')
if not key:
    raise SystemExit('DeepSeek 凭据缺失')
os.environ.update(OPENAI_API_KEY=key, OPENAI_BASE_URL='https://api.deepseek.com', OPENAI_MODEL='deepseek-flash',
                  LLM_PROVIDER='deepseek', AGENT_HTTP_TRUST_ENV='false', LLM_EXPERIMENT_PROFILE='validation-deepseek-v1')
for name in ('LLM_MAX_OUTPUT_TOKENS', 'LLM_REASONING_EFFORT', 'ENABLE_THINKING', 'PRESERVE_REASONING'):
    os.environ.pop(name, None)
manifest = json.loads((OUT / 'manifest.json').read_text(encoding='utf8'))
task = manifest['tasks'][0]

def save():
    rows = [json.loads(p.read_text(encoding='utf8')) for p in
            (ROOT / 'runs' / task['id'] / 'B').glob('*/summary.json')]
    (OUT / 'report.json').write_text(json.dumps(report(manifest, rows), ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print('REPORT_WRITTEN', len(rows), flush=True)

async def main():
    try:
        for repetition in (2, 3):
            for attempt in (1, 2, 3):
                try:
                    summary = await run(ROOT / task['config'], policy='llm', obs_mode='B', repo_root=ROOT,
                                        run_kind='official', manifest=manifest, repetition=repetition, attempt=attempt)
                    print('EPISODE_DONE', repetition, json.dumps({k: summary.get(k) for k in ('ended_reason','steps','target_success','progress','tokens')}, ensure_ascii=False), flush=True)
                    break
                except Exception as exc:
                    print('EPISODE_ERROR', repetition, attempt, type(exc).__name__, flush=True)
                    if not _model_link_down(exc) or attempt == 3:
                        break
            save()
    finally:
        save()

if __name__ == '__main__':
    asyncio.run(main())
