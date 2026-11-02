import json,sys
from pathlib import Path
r=Path(__file__).resolve().parents[1];base=r/'runs/xinshiji-independent/evaluation';d=json.loads((r/'configs/xinshiji.json').read_text('utf8'))
d['entry_url']=d['entry_url'].replace('8821','8823');d['allow_hosts']=['127.0.0.1:8823'];d['local_serve']['command']=[sys.executable,'scripts/serve_static.py','--root','tasks/xinshiji/mirror','--port','8823'];d['local_serve']['ready_url']=d['entry_url'];d['local_serve']['port']=8823
d['limits']['max_steps']=2;d['limits']['max_seconds']=60;d['notes_for_report']=['Independent evaluator CLI smoke; no model API; scripted give_up is not solution coverage.']
(base/'configs/xinshiji-cli-smoke.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
print(base)
