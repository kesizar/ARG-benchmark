"""Package incomplete recovery evidence without publishing a runnable task."""
from pathlib import Path
import hashlib,json,zipfile,sys
R=Path(__file__).resolve().parents[1];T='ribbon-archive';J=R/'judge'/T;D=R/'tasks'/T
def w(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
def main():
 a=json.loads((J/'source/access-audit.json').read_text(encoding='utf8'));D.mkdir(parents=True,exist_ok=True)
 review='''Ribbon Archive / base664:0181 — HANDOFF: recovery only

Entry: https://x.com/ribbonarchive05 . No catalogue config exists; stable task id ribbon-archive.
The 125725-byte original is a complete HTML document but only a partial X profile render. It advertises 29 posts, embeds five distinct status URLs and shows login/signup. Those five public post pages were recovered through HTTP 200. Replies/media/about redirect to /i/jf/onboarding/web?...mode=login and return a generic X shell rather than timelines. The five recovered posts concern dreams, longer hair, mirrors and games; no verifiable authored puzzle validator, answer submission, branching state, ending or failure condition is exposed. This is narrative evidence, not five reasoning checkpoints. No completion or disappearance claim can be inferred from absence.

Playwright Edge normal public navigation failed with ERR_HTTP_RESPONSE_CODE_FAILURE, while urllib HTTP profile and five posts succeeded. This is a browser-route failure, not proof the site is dead or login is always required. Account requirement remains unknown; no personal account was used or purchased. X frontend assets, profile images and remote APIs remain external dependencies; dynamic JS entry references are enumerated in access-audit.json. No complete offline game or operational L3 task is established.

Full flow, all branches/endings, independent judge, normal UI positive/negative/reset tests and two independent executable deployments are NOT VERIFIED. No fabricated judge/config or prepared package is delivered. The recovery ZIP is archival evidence only, includes raw originals and public responses, and must not be served as an offline game. No edits were applied to original HTML. Judge-side material stays private.

Resume: acquire the complete 29-post timeline, replies/threads and all clue media from an authorized public export or reusable test account; establish original game scope and formal terminal conditions from author evidence; preserve originals/media hashes; map actual inference points before implementing judge; then validate normal UI success/failure/reset and both separated executable deliveries. If genuine account conditions apply, prepare a test account and verified reset before enabling L3. Ports 8821–8823 were reserved but unused and may be released.

Audit command: mirror/harness/.venv/Scripts/python.exe scripts/ribbon_archive_audit.py . Bounded public read-only requests; no paid model API, sends, login, state mutation or push. Existing Windows Python/Playwright/msedge reused. The original workspace audit required the exact-command sandbox escalation; no platform security controls bypassed.
'''
 (J/'review.md').write_text(review,encoding='utf8');(D/'README.md').write_text(review,encoding='utf8')
 w(D/'provenance.json',{'record_id':'base664:0181','task_id':T,'entry':'https://x.com/ribbonarchive05','snapshot':a['snapshot'],'audit':'judge/ribbon-archive/source/access-audit.json','changes':[],'resource_completeness':'partial_public_x_profile_and_five_posts','account_requirement':'unknown','runtime_layer_candidate':'L3','runtime_layer_verified':False})
 files=[*sorted(J.rglob('*')),*sorted(D.rglob('*')),R/'scripts/ribbon_archive_audit.py',Path(__file__)]
 files=[p for p in files if p.is_file() and p.name!='recovery-verification.json'];manifest=[{'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]
 z=R/'packs'/f'{T}.recovery.zip'
 with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as q:
  for p in files:q.write(p,p.relative_to(R).as_posix())
  q.writestr('RECOVERY-MANIFEST.json',json.dumps(manifest,indent=2))
 dest=R/'runs'/f'{T}-recovery-extracted';dest.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(z) as q:
  assert q.testzip() is None;q.extractall(dest)
 for item in manifest:assert hashlib.sha256((dest/item['path']).read_bytes()).hexdigest()==item['sha256']
 w(J/'recovery-verification.json',{'zip_crc_passed':True,'all_extracted_hashes_passed':True,'file_count':len(manifest),'extracted_to':dest.relative_to(R).as_posix(),'scope':'archival integrity only; no executable deployment','python':sys.version})
 result={'record_id':'base664:0181','task_id':T,'title':'Ribbon Archive','status':'blocked_incomplete_resources_and_browser_access','runtime_layer':'L3','runtime_layer_scope':'candidate only, no executable config','account_requirement':'unknown','ready_for_local_execution':False,'ready_for_formal_scoring':False,'resource_status':'partial_x_profile_and_five_public_posts_recovered; 29_post_timeline_and_threads_missing','integration_status':'not_implemented_no_verified_browser_route','flow_status':'unverified_no_authored_puzzle_or_terminal_state_established','judge_status':'not_implemented_no_invented_checkpoints','delivery_status':'recovery_zip_integrity_verified_only; executable_two_package_deployment_not_attempted','model_api_used':False,'model_api_calls':0,'config':None,'resources_bundle':None,'evaluation_bundle':None,'recovery_bundle':z.relative_to(R).as_posix(),'recovery_sha256':hashlib.sha256(z.read_bytes()).hexdigest(),'evidence':['judge/ribbon-archive/source/access-audit.json','judge/ribbon-archive/source/visible-text.txt','judge/ribbon-archive/review.md','judge/ribbon-archive/recovery-verification.json','tasks/ribbon-archive/provenance.json'],'checks':{'original_bytes':125725,'public_status_pages_recovered':5,'profile_http_status':200,'browser_navigation_passed':False,'full_29_posts_recovered':False,'no_original_changes':True,'zip_crc_passed':True,'all_extracted_hashes_passed':True},'limits':['HTTP accessibility does not establish interactive browser usability.','Generic replies/media/about shell gives no complete archive.','No verified reasoning, formal endings/failures, judge, UI success/negative/reset or independent executable deployments.','Runtime L3 is a candidate classification only; account requirement unknown.'],'handoff':'See judge/ribbon-archive/review.md; reserved ports 8821–8823 unused.'}
 w(R/'data/preparation/results/base664-0181.json',result);print(json.dumps({'result':'data/preparation/results/base664-0181.json','recovery':result['recovery_bundle'],'files':len(manifest),'status':result['status']}))
if __name__=='__main__':main()
