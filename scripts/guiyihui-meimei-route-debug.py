from pathlib import Path
p=Path('scripts/guiyihui-meimei-route-review.py');s=p.read_text(encoding='utf-8').replace("if route=='A':\n     assert not score", "if route=='A':\n     log['A_debug']={'score':score,'values':j.values,'prev_values':j.prev_values}; assert not score")
p.write_text(s,encoding='utf-8')
