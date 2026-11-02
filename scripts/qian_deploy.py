"""Independent collection deployment on three dedicated ports, then standard CLI."""
import concurrent.futures,hashlib,json,subprocess,sys,uuid,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];TASK='qian-anon'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 archive=ROOT/f'packs/{TASK}.prepared.zip';dst=ROOT/'runs'/f'qian-deployment-{uuid.uuid4().hex[:8]}';dst.mkdir(parents=True)
 with zipfile.ZipFile(archive) as z:assert z.testzip() is None;z.extractall(dst)
 manifest=json.loads((dst/'BUNDLE-MANIFEST.json').read_text(encoding='utf-8'))
 for f in manifest['files']:assert sha(dst/f['path'])==f['sha256'],f['path']
 report={'archive':archive.relative_to(ROOT).as_posix(),'archive_sha256':sha(archive),'deployment_root':str(dst),'crc_ok':True,'all_manifest_hashes_match':True,'model_api_used':False,'environment':'Same Windows host; preinstalled Python dependencies and Edge/Chromium, not a clean install or cross-OS test.','runtime_hashes':{p:sha(dst/p) for p in ['harness/observe.py','harness/browser_harness.py','harness/judge.py']},'standard_cli':[]}
 def run(cmd,name):
  p=subprocess.run([sys.executable,*cmd],cwd=dst,capture_output=True,text=True,encoding='utf-8',errors='replace');(dst/name).write_text(p.stdout+'\n'+p.stderr,encoding='utf-8');assert p.returncode==0,(name,p.stdout[-2000:],p.stderr[-2000:]);print(name,'passed',flush=True)
 def group(port,units):
  results=[]
  for key in units:
   script='verify_surf.py' if key=='surf' else 'verify_sample.py';cmd=[f'judge/{TASK}/{script}','--root',str(dst),'--port',str(port),'--unit',key]
   if key!='surf':cmd.append('--deployment-smoke')
   run(cmd,f'deployment-ui-{key}.log');evidence=dst/f'judge/{TASK}/verification/{key}-acceptance.json' if key=='surf' else dst/f'judge/{TASK}/verification/{key}-deployment-acceptance.json'
   data=json.loads(evidence.read_text(encoding='utf-8'));assert data['pass'];results.append({'unit':key,'evidence':evidence.relative_to(ROOT).as_posix(),'ending_ids':sorted({b['score']['route_id'] for b in data['branches']})})
  return results
 groups=[(8831,['quiz','hunt','gal']),(8832,['pipa','cross','maze']),(8833,['surf'])]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:report['unit_ui']=[r for group_result in pool.map(lambda item:group(*item),groups) for r in group_result]
 assert len(report['unit_ui'])==7
 run([f'judge/{TASK}/verify_auxiliary.py','--root',str(dst),'--unit','quiz','--port','8833'],'deployment-auxiliary.log')
 for key in ['quiz','pipa','cross','hunt','surf','maze','gal']:
  run(['scripts/run_one.py','--config',f'configs/{TASK}-{key}.json','--policy','script'],f'deployment-cli-{key}.log');summaries=sorted((dst/f'runs/{TASK}-{key}').rglob('summary.json'));assert summaries;report['standard_cli'].append(summaries[-1].relative_to(ROOT).as_posix())
 report['pass']=True;(ROOT/f'judge/{TASK}/deployment.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 result_path=ROOT/'data/preparation/results/base664-0521.json';r=json.loads(result_path.read_text(encoding='utf-8'));r.update(status='engineering_ready_content_review_required',delivery_status='independent_seven_unit_ui_and_standard_cli_passed',evaluation_bundle_sha256=report['archive_sha256'],deployment_evidence=f'judge/{TASK}/deployment.json',runtime_hashes=report['runtime_hashes']);result_path.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(dst,flush=True)
if __name__=='__main__':main()
