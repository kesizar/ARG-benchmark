from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];T='qingmiao-zhongxue'
words=['350','2510','乳糖不耐','5201','YC001','20101123','英才2301班','营养不良性贫血','青苗论坛','农场办公室档案柜','20250308','QM230617001','幼苗共育','QM251123489','吃植物人','牛奶','砧木','接穗','成材']
j={'hooks':{},'checkpoints':[],'routes':[],'events':{},'answer_sha256':[],'request_milestones':[],'submit_conclusion':{'enabled':False,'schema':None}}
spec=[]
positions=[1,2,3,4,5,6,7,8,13,15,16,19,20,21,22,23,25,26,27]
for n,w in enumerate(words,1):
 ident=f'k{n:02d}'
 j['hooks'][ident]={'type':'js_truthy','expr':f"typeof conversationHistory!=='undefined'&&(conversationHistory.filter(m=>m.type==='sent')[{positions[n-1]}]?.content||'').includes({json.dumps(w,ensure_ascii=False)})"}
 j['checkpoints'].append({'id':ident,'hook':ident,'op':'truthy','role':'optional'})
 spec.append({'id':ident,'answer':w,'accepted_sent_index':positions[n-1],'condition':'Accepted message at its fixed progression index in conversationHistory; never raw input or earlier messages containing a later answer.','role':'optional','why':'Original ending trigger bypasses all earlier gates; this is not mandatory for either original ending.'})
for ident,expr in [('report',"document.querySelector('#resultMessage.success')&&document.querySelector('#submitReportBtn').disabled"),('report-decrypt',"document.querySelector('#encryptedContent')&&document.querySelector('#encryptedContent').style.display==='block'"),('labor-2',"document.querySelector('#imageContainer2')&&document.querySelector('#imageContainer2').style.display==='block'"),('labor-3',"document.querySelector('#imageContainer3')&&document.querySelector('#imageContainer3').style.display==='block'")]:
 j['hooks'][ident]={'type':'js_truthy','expr':expr};j['checkpoints'].append({'id':ident,'hook':ident,'op':'truthy','role':'optional'})
 spec.append({'id':ident,'condition':expr,'role':'optional','latch':'Judge.update retains observed successful event through tab switches; reset constructs a new Judge.'})
for ident,element,tier in [('gentle','typewriterEndTypedText','normal'),('harsh','animationEndTypedText','normal')]:
 j['hooks'][ident]={'type':'js_truthy','expr':f"document.getElementById('{element}')&&document.getElementById('{element}').textContent==='END'"}
 j['routes'].append({'id':ident,'tier':tier,'gates':[],'ending':{'hook':ident,'op':'truthy'}})
(R/'judge'/T/'judge.json').write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
(R/'judge'/T/'checkpoint-spec.json').write_text(json.dumps({'checkpoints':spec,'routes':j['routes'],'ending_tiers':'Both routes conservatively normal. Original labels only END and establishes no higher-ranked ending; good_ending must be false. Formal suitability pending bypass review.','coverage':'19 accepted chat reasoning/lookup prompts; aggregate six-field report; three optional school decrypt gates; six reconvergent dialogue choices and recording/GIF/police transitions audited separately.'},ensure_ascii=False,indent=2),encoding='utf-8')
print(len(j['checkpoints']))
