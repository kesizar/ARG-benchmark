from pathlib import Path
import json,hashlib,zipfile,subprocess,sys,threading,functools,http.server,importlib.util,difflib
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];T=R/'tasks/guimi-qiyun';O=R/'runs/guimi-qiyun';A=T/'audit'
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def server(root,port):
 class Quiet(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*a):pass
 s=http.server.ThreadingHTTPServer(('127.0.0.1',port),functools.partial(Quiet,directory=str(root)));threading.Thread(target=s.serve_forever,daemon=True).start();return s
def main():
 ui=json.loads((O/'ui-evidence.json').read_text(encoding='utf-8'))
 spec=importlib.util.spec_from_file_location('auditjudge',R/'judge/guimi-qiyun/audit_judge.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 tests=[]
 for e in ui['episodes']:
  verdict=mod.judge(True,e['ending']);assert verdict['route'] in e['hooks'] and e['hooks'][verdict['route']];assert verdict['reasoning_points']==0;tests.append({'episode':e['episode'],'verdict':verdict})
 assert mod.judge(False,'💎 完美清算')['route'] is None
 write(O/'judge-tests.json',{'independent_saved_visible_outcome_checks':tests,'hidden_ending_rejected':True,'synthetic_state_injection':False})
 src=(A/'original.html').read_text(encoding='utf-8').splitlines(True);(A/'source-fragments.txt').write_text(''.join(f'{i+1}: {src[i]}' for lo,hi in [(850,873),(924,1048),(1187,1214),(1255,1290)] for i in range(lo,min(hi,len(src)))),encoding='utf-8')
 for orig,dest,name in [('original-config.json',R/'configs/guimi-qiyun.json','config.diff'),('original-judge.json',R/'judge/guimi-qiyun/judge.json','judge.diff')]:
  (A/name).write_text(''.join(difflib.unified_diff((A/orig).read_text(encoding='utf-8').splitlines(True),dest.read_text(encoding='utf-8').splitlines(True),fromfile=orig,tofile=str(dest.relative_to(R)))),encoding='utf-8')
 subprocess.run([sys.executable,str(R/'scripts/build_prepared_bundle.py'),'--task','guimi-qiyun'],check=True,cwd=R)
 prepared=R/'packs/guimi-qiyun.prepared.zip'
 with zipfile.ZipFile(prepared,'a',compression=zipfile.ZIP_DEFLATED) as z:
  for p in [R/'judge/guimi-qiyun/audit_judge.py',O/'judge-tests.json',O/'ui-evidence.json']+list(A.glob('*.json'))+[A/'source-fragments.txt']:
   z.write(p,p.relative_to(R).as_posix())
 resources=R/'packs/guimi-qiyun.resources.zip'
 with zipfile.ZipFile(resources,'w',compression=zipfile.ZIP_DEFLATED) as z:
  for p in (T/'mirror').rglob('*'):
   if p.is_file():z.write(p,p.relative_to(T/'mirror').as_posix())
 packages=[];deploy=[]
 with sync_playwright() as pw:
  b=pw.chromium.launch(channel='msedge',headless=True)
  for label,archive,port in [('prepared',prepared,8832),('resources',resources,8833)]:
   extract=O/('unpacked-'+label);extract.mkdir(exist_ok=True)
   with zipfile.ZipFile(archive) as z:
    z.extractall(extract);assert all((extract/n).read_bytes()==z.read(n) for n in z.namelist() if not n.endswith('/'))
   root=extract/'tasks/guimi-qiyun/mirror' if label=='prepared' else extract;srv=server(root,port);c=b.new_context(viewport={'width':1366,'height':900});p=c.new_page();p.goto(f'http://127.0.0.1:{port}/',wait_until='domcontentloaded');p.locator('#btnStart').click()
   for _ in range(30):
    choices=p.locator('#chapterArea .opt');choices.first.click();p.locator('#chapterArea button[onclick="nextChapter()"]').click()
   title=p.locator('#endTitle').inner_text();assert '鱼死网破' in title;assert mod.judge(True,title)['route']=='both';p.screenshot(path=str(O/(label+'-independent-ending.png')),full_page=True);p.reload();assert p.evaluate('S.ch===0 && S.evid.length===0 && !S.done');c.close();srv.shutdown()
   if label=='prepared':
    cfg=json.loads((extract/'configs/guimi-qiyun.json').read_text(encoding='utf-8'));cfg['entry_url']=f'http://127.0.0.1:{port}/';cfg['allow_hosts']=[f'127.0.0.1:{port}'];cfg['local_serve']['port']=port;cfg['local_serve']['ready_url']=cfg['entry_url'];cfg['local_serve']['command'][-1]=str(port);write(extract/'configs/guimi-qiyun.json',cfg)
   packages.append({'archive':str(archive.relative_to(R)),'sha256':sha(archive),'bytes':archive.stat().st_size});deploy.append({'label':label,'root':str(extract),'port':port,'archive_members_verified':True,'game_sha256':sha(root/'index.html'),'ending':title,'normal_ui_30_chapters':True,'fresh_context':True,'refresh_reset':True,'base_environment':'same Windows/Edge/Python, no cross-OS claim'})
  b.close()
 write(O/'packages.json',packages);write(O/'deployment.json',deploy)
 # Update outer archive hash after adding audit files; the embedded manifest still pins every original runtime member.
 manifest=json.loads((R/'packs/guimi-qiyun.prepared.manifest.json').read_text(encoding='utf-8'));manifest['archive_sha256']=sha(prepared);write(R/'packs/guimi-qiyun.prepared.manifest.json',manifest)
 result={'record_id':'base664:0429','task_id':'guimi-qiyun','title':'闺蜜正在偷走你气运','runtime_layer':'L1','account_requirement':'none','status':'recovery_audited_original_highest_ending_unreachable','resource_status':'all_gameplay_inline_optional_donation_image_missing','integration_status':'local_static_config_complete','content_status':'30_chapters_all_choices_failure_payloads_replies_mail_notes_mapped','judge_status':'independent_diagnostic_outcomes_zero_reasoning_checkpoints','ui_status':'full_source_scheduled_option_ordinal_and_collection_sweeps_no_independent_solving_claim','delivery_status':'two_archives_independent_30_chapter_deployment_passed','engineering_ready':False,'formal_ready':False,'formal_scoring_suitability':'ineligible_pending_authoritative_reachable_ending_and_validated_reasoning_gate','stages':{'resource_audit':'complete_with_optional_missing_image','integration':'recovery_runnable','content':'all_authored_branches_mapped_and_perfect_egg_proven_unreachable','judge':'diagnostics_only_independent_checks_passed','ui':'reachable_endings_choices_failures_refresh_and_context_reset_verified_see_coverage','delivery':'two_archives_independent_extraction_hash_UI_acceptance_passed','review':'HANDOFF_parent_review_required'},'findings':['Perfect needs >=4 views >=60; optimistic bf max18 and fam max56 prove impossible. Only three possible qualifying people. Egg nested in perfect also impossible.','No answer validation: note comparison click grants fixed reward; top toolbar bypasses AP; option failure still grants hole/gotEv. No manufactured reasoning points.','Missing optional donation image; source unchanged. Public recovery TLS failure captured.','Generic ending restart shows intro without clearing state; reload is reliable reset.'],'coverage':{'ui_episodes':len(ui['episodes']),'observed_endings':sorted({e['ending'] for e in ui['episodes']}),'source_all_options':sum(len(ch.get('opts',[])) for ch in json.loads((A/'content-map.json').read_text(encoding='utf-8'))['chapters']),'limitations':'Source-scheduled fixtures do not prove reasoning solvability. All choices and failures mapped; not every mutually exclusive historical state combination replayed. Perfect/egg blocked by original logic.'},'evidence':['tasks/guimi-qiyun/README.md','tasks/guimi-qiyun/provenance.json','tasks/guimi-qiyun/audit/resource-audit.json','tasks/guimi-qiyun/audit/content-map.json','tasks/guimi-qiyun/audit/reachability.json','tasks/guimi-qiyun/audit/source-fragments.txt','judge/guimi-qiyun/checkpoint-spec.json','runs/guimi-qiyun/ui-evidence.json','runs/guimi-qiyun/judge-tests.json','runs/guimi-qiyun/packages.json','runs/guimi-qiyun/deployment.json'],'packages':packages,'independent_acceptance':deploy,'resume':'Seek author-confirmed corrected snapshot and missing original optional image. Do not patch thresholds/rewards speculatively. Reuse source/UI evidence for unchanged portions; recheck affected paths after authoritative fix.','paid_api_calls':0,'handoff':'HANDOFF'}
 write(R/'data/preparation/results/base664-0429.json',result);print(json.dumps({'packages':packages,'result':'data/preparation/results/base664-0429.json'},ensure_ascii=False))
if __name__=='__main__':main()
