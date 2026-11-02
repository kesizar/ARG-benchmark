import json,zipfile,subprocess,sys,hashlib,difflib
from pathlib import Path
r=Path(__file__).resolve().parents[1]
p=r/'configs/xinshiji.json';old=p.read_text('utf8');backup=r/'tasks/xinshiji/source/config.before-v2.json'
if not backup.exists():backup.write_text(old,encoding='utf8')
d=json.loads(old)
for k in ['entry_url']:d[k]=d[k].replace(':8821',':8823')
d['allow_hosts']=['127.0.0.1:8823'];d['local_serve']['command'][-1]='8823';d['local_serve']['port']=8823;d['local_serve']['ready_url']=d['entry_url'];d['limits'].update(max_steps=450,max_seconds=5400)
d['notes_for_report']=['Engineering UI verified, formal scoring held for date/portrait/symbol-count clue ambiguities; see judge/xinshiji/review.md.','Original game unchanged; missing decorative beijing.jpg has authored onerror hide fallback.','Company search can skip six optional reasoning points. Survey is an unscored event.']
new=json.dumps(d,ensure_ascii=False,indent=2)+'\n';p.write_text(new,encoding='utf8')
(r/'judge/xinshiji/recovery/config-v2.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True))),encoding='utf8')
p=r/'judge/xinshiji/checkpoint-spec.json';d=json.loads(p.read_text('utf8'));d['readiness']='engineering verified; formal content review required for explicit ambiguities';d['failure']='Normal UI verified: manager wrong food/hobby retry, wrong parents/date modal, wrong member login, portrait wrong resets, survey rejection then existing card replay may recover. No separate death ending.';d['resource_soft_omission']='beijing.jpg is decorative cover; original onerror hides; all moments clue text works';d['current_judge']='5 critical and6 optional reasoning checkpoints; questionnaire is unscored event; actual ending and three flags required';d['review']='judge/xinshiji/review.md';p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
(r/'tasks/xinshiji/README.md').write_text('''# 新世纪乐园失踪案

Engineering UI verified; formal scoring content review required. Original91 game files unchanged. One original cosmetic moments cover beijing.jpg is absent at origin and has an authored onerror hide fallback. No puzzle material is replaced.

From evaluator root: python scripts/serve_static.py --root tasks/xinshiji/mirror --port8823 (insert a space between --port and8823). Stop Ctrl-C. Start at http://127.0.0.1:8823/index.html in a new browser context. The original new-game flow and ending restart clear local/session storage; Continue preserves the saved investigation. Python3.11+, requirements.txt packages, installed Edge/Chrome or Playwright Chromium are external prerequisites. No API/account needed for script verification; member credentials are fictional game clues.

Use python scripts/run_one.py --config configs/xinshiji.json --policy script for a give-up smoke episode. LLM calls require separately supplied infrastructure credentials and are not part of this preparation. Serve only the mirror directory; evaluator judge files must not be hosted.

Normal UI covers all authored decision branches, one full ending, wrong-answer retries, survey rejection/replay, member portraits, scene switching, Continue and new-game/ending resets. Five critical and six optional reasoning points are tracked; survey is unscored. Optional branches may be skipped via direct company search. See judge/xinshiji/review.md for date, portrait and icon-count ambiguities. Engineering success does not approve these for formal scoring.
'''.replace('--port8823 (insert a space between --port and8823)','--port 8823'),encoding='utf8')
subprocess.run([sys.executable,str(r/'scripts/build_prepared_bundle.py'),'--task','xinshiji'],cwd=r,check=True)
archive=r/'packs/xinshiji.prepared.zip';tmp=r/'packs/xinshiji.prepared.v2-tmp.zip'
extra=['scripts/xinshiji_ui.py','scripts/xinshiji_judge_probe.py','scripts/xinshiji_mandatory_judge_ui.py','scripts/xinshiji_branches_ui.py','scripts/xinshiji_garden_delta_ui.py','judge/xinshiji/review.md','judge/xinshiji/recovery/branches/ui.json','judge/xinshiji/recovery/mandatory-judge/ui-8823.json','judge/xinshiji/recovery/clues/audit.json']
with zipfile.ZipFile(archive) as src,zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as dst:
 for n in src.namelist():
  if n!='BUNDLE-MANIFEST.json':dst.writestr(n,src.read(n))
 manifest=json.loads(src.read('BUNDLE-MANIFEST.json'));manifest['readiness']='Engineering verified; formal scoring held for documented clue ambiguities.'
 for n in extra:
  f=r/n;dst.write(f,n);manifest['files'].append({'path':n,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size})
 dst.writestr('BUNDLE-MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
tmp.replace(archive)
resource=r/'packs/xinshiji.resources.zip'
with zipfile.ZipFile(resource,'w',zipfile.ZIP_DEFLATED)as z:
 for f in (r/'tasks/xinshiji/mirror').rglob('*'):
  if f.is_file():z.write(f,f.relative_to(r/'tasks/xinshiji/mirror'))
base=r/'runs/xinshiji-independent/v2';base.mkdir(parents=True,exist_ok=True)
records=[]
for kind,f in [('resources',resource),('evaluation',archive)]:
 dest=base/kind
 if dest.exists():raise RuntimeError('Refuse overwrite '+str(dest))
 dest.mkdir();zipfile.ZipFile(f).extractall(dest)
 with zipfile.ZipFile(f)as z:
  assert z.testzip() is None
  assert all(hashlib.sha256((dest/n).read_bytes()).digest()==hashlib.sha256(z.read(n)).digest() for n in z.namelist() if not n.endswith('/'))
 records.append({'kind':kind,'path':f.relative_to(r).as_posix(),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size,'extracted_to':dest.relative_to(r).as_posix(),'crc_and_all_bytes_match':True})
(r/'judge/xinshiji/recovery/packages-v2.json').write_text(json.dumps({'packages':records,'source_game_bytes_unchanged':True,'cross_os_tested':False,'ui_reuse':'same game assets as independently UI-tested v1; new judge delta in mandatory-judge and branches logs','cli_pending':True},ensure_ascii=False,indent=2),encoding='utf8')
print('V2 packages extracted; game91 files unchanged; CLI delta pending.')
