"""Verify frozen bundle equivalence and independently host both package boundaries."""
from pathlib import Path
import hashlib, json, socket, subprocess, sys, time, urllib.request, urllib.error, zipfile
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
T = 'yongyuan-xiatian'
OUT = ROOT / 'judge' / T
def sha(b): return hashlib.sha256(b).hexdigest()
prepared = ROOT / 'packs' / f'{T}.prepared.zip'
resources = ROOT / 'packs' / f'{T}.resources.zip'
deployment = ROOT / 'runs/yongyuan-deploy-0fd1d515'
resource_root = ROOT / 'runs/yongyuan-resources-deploy'
report = {'kind': 'independent_windows_deployment_and_frozen_evidence_audit', 'model_api_calls': 0}
with zipfile.ZipFile(prepared) as z:
    assert z.testzip() is None
    manifest = json.loads(z.read('BUNDLE-MANIFEST.json'))
    for row in manifest['files']:
        for base in [ROOT, deployment]:
            assert sha((base / row['path']).read_bytes()) == row['sha256'], (base, row['path'])
    report['prepared_manifest_files_verified'] = len(manifest['files'])
with zipfile.ZipFile(resources) as z:
    assert z.testzip() is None
    resource_root.mkdir(parents=True, exist_ok=True)
    z.extractall(resource_root)
    public = z.namelist()
    for path in public:
        assert z.read(path) == (ROOT/path).read_bytes() == (deployment/path).read_bytes() == (resource_root/path).read_bytes()
report['archives'] = [{'path': str(p.relative_to(ROOT)), 'sha256': sha(p.read_bytes()), 'bytes': p.stat().st_size} for p in [resources, prepared]]
acceptance_path = deployment / 'judge' / T / 'verification/acceptance.json'
acceptance = json.loads(acceptance_path.read_text(encoding='utf-8'))
assert acceptance['pass'] and acceptance['fresh_reset_verified'] and acceptance['fresh_server_owned']
assert acceptance['score']['ending_reached'] and acceptance['score']['ending_tier'] == 'normal'
assert len(acceptance['score']['checkpoints']) == 1 and len(acceptance['score']['diagnostic']) == 7
assert acceptance['negative_checks'] == 50 and not acceptance['errors'] and not acceptance['http_errors'] and not acceptance['blocked']
report['full_ui'] = {'path': str(acceptance_path.relative_to(ROOT)), 'sha256': sha(acceptance_path.read_bytes()), 'steps': len(acceptance['steps']), 'negative_checks': acceptance['negative_checks'], 'score': acceptance['score'], 'fresh_reset_verified': True, 'reuse_boundary': 'All 74 packaged files match accepted independent extraction and current workspace byte for byte. No game/judge/runtime changes.'}
report['deployments'] = []
for base, port, kind in [(resource_root, 8833, 'resources_only'), (deployment, 8832, 'prepared')]:
    # Fail rather than attach to an existing server.
    with socket.socket() as s:
        s.bind(('127.0.0.1', port))
    log_path = base / 'deployment-http.log'
    with log_path.open('w', encoding='utf-8') as log:
        proc = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1', '--directory', str(base / 'tasks' / T / 'mirror')], cwd=base, stdout=log, stderr=log)
        try:
            for attempt in range(40):
                try:
                    urllib.request.urlopen(f'http://127.0.0.1:{port}/index.html', timeout=2).read()
                    break
                except (OSError, urllib.error.URLError): time.sleep(.1)
            rows = []
            for path in public:
                relative = Path(path).relative_to(Path('tasks') / T / 'mirror').as_posix()
                data = urllib.request.urlopen(f'http://127.0.0.1:{port}/{quote(relative)}', timeout=10).read()
                assert data == (base/path).read_bytes()
                rows.append({'path': relative, 'sha256': sha(data), 'bytes': len(data)})
            for private in ['/judge/yongyuan-xiatian/judge.json', '/configs/yongyuan-xiatian.json', '/harness/judge.py']:
                try: urllib.request.urlopen(f'http://127.0.0.1:{port}{private}', timeout=2); raise AssertionError(private)
                except urllib.error.HTTPError as error: assert error.code == 404
            report['deployments'].append({'kind': kind, 'directory': str(base), 'port': port, 'owned_pid': proc.pid, 'public_files': rows, 'private_paths_404': True})
        finally:
            proc.terminate(); proc.wait(timeout=10)
report['base_environment'] = {'python': sys.version, 'executable': sys.executable, 'scope': 'Existing Windows Python dependencies/browser, not a fresh OS or cross-platform test.'}
report['pass'] = True
(OUT / 'deployment.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'pass': True, 'public_files': len(public), 'ui_steps': report['full_ui']['steps'], 'ports': [8832, 8833]}, ensure_ascii=False))
