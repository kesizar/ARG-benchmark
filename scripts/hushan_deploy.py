"""Extract evaluator collection, check all bytes, run six UI units and standard CLI."""
import hashlib,json,subprocess,sys,uuid,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];TASK='hushan-xiangcheng'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 archive=ROOT/f'packs/{TASK}.prepared.zip';dst=ROOT/'runs'/f'hushan-deployment-{uuid.uuid4().hex[:8]}';dst.mkdir(parents=True)
 with zipfile.ZipFile(archive) as z:assert z.testzip() is None;z.extractall(dst)
 manifest=json.loads((dst/'BUNDLE-MANIFEST.json').read_text(encoding='utf-8'))
 for item in manifest['files']:assert sha(dst/item['path'])==item['sha256'],item['path']
 report={'archive':str(archive.relative_to(ROOT)),'archive_sha256':sha(archive),'extracted_root':str(dst),'crc_ok':True,'all_manifest_hashes_match':True,'model_api_used':False,'base_environment':'Windows; already installed Python dependencies and Edge/Chromium, not fresh installation','runtime_hashes':{p:sha(dst/p) for p in ['harness/observe.py','harness/browser_harness.py','harness/judge.py']},'standard_cli':[]}
 def run(cmd,name):
  proc=subprocess.run([sys.executable,*cmd],cwd=dst,capture_output=True,text=True,encoding='utf-8',errors='replace');(dst/name).write_text(proc.stdout+'\n'+proc.stderr,encoding='utf-8');assert proc.returncode==0,(name,proc.stdout[-2000:],proc.stderr[-2000:]);print(name,'passed',flush=True)
 run(['judge/hushan-xiangcheng/verify_sample.py','--root',str(dst),'--port','8833','--deployment-smoke'],'deployment-ui.log')
 report['ui_acceptance']=str((dst/f'judge/{TASK}/verification/deployment-acceptance.json').relative_to(ROOT))
 data=json.loads((dst/f'judge/{TASK}/verification/deployment-acceptance.json').read_text(encoding='utf-8'));assert data['pass'] and len(data['branches'])==6
 run(['judge/hushan-xiangcheng/verify_auxiliary.py','--root',str(dst),'--port','8833'],'deployment-aux.log')
 report['auxiliary_acceptance']=str((dst/f'judge/{TASK}/verification/auxiliary-acceptance.json').relative_to(ROOT))
 for key in ['ids','radical','iol','family','tone','merge']:
  run(['scripts/run_one.py','--config',f'configs/{TASK}-{key}.json','--policy','script'],f'deployment-cli-{key}.log')
  summaries=sorted((dst/f'runs/{TASK}-{key}').rglob('summary.json'));assert summaries
  report['standard_cli'].append(str(summaries[-1].relative_to(ROOT)))
 report['pass']=True;(ROOT/f'judge/{TASK}/deployment.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 for src,name in [(dst/f'judge/{TASK}/verification/deployment-acceptance.json','deployed-acceptance.json'),(dst/f'judge/{TASK}/verification/auxiliary-acceptance.json','deployed-auxiliary-acceptance.json')]:
  (ROOT/f'judge/{TASK}/verification'/name).write_bytes(src.read_bytes())
 resultpath=ROOT/'data/preparation/results/base664-0445.json';result=json.loads(resultpath.read_text(encoding='utf-8'));result.update(delivery_status='independent_six_unit_ui_and_standard_cli_passed',deployment_evidence=f'judge/{TASK}/deployment.json',deployed_acceptance=f'judge/{TASK}/verification/deployed-acceptance.json',evaluation_bundle_sha256=report['archive_sha256'],runtime_hashes=report['runtime_hashes']);resultpath.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(dst,flush=True)
if __name__=='__main__':main()
