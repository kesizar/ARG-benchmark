from pathlib import Path
import json,hashlib,re
R=Path(__file__).resolve().parents[1];J=R/'judge/yucai-gaozhong';P=J/'tier-review';P.mkdir(exist_ok=True)
for src,name in [(R/'packs/yucai-gaozhong.prepared.manifest.json','prior-prepared-manifest.json'),(J/'deployment.json','prior-deployment.json'),(R/'data/preparation/results/base664-0408.json','prior-result.json')]:
 if not (P/name).exists():(P/name).write_bytes(src.read_bytes())
for filename,replacements in {'prepare':[('8821','8831')],'deliver':[('8822','8832'),("/'deployments'/kind","/'tier-review-deployments'/kind"),("task/'deployment.json'","task/'tier-review-deployment.json'")],'verify':[('else 8821','else 8831')]}.items():
 p=R/f'scripts/yucai_gaozhong_{filename}.py';s=p.read_text(encoding='utf-8-sig')
 for a,b in replacements:s=s.replace(a,b)
 p.write_text(s,encoding='utf-8')
p=J/'CONTENT_AUDIT.md';s=p.read_text(encoding='utf-8');s=s.replace('Good labels for restore/witness reflect their source successful public evidence outcomes; minute13 remains normal, unreachable blank/unresolved carry no scored tier.','Original ENDINGS only calls minute13/restore regular endings and witness13 a hidden ending. No explicit author good/bad ranking was found in the preserved complete original JS/HTML/CSS. Narrative outcomes do not authorize an inferred good ranking. All three reachable judge routes therefore use neutral normal tier with good_ending=false; authored regular/hidden labels remain separate metadata. Unreachable blank/unresolved carry no scored tier.');p.write_text(s,encoding='utf-8')
p=R/'tasks/yucai-gaozhong/README.md';s=p.read_text(encoding='utf-8').replace('8821','8831');s+='\n2026-10-27结局评级复核：作者的常规/隐藏分类与评测好坏等级分开。三个可达结局均为neutral normal，good_ending=false；minute13/restore保留常规，witness13保留隐藏。无明确作者好坏等级来源，不按剧情结果擅自升为good。\n';p.write_text(s,encoding='utf-8')
src=(J/'original/game.js').read_text(encoding='utf-8');e={'source':'judge/yucai-gaozhong/original/game.js','source_sha256':hashlib.sha256((J/'original/game.js').read_bytes()).hexdigest(),'definition_lines':[{'line':i+1,'text':l} for i,l in enumerate(src.splitlines()) if 106<=i+1<=112],'explicit_good_bad_labels_found':bool(re.search(r'好结局|坏结局|good.?ending|bad.?ending',src,re.I)),'decision':'All three reachable routes neutral normal; good_ending false. Keep regular/hidden author labels as separate route metadata. No original game edits.'}
(P/'author-ranking-evidence.json').write_text(json.dumps(e,ensure_ascii=False,indent=2),encoding='utf-8')
