"""Choose a browser timezone window without touching game state or OS clock."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,subprocess,sys,uuid
R=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser();p.add_argument('--window',choices=['night','day'],default='night');p.add_argument('--policy',choices=['script','llm'],default='script');a=p.parse_args()
c=json.loads((R/'configs/k7-dangan.json').read_text(encoding='utf-8'));target=2 if a.window=='night' else 12;offset=(target-datetime.now(timezone.utc).hour+12)%24-12;c['timezone']='Etc/GMT'+('+'+str(-offset) if offset<0 else '-'+str(offset) if offset>0 else '')
out=R/'runs'/('k7-window-'+uuid.uuid4().hex[:8]);out.mkdir(parents=True);cfg=out/'config.json';cfg.write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf-8');print('Browser timezone',c['timezone'],flush=True);raise SystemExit(subprocess.call([sys.executable,str(R/'scripts/run_one.py'),'--config',str(cfg),'--policy',a.policy],cwd=R))
