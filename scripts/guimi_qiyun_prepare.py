from pathlib import Path
import json,re,hashlib,urllib.request,urllib.parse,difflib
R=Path(__file__).resolve().parents[1]; T=R/'tasks/guimi-qiyun'; A=T/'audit'; M=T/'mirror'; J=R/'judge/guimi-qiyun'
for d in [A,M,J,R/'runs/guimi-qiyun']:d.mkdir(parents=True,exist_ok=True)
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
raw=(R/'ARG-packs/verify-416/bodies/429.html').read_bytes(); s=raw.decode('utf-8'); (A/'original.html').write_bytes(raw); (M/'index.html').write_bytes(raw)
assets=[]
for ref in re.findall(r'(?:src|href)=["\']([^"\']+)',s):
 if ref.startswith('#'):continue
 url=urllib.parse.urljoin('https://886ced7870114bb3997ee26c49986458.app.workbuddy.link/',urllib.parse.quote(ref))
 item={'reference':ref,'url':url,'role':'optional donation image; original explicitly says does not affect completion'}
 try:
  with urllib.request.urlopen(url,timeout=25) as response:
   data=response.read(); item.update(status=response.status,content_type=response.headers.get('Content-Type'),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
  if item['content_type'].startswith('image/'):(M/ref).write_bytes(data); item['recovered']=True
  else:item['recovered']=False
 except Exception as e:item.update(recovered=False,error=str(e))
 assets.append(item)
write(A/'resource-audit.json',{'html_bytes':len(raw),'html_sha256':hashlib.sha256(raw).hexdigest(),'complete':s.rstrip().endswith('</html>'),'assets':assets,'scripts':'all inline','styles':'all inline','account_requirement':'none','external_gameplay_requests':[],'localization':'byte-identical original; no patches'})
c=json.loads((R/'configs/guimi-qiyun.json').read_text(encoding='utf-8'))
if not (A/'original-config.json').exists():write(A/'original-config.json',c)
if not (A/'original-judge.json').exists():write(A/'original-judge.json',json.loads((J/'judge.json').read_text(encoding='utf-8')))
c.update(runtime_layer='L1',account_requirement='none',entry_url='http://127.0.0.1:8831/',allow_hosts=['127.0.0.1:8831']);c['local_serve']={'enabled':True,'command':['python','scripts/serve_static.py','--root','tasks/guimi-qiyun/mirror','--port','8831'],'cwd':'.','ready_url':c['entry_url'],'ready_timeout_s':30,'port':8831}
c['notes_for_report']=['Pinned base664:0429; no paid API needed. All story branches retained. Original unvalidated compare buttons and unconditional hole rewards make this a narrative choice/resource task; no formal reasoning points certified. Source-derived route schedules are engineering regression fixtures, not proof of independent solving.']
write(R/'configs/guimi-qiyun.json',c)
titles={'perfect':'💎 完美清算','clean':'⚔️ 干净利落','bitter':'🩸 惨胜','both':'🌪 鱼死网破','killed':'💀 被反杀'}
hooks={k:{'type':'js_truthy','expr':"document.querySelector('#screenEnd').classList.contains('active') && document.querySelector('#endTitle').textContent === "+json.dumps(v,ensure_ascii=False)} for k,v in titles.items()}
hooks['egg']={'type':'js_truthy','expr':"document.querySelector('#screenEnd').classList.contains('active') && document.querySelector('#endTitle').textContent === '💎 完美清算' && document.querySelector('#endBody').textContent.includes('【隐藏彩蛋】')"}
judge={'hooks':hooks,'checkpoints':[{'id':'egg','hook':'egg','op':'truthy','role':'diagnostic'}],'events':{},'routes':[{'id':k,'tier':('good' if k in ['perfect','clean'] else 'normal' if k=='bitter' else 'bad'),'gates':[],'ending':{'hook':k,'op':'truthy'}} for k in titles],'ending':{'hook':'perfect','op':'truthy'},'answer_sha256':[],'answer_hash_file':None,'request_milestones':[],'submit_conclusion':{'enabled':False,'schema':None},'rubric_path':None}
write(J/'judge.json',judge)
write(J/'checkpoint-spec.json',{'reasoning_checkpoints':[],'diagnostic':'ending titles observed only in visible ending screen, egg is nested perfect variant; no points for ordinary collection/chapters','endings':{'perfect':'holes >=7, at least 4 of 5 viewpoints >=60, alert<=50','clean':'otherwise score>=30','bitter':'otherwise score>=20','both':'otherwise score>=10','killed':'otherwise','egg':'perfect and holes>=9'},'score':'holes*2 + meet*3 + (alert<=50 ? 2 : 0) + min(evidence,10)','latching':'new Judge for each episode; title hooks check screen visibility, no hidden-text matches','source_caveats':['need uses ANY evidence, not all','pickOpt unconditionally adds hole and gotEv even on fail','top toolbar opens messages/mail/log for zero AP; probe buttons spend AP but can be bypassed normally','compareLog rewards fixed entries without asking player to identify contradiction','ending restart showIntro retains state; refresh or failure btnRetry resets state'],'formal_review':'do not certify a reasoning benchmark from scripted known-answer/source routes'})
write(T/'provenance.json',{'record_id':'base664:0429','task_id':'guimi-qiyun','snapshot':'ARG-packs/verify-416/bodies/429.html','sha256':hashlib.sha256(raw).hexdigest(),'runtime_layer':'L1','account_requirement':'none','patches':[]})
print(json.dumps({'assets':assets,'prepared':True},ensure_ascii=False))
