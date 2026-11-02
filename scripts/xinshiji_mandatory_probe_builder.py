from pathlib import Path
r=Path(__file__).resolve().parents[1];s=(r/'scripts/xinshiji_ui.py').read_text('utf8')
s=s.replace('from playwright.sync_api import sync_playwright','from playwright.sync_api import sync_playwright\nfrom xinshiji_judge_probe import Probe\nprobe=Probe()')
s=s.replace("out=Path('judge/xinshiji/recovery')","out=Path('judge/xinshiji/recovery/mandatory-judge')")
s=s.replace('def mark(name,**kw):events.append', 'def mark(name,**kw):\n kw[\'judge\']=probe.sample(p)\n if name==\'independent_judge_completed_one\':assert probe.j.score()[\'checkpoints_reached\']==5\n if name.endswith(\'negative_pass\'):\n  k={\'Archive\':\'archive\',\'Chat\':\'chat\',\'Plan\':\'plan\',\'lock\':\'company-lock\'}.get(name.split(\'_\')[0]);assert k is None or not probe.j.values[k]\n events.append')
s=s.replace("assert not score(p);mark('independent_judge_reset_zero')","assert not score(p);probe=Probe();mark('independent_judge_reset_zero');assert not any(probe.j.values.values())")
(r/'scripts/xinshiji_mandatory_judge_ui.py').write_text(s,encoding='utf8')
print('Build mandatory judge delta verifier')
