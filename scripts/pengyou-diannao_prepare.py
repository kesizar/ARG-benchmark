from pathlib import Path
import json,shutil,hashlib,re
R=Path(__file__).resolve().parents[1];T='pengyou-diannao';D=R/f'tasks/{T}/mirror';D.mkdir(parents=True,exist_ok=True)
manifest=json.loads((R/f'judge/{T}/source/live-manifest.json').read_text(encoding='utf-8'));valid=[]
for f in manifest:
 if f.get('status')==200 and re.fullmatch(r'[^/${}]+\.(html|jpg)',f['path']):
  shutil.copyfile(R/f'judge/{T}/source/live'/f['path'],D/f['path']);valid.append(f)
c=json.loads((R/'configs/duoluoleisi.json').read_text(encoding='utf-8'));c.update(id=T,entry_url='http://127.0.0.1:8821/index.html',allow_hosts=['127.0.0.1:8821'],judge_path=f'judge/{T}/judge.json',account_requirement='none');c['model_visible']['title']='我朋友留下的电脑界面';c['local_serve']['command'][3]=f'tasks/{T}/mirror';c['limits'].update(max_steps=1200,max_seconds=3600);c['notes_for_report']=['Frozen live 2026-10-26 full version; archived entry alone was incomplete.','Simulated accounts/payment are entirely local fiction, no real account or purchase.','Fresh browser context clears localStorage. In-game restart clears all data including saves.'];c['actions_enabled']+=['switch_tab','close_tab'];(R/f'configs/{T}.json').write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf-8')
text=(D/'review.html').read_text(encoding='utf-8');rejects=[x=='true' for x in re.findall(r'shouldReject: (true|false)',text)];assert len(rejects)==30
hooks={};checkpoints=[];adopt=[]
for i,reject in enumerate(rejects):
 key=f'article_{i:02d}';hooks[key]={'type':'js_truthy','expr':f'JSON.parse(localStorage.getItem("review_processed")||"[]").includes({i})'};checkpoints.append({'id':key,'hook':key,'op':'truthy',**({'role':'optional'} if reject else {})})
 if not reject:adopt.append(key)
for key,storage in [('necklace_code','has_secret_code'),('editor_login','editor_logged_in')]:hooks[key]={'type':'js_truthy','expr':f'localStorage.getItem("{storage}")==="true"'};checkpoints.append({'id':key,'hook':key,'op':'truthy'})
for key,path in [('surface','crash.html'),('true','true_ending.html'),('hidden','hidden_ending.html')]:hooks[key]={'type':'js_truthy','expr':f'location.pathname.endsWith("/{path}") && !!document.querySelector(".xp-dialog")'}
hooks={k:v for k,v in hooks.items() if not k.startswith('article_')};hooks['processed']={'type':'localstorage','key':'review_processed','mode':'json_path','path':''}
for cp in checkpoints:
 if cp['id'].startswith('article_'):cp.update(hook='processed',op='includes',value=int(cp['id'][8:]))
j={'hooks':hooks,'checkpoints':[cp for cp in checkpoints if cp['id']!='necklace_code'],'events':{'necklace_search':{'hook':'necklace_code','op':'truthy'}},'routes':[{'id':key,'tier':'normal','gates':[] if key=='surface' else ['editor_login'],**({'gate_groups':[{'ids':adopt,'required':15}]} if key=='surface' else {}),'ending':{'hook':key,'op':'truthy'}} for key in ['surface','true','hidden']],'ending':{'hook':'true','op':'truthy'},'answer_sha256':[],'answer_hash_file':None,'request_milestones':[],'submit_conclusion':{'enabled':False,'schema':None},'rubric_path':None};(R/f'judge/{T}/judge.json').write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
p={'record_id':'added84:0082','origin':'https://myfriendpc2005.pages.dev/','version':'live frozen 2026-10-26','archived_entry_sha256':'48037d6c205464bfed259d1eb81673c4652917de4faf4919c21af46554c8cdeb','live_entry_sha256':valid[0]['sha256'],'game_changes':[],'files':valid,'excluded_crawler_false_positive':'${isSeller (dynamic CSS expression was not a real file)'};(R/f'tasks/{T}/provenance.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8');print('prepared',len(valid),'files;adopt',len(adopt),'reject',sum(rejects))
