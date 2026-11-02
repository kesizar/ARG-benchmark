"""Isolated small-scale protocol validation; never stores API credentials."""
import asyncio
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.env import load_env
from harness.config import load_config
from harness.policy_llm import LLMPolicy
from harness.protocol_identity import file_sha256
from harness.protocol_report import report
from harness.loop import run

OUT = ROOT / 'data/pilot/protocol-validation-rerun-20261028'
load_env(ROOT)
key = os.environ.get('AGENT_API_KEY')
if not key:
    raise SystemExit('DeepSeek 凭据缺失')
os.environ.update(OPENAI_API_KEY=key, OPENAI_BASE_URL='https://api.deepseek.com',
                  OPENAI_MODEL='deepseek-flash', LLM_PROVIDER='deepseek',
                  AGENT_HTTP_TRUST_ENV='false', LLM_EXPERIMENT_PROFILE='validation-deepseek-v1')
for name in ('LLM_MAX_OUTPUT_TOKENS', 'LLM_REASONING_EFFORT', 'ENABLE_THINKING', 'PRESERVE_REASONING'):
    os.environ.pop(name, None)

def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def prepare():
    if OUT.exists():
        raise SystemExit('验证目录已存在，拒绝覆盖')
    OUT.mkdir(parents=True)
    tasks = []
    definitions = [
        ('dengta', 'data/pilot/deepseek-20261028/config.json', 'data/pilot/deepseek-20261028/judge.json',
         ['birthday-rehearsal'], 30, 'scripts/dengta-jushe_ui.py', 150, 7200),
    ]
    for label, config, judge, routes, ref, evidence, steps, seconds in definitions:
        cfg = json.loads((ROOT / config).read_text(encoding='utf-8-sig'))
        j = json.loads((ROOT / judge).read_text(encoding='utf-8-sig'))
        task_id = 'protocol-validation-rerun-20261028-' + label
        cfg['id'] = task_id
        cfg['limits'] = {'max_steps': steps, 'max_seconds': seconds, 'max_answer_submits': 10}
        cfg['require_images'] = True
        cfg['judge_path'] = f'data/pilot/protocol-validation-rerun-20261028/{label}-judge.json'
        cfg['notes_for_report'] = ['隔离的正式流程验证，不作为模型排名。']
        j['scoring_protocol'] = 'target_v1'
        j['target_success'] = {'route_ids': routes}
        cp = OUT / f'{label}-config.json'
        jp = OUT / f'{label}-judge.json'
        write_json(cp, cfg); write_json(jp, j)
        tasks.append({'id': task_id, 'config': cp.relative_to(ROOT).as_posix(),
                      'config_sha256': file_sha256(cp), 'judge_sha256': file_sha256(jp),
                      'progress_scored': True, 'capabilities': ['state'],
                      'reference_steps': ref, 'reference_evidence': evidence})
    cfg = load_config(ROOT / tasks[0]['config'], 'B'); cfg['_run_kind'] = 'official'
    policy = LLMPolicy(cfg, OUT)
    manifest = {'id': 'validation-rerun-20261028', 'obs_mode': 'B', 'repeats': 3,
                'required_capabilities': ['state'],
                'models': [{'provider': policy.provider, 'name': policy.model_name,
                            'profile_id': 'validation-deepseek-v1', 'profile_sha256': policy.profile_sha256()}],
                'tasks': tasks}
    report(manifest, [])
    write_json(OUT / 'manifest.json', manifest)
    write_json(OUT / 'profile.json', policy.profile())
    return manifest

def save_report(manifest):
    rows = []
    for task in manifest['tasks']:
        for p in sorted((ROOT / 'runs' / task['id'] / 'B').glob('*/summary.json')):
            rows.append(json.loads(p.read_text(encoding='utf-8-sig')))
    write_json(OUT / 'report.json', report(manifest, rows))
    print('REPORT_WRITTEN', len(rows), flush=True)

async def main():
    manifest = prepare()
    print('MANIFEST_READY', flush=True)
    try:
        summary = await run(ROOT / manifest['tasks'][0]['config'], policy='llm', obs_mode='B',
                            headless=True, repo_root=ROOT, run_kind='official', manifest=manifest, repetition=1)
        print('EPISODE_DONE', json.dumps({k: summary.get(k) for k in ('ended_reason', 'steps', 'target_success', 'progress', 'tokens')}, ensure_ascii=False), flush=True)
    finally:
        save_report(manifest)

asyncio.run(main())
