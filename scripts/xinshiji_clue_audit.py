"""Evaluator-only visual clue inspection, separate from normal-UI route evidence."""
import json,threading,http.server,functools,itertools,datetime
from pathlib import Path
from playwright.sync_api import sync_playwright
r=Path(__file__).resolve().parents[1];out=r/'judge/xinshiji/recovery/clues';out.mkdir(parents=True,exist_ok=True)
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
s=http.server.ThreadingHTTPServer(('127.0.0.1',8821),functools.partial(Quiet,directory=str(r/'tasks/xinshiji/mirror')));threading.Thread(target=s.serve_forever,daemon=True).start()
report={'scope':'Evaluator-only direct page visual inspection; not normal-UI navigation or model action evidence','pages':[]}
with sync_playwright() as pw:
 b=pw.chromium.launch(channel='msedge',headless=True);p=b.new_page(viewport={'width':1366,'height':900})
 try:
  for name in ['aqiang-moments','sun-moments','gzh-article5','gzh-article6','gzh-article7','family-chat','wang-chat','leyuan','member-page','sunflower']:
   p.goto('http://127.0.0.1:8821/'+name+'.html',timeout=15000);p.wait_for_timeout(500)
   text=p.locator('body').inner_text();images=p.locator('img').evaluate_all('(xs)=>xs.map(x=>({src:x.getAttribute("src"),loaded:x.complete&&x.naturalWidth>0,display:getComputedStyle(x).display}))')
   p.screenshot(path=str(out/(name+'.png')),full_page=True)
   row={'page':name,'text':text,'images':images}
   if name=='gzh-article6':row['body_symbol_counts']={c:text.count(c) for c in ['♦','⭐','❤']};row['cover_image_each_symbol']=1
   if name=='sunflower':p.keyboard.press('Control+a');p.screenshot(path=str(out/'sunflower-selected.png'),full_page=True)
   report['pages'].append(row)
  # Game-side archive numeric substitution constraints, independently enumerate plausible16-19 meeting hour and2023 year.
  sols=[]
  for A,B in [(1,x) for x in range(6,10)]:
   C,D,E=2,0,3
   for F,G,H,I in itertools.permutations(set(range(10))-{A,B,C,D,E},4):
    if H+G>10 and 1000*F+100*G+10*B+H+1000*A+100*D+10*I+G==10000*A+1000*D+100*B+10*G+C:sols.append([A,B,C,D,E,F,G,H,I])
  report['archive_numeric_solutions_given_16_to_19_and_year2023']=sols
 finally:b.close();s.shutdown()
(out/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'pages':len(report['pages']),'archive_solutions':sols}))
