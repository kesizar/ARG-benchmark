"""Prepare a frozen source revision. UI acceptance remains independent."""
from pathlib import Path
import base64,difflib,hashlib,json,re,shutil,zipfile
R=Path(__file__).resolve().parents[1];T='shenjia-yichan';J=R/'judge'/T;M=R/'tasks'/T/'mirror'
def write(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
 source=R/'ARG-packs/verify-84/bodies/22.html';raw=source.read_text(encoding='utf-8');(J/'source').mkdir(parents=True,exist_ok=True);shutil.copyfile(source,J/'source/original.html');M.mkdir(parents=True,exist_ok=True)
 # Preserve original source once the publicly available optional clip is acquired.
 assert (M/'loga43.mp4').stat().st_size==13657233
 cooked=raw
 (M/'index.html').write_text(cooked,encoding='utf-8')
 (J/'source/compatibility.diff').write_text(''.join(difflib.unified_diff(raw.splitlines(True),cooked.splitlines(True),fromfile='original.html',tofile='mirror/index.html')),encoding='utf-8')
 def dec(s):return bytes(b^0x5a for b in base64.b64decode(s)).decode()
 members=[]
 for line in raw.split('const _FM_ = [',1)[1].split('];',1)[0].splitlines():
  mat=re.search(r'id:"([^"]+)",_n:"([^"]+)".*?gen:(\d),_r:"([^"]+)".*?slotLabel:\x27([^\x27]+)',line)
  if mat:members.append(dict(id=mat[1],name=dec(mat[2]),gen=int(mat[3]),role=dec(mat[4]),slot_label=mat[5]))
 assert len(members)>30
 clue_ids=re.findall(r"^  '(CLUE-\d+)':",raw,re.M)
 write(J/'private-members.json',members)
 hooks={};points=[]
 for member in members:
  id=member['id'];name=member['name']
  expr='(()=>{const s=JSON.parse(localStorage.getItem("shen_family_save")||"{}");return (s.confirmedSlots||[]).includes('+json.dumps(id)+')&&(s.placedMembers||{})['+json.dumps(id)+']==='+json.dumps(name,ensure_ascii=False)+'})()'
  hooks[id]={'type':'js_truthy','expr':expr};points.append({'id':id,'hook':id,'op':'truthy','role':'diagnostic' if id in {'G3-10','G3-12','G3-13'} else 'critical','description':member['slot_label']+'的身份关系经原作批量验证确认'})
 hooks['ending']={'type':'js_truthy','expr':'(()=>{const w=document.getElementById("win-screen");return !!w&&getComputedStyle(w).display!=="none"&&w.innerText.includes("调 查 完 成")})()'}
 for id in clue_ids:hooks[id]={'type':'js_truthy','expr':'(JSON.parse(localStorage.getItem("shen_family_save")||"{}").discoveredClues||[]).includes('+json.dumps(id)+')'}
 write(J/'judge.json',{'hooks':hooks,'checkpoints':points,'events':{id:{'hook':id,'op':'truthy'} for id in clue_ids},'routes':[{'id':'investigation_complete','gates':[m['id'] for m in members if m['id'] not in {'G3-10','G3-12','G3-13'}],'ending':{'hook':'ending','op':'truthy'}}],'ending':{'hook':'ending','op':'truthy'},'answer_sha256':[]})
 cfg=json.loads((R/'configs'/f'{T}.json').read_text(encoding='utf-8'));cfg.update(runtime_layer='L1',account_requirement='none',entry_url='http://127.0.0.1:8811/index.html',allow_hosts=['127.0.0.1:8811'],limits={'max_steps':1500,'max_seconds':7200,'max_answer_submits':100},notes_for_report=['Frozen archived source; all named websites and accounts are locally simulated. Engineering readiness depends on independent UI acceptance. Original optional logo video acquired; game HTML unchanged.'])
 cfg['local_serve']={'enabled':True,'port':8811,'ready_url':cfg['entry_url'],'command':['python','scripts/serve_static.py','--root',f'tasks/{T}/mirror','--port','8811']}
 cfg['policy_script']=[{'op':'click','n':1},{'op':'give_up'}];write(R/'configs'/f'{T}.json',cfg)
 flow={'record_id':'added84:0022','source_revision':'Archived 2026-10-23 snapshot, not current live parity','members':members,'clue_ids':clue_ids,'puzzle_points':len(members)-3,'mechanical_slots':len(members),'ending_count':1,'failure_ending_count':0,'branch_semantics':'All placements are unscored drafts until successful batch confirmation. Anywrongname rejects andremoves wholeunconfirmedbatch. Minimum3drafts perbatch until<3remaining; largerbatches allowed. One finaldialogue thencompletion overlay. No need to readclues tosubmit; blankresearch completion possible if guessed.','side_branches':['All locally simulated source documents and search aliases','Eleven optional interbatch dialogue rounds1..10 and final; can batchallpeople toskip rounds','familyname removal nativeconfirm; settingsrestart nativeconfirm','4:3 ratio,fontscale1/1.25/1.5/2,help,startmenu,browserhistory,evidenceshelf','Optional ?logo=1 originalvideo retained; originalskip/errorfallback remains'],'point_policy':'One independently validated relationship perfamily slot. Source author comment35 outdated. Decoynames no separate score. Search, reading,dialogue,settings are events/mechanics, not reasoning points.','reset':'Fresh browsercontext recommended; in-game reset clearsfamilyprogress thenreloads. Notes/preferences retained by author.','risks':['Source hints and dialogue may directly reveal some names; difficultyreview required','Obfuscated answer map remains game source; no modeltools source access','Unchecked finalwin after allconfirmed persists onlyvia completingdialogue, reloadmay require careful recovery review','Three spouse names have no textual documentary evidence; diagnostic only']}
 write(J/'checkpoint-spec.json',flow)
 write(R/'tasks'/T/'provenance.json',{'record_id':'added84:0022','source_snapshot':source.relative_to(R).as_posix(),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'original_url':'https://pcz58ruc.mule.page/沈家遗产_游戏原型.html','changes':[],'missing_optional_assets':[],'files':[{'path':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in M.iterdir() if p.is_file()],'video_source':'https://pcz58ruc.mule.page/loga43.mp4'})
 (R/'tasks'/T/'README.md').write_text('沈家遗产（added84:0022）\n\nL1 本地模拟2003年网络调查。启动 python scripts/run_one.py --config configs/shenjia-yichan.json --policy script。模型模式用--policy llm并由评测侧配置API，资源包不含密钥。本次准备不调用模型。浏览器需Edge/Chrome或Playwright Chromium、Python依赖见评测包requirements。服务根仅tasks/shenjia-yichan/mirror，勿托管评测包根或judge。每局新context清空进度；原作设置重开亦可，但笔记/偏好按原作保留。独立人物关系按提交验证后计分，填写草稿不计分。唯一调查完成结局，验证错误可重试不算死亡。可选?logo=1片头视频缺失；默认无片头，不宣称全部视听材料完整。当前难度/直接揭示答案等问题待内容复核，工程通过不等于正式计分批准。\n',encoding='utf-8')
 zip_path=R/'packs'/f'{T}.resources.zip'
 with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
  for f in M.iterdir():z.write(f,f.name)
 print('members',len(members),'clues',len(clue_ids))
if __name__=='__main__':main()
