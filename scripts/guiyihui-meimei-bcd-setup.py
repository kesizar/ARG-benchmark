from pathlib import Path
p=Path('scripts/guiyihui-meimei-route-review.py');s=p.read_text(encoding='utf-8').replace("for route in 'ABCD':", "for route in 'BCD':").replace('verification/route-review.json','verification/route-review-bcd-current.json');Path('scripts/guiyihui-meimei-route-review-bcd.py').write_text(s,encoding='utf-8')
