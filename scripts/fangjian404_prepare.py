"""Freeze record359; evaluator inventory preserves original fixed text and logic."""
import ast,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];TASK='fangjian-404-yingzi'
def write(p,o):p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8')
def literal(s):
 s=re.sub(r'^\s*//.*$','',s,flags=re.M)
 s=re.sub(r'\b(announce|neighbor|chat|factory|strange|basement|deleted|id|title|author|replies|last|content|locked|needLogin|hidden|forbidden|editable|editContent|time|text|date|board|postId|cult|main|sub):',r"'\1':",s)
 s=re.sub(r'\btrue\b','True',s);s=re.sub(r'\bfalse\b','False',s)
 return ast.literal_eval(s)
def main():
 raw=(ROOT/'ARG-packs/verify-416/bodies/359.html').read_bytes();assert hashlib.sha256(raw).hexdigest()=='f8dd2cb93e12ed97b5e1ce684173b93e73be8cb22cd1e8b892c630398cf7fb03';s=raw.decode('utf-8');mirror=ROOT/f'tasks/{TASK}/mirror';source=ROOT/f'judge/{TASK}/source';mirror.mkdir(parents=True,exist_ok=True);source.mkdir(parents=True,exist_ok=True);(mirror/'index.html').write_bytes(raw);(source/'359.original.html').write_bytes(raw)
 posts=literal(re.search(r'const posts = (\{[\s\S]*?\n\});',s).group(1));logs=literal(re.search(r'const guardianLogs = (\[[\s\S]*?\n\]);',s).group(1));keywords=literal(re.search(r'const searchKeywords = (\{[\s\S]*?\n\});',s).group(1))
 write(f'judge/{TASK}/source-inventory.json',{'posts':posts,'guardian_logs':logs,'search_keywords':keywords,'fake_keywords':literal(re.search(r'const fakeKeywords = (\[[^\n]+\]);',s).group(1)),'forbidden_flavor':literal(re.search(r'const forbiddenTexts = (\[[\s\S]*?\n\]);',s).group(1))})
 write(f'tasks/{TASK}/provenance.json',{'record_id':'base664:0359','source_snapshot':'ARG-packs/verify-416/bodies/359.html','canonical_url':'https://yingzizzzz936-ux.github.io/404-game/','original_sha256':hashlib.sha256(raw).hexdigest(),'original_bytes':len(raw),'runtime_sha256':hashlib.sha256(raw).hexdigest(),'required_external_assets':[],'compatibility_changes':[]})
 cfg=json.loads((ROOT/'configs/qian-anon-cross.json').read_text(encoding='utf-8'));cfg.update(id=TASK,category='web_puzzle',judge_path=f'judge/{TASK}/judge.json',seed=20260359);cfg['local_serve']['command'][3]=f'tasks/{TASK}/mirror';cfg['model_visible']={'title':'404——不存在的房间','intro':'你在本地托管的论坛解谜中，寻找线索、推理账号与关键操作，完成故事。只用屏幕信息与列出的动作；站内人物和账号是游戏虚构内容。'};cfg['limits'].update(max_steps=360,max_answer_submits=30);cfg['notes_for_report']=['Original record base664:0359; all site/account functions are local fiction; source-view affordance not currently exposed to model.'];write(f'configs/{TASK}.json',cfg)
 hooks={};checkpoints=[]
 for cid,expr,role in [('admin_login',"typeof currentUser!=='undefined'&&currentUser==='menghua'",'critical'),('offering_cancelled',"typeof offeringCanceled!=='undefined'&&offeringCanceled===true",'critical'),('brother_login',"typeof currentUser!=='undefined'&&currentUser==='menghui19'",'optional'),('guardian_login',"typeof currentUser!=='undefined'&&currentUser==='chenshouyi'",'optional')]:hooks[cid]={'type':'js_truthy','expr':expr};checkpoints.append({'id':cid,'hook':cid,'op':'truthy','role':role})
 routes=[]
 for eid,term,tier,gates in [('true','真结局：解脱','good',['admin_login','offering_cancelled']),('bad','坏结局：留下','bad',['admin_login','offering_cancelled']),('hidden','隐藏结局：守护者','normal',['admin_login','offering_cancelled']),('loop_failure','假结局：循环继续','bad',[])]:
  hooks[eid]={'type':'js_truthy','expr':f"getComputedStyle(document.querySelector('#ending-modal')).display!=='none'&&document.querySelector('#ending-title').textContent.includes({json.dumps(term,ensure_ascii=False)})"};routes.append({'id':eid,'tier':tier,'gates':gates,'ending':{'hook':eid,'op':'truthy'}})
 judge={'hooks':hooks,'checkpoints':checkpoints,'events':{},'routes':routes,'ending':None,'request_milestones':[],'submit_conclusion':{'enabled':False,'schema':None}};write(f'judge/{TASK}/judge.json',judge)
 print({'posts_per_board':{k:len(v) for k,v in posts.items()},'guardian_logs':len(logs),'search_keywords':len(keywords)})
if __name__=='__main__':main()
