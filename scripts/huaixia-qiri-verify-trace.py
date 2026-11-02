"""Check recorded UI-and-hook observations without inferring unvisited routes."""
import json
from pathlib import Path

p=Path('runs/huaixia-qiri')
data=json.loads((p/'explore-negative.json').read_text(encoding='utf-8'))
states=data['states']
checks=[]
for name,fail,hook in [
 ('five-elements','圆盘咔哒','wuxing'),
 ('sexagenary','铜牌"咔"','ganzhi'),
 ('zodiac','牌位归位的一瞬间','shengxiao'),
 ('ritual','次序错了','ritual')]:
 failure=next((x for x in states if fail in x['body']),None)
 success=next((x for x in states if x.get('hooks',{}).get(hook)),None)
 ok=bool(failure and success and failure['step']<success['step'] and not failure['hooks'].get(hook))
 checks.append({'id':name,'passed':ok,'failure_step':failure and failure['step'],'success_step':success and success['step']})
ending=states[-1]
checks.append({'id':'bride_visible_ending','passed':ending.get('hooks',{}).get('end_bride') is True and not any(v for k,v in ending.get('hooks',{}).items() if k.startswith('end_') and k!='end_bride')})
yang=json.loads((p/'route-death-yang.json').read_text(encoding='utf-8'))['states']
checks.append({'id':'yang_terminal','passed':yang[-1].get('hooks',{}).get('end_yang') is True and not any(v for k,v in yang[-1].get('hooks',{}).items() if k.startswith('end_') and k!='end_yang')})
reset=json.loads((p/'reset-test.json').read_text(encoding='utf-8'))
checks.append({'id':'fresh_context_reset','passed':reset['storage_count']==0 and reset['continue_disabled'] and reset['ghost_disabled'] and reset['taoist_disabled']})
hidden=json.loads((p/'route-hidden.json').read_text(encoding='utf-8'))['states']
wrong=next((s for s in hidden if s['step']=='deduce_wrong'),None)
checks.append({'id':'deduction_wrong_combination','passed':bool(wrong and not any(v for k,v in wrong['hooks'].items() if k.startswith('ded_')))})
for ident in ['ded_axiu','ded_minghun','ded_touqi','ded_self']:
 sample=next((s for s in hidden if s['step']=='deduce_'+ident),None)
 checks.append({'id':ident,'passed':bool(sample and sample['hooks'].get(ident))})
last=hidden[-1]
checks.append({'id':'hidden_ending','passed':last.get('hooks',{}).get('end_hidden') is True})
masked=[s for s in hidden if isinstance(s['step'],int) and '返回标题 · 开始新的周目' in s['body']]
checks.append({'id':'unrevealed_ending_templates_do_not_score','passed':len(masked)>=2 and all(not any(v for k,v in s.get('hooks',{}).items() if k.startswith('end_')) for s in masked)})
mask=json.loads((p/'mask-test.json').read_text(encoding='utf-8'))
checks.append({'id':'design_document_overlay_does_not_score','passed':not any(mask['hooks'].values())})
for file, hook in [('route-good.json','end_good'),('route-vigil.json','end_vigil'),('route-double.json','end_double'),('route-sacrifice.json','end_sacrifice'),('route-hp.json','end_hp')]:
 samples=json.loads((p/file).read_text(encoding='utf-8'))['states'];s=samples[-1]
 checks.append({'id':hook,'passed':s.get('hooks',{}).get(hook) is True and not any(v for k,v in s.get('hooks',{}).items() if k.startswith('end_') and k!=hook)})
out={'checks':checks,'all_pass':all(c['passed'] for c in checks),'scope':'Only recorded UI paths and draft hooks; no claim of complete route or deduction coverage.'}
(p/'trace-verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out,ensure_ascii=True))
