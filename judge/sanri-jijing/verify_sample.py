"""Evaluator-only deterministic normal-UI acceptance. Never serves evaluator files."""
from pathlib import Path
import argparse,itertools,json,sys,subprocess,time,urllib.request
p=argparse.ArgumentParser();p.add_argument('--root');p.add_argument('--game-root');p.add_argument('--port',type=int,default=8811);p.add_argument('--out',required=True);p.add_argument('--exhaustive',action='store_true');p.add_argument('--snow',action='store_true');a=p.parse_args()
R=Path(a.root).resolve() if a.root else Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from harness.judge import Judge
from playwright.sync_api import sync_playwright
O=Path(a.out).resolve();O.mkdir(parents=True,exist_ok=True);G=Path(a.game_root).resolve() if a.game_root else R/'tasks/sanri-jijing/mirror';url=f'http://127.0.0.1:{a.port}/index.html'
print('launch server',str(R),str(G),flush=True)
server=subprocess.Popen([sys.executable,str(R/'scripts/serve_static.py'),'--root',str(G),'--port',str(a.port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
trace=[];errors=[];requests=[];blocked=[]
try:
 for _ in range(100):
  try: urllib.request.urlopen(url,timeout=.5).close();break
  except Exception:time.sleep(.1)
 print('server ready or readiness exhausted',flush=True)
 with sync_playwright() as pw:
  print('launch browser',flush=True);b=pw.chromium.launch(channel='msedge',headless=True);c=b.new_context(viewport={'width':1366,'height':900},service_workers='block');page=c.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda req:requests.append(req.url))
  def route(r):
   if r.request.url.startswith(f'http://127.0.0.1:{a.port}/'):r.continue_()
   else:blocked.append(r.request.url);r.abort()
  c.route('**/*',route);page.goto(url);judge=Judge.load(R/'judge/sanri-jijing/judge.json','sanri-jijing',R)
  def snap(label,count,ending=False):
   judge.prev_values=dict(judge.values);judge.values={k:page.evaluate(v['expr']) for k,v in judge.cfg['hooks'].items()};judge.update(len(trace));s=judge.score();assert len(judge.checkpoints)==count,(label,s);assert s['ending_reached']==ending,(label,s)
   print(label,flush=True);trace.append({'stage':label,'score':s,'unlocked':page.evaluate('unlocked'),'errors':list(errors)})
  def click(sel):page.locator(sel).click();page.wait_for_timeout(70)
  def text(sel,label):page.locator(sel).get_by_text(label,exact=True).click();page.wait_for_timeout(70)
  snap('initial',0);click('.start-btn');page.wait_for_timeout(1200)
  for i in range(3):click('#stoneCv');snap(f'stone_{i+1}_no_score',0)
  page.locator('#l0').wait_for(state='visible');page.wait_for_timeout(800)
  click('#l0 .sb');snap('empty_name',0);page.locator('#a0').fill('张起灵');click('#l0 .sb');snap('wrong_name',0);page.locator('#a0').fill('  白玛  ');click('#l0 .sb');snap('name',0)
  page.locator('#l1').wait_for(state='visible');page.wait_for_timeout(1200)
  for label in ['一头牦牛','一面经幡','一座雪山']:
   text('#l1',label);snap('wrong_choice_'+label,0);page.wait_for_timeout(1000)
  text('#l1','一双藏民的眼睛');snap('choice',0);page.locator('#l2').wait_for(state='visible');page.wait_for_timeout(1200)
  pairs=list(itertools.permutations('声沉默命名苦',2)) if a.exhaustive else [('默','沉')]
  for pair in pairs:
   if pair==('沉','默'):continue
   for ch in pair:text('#g2',ch)
   snap('wrong_glyph_'+''.join(pair),0)
  text('#g2','沉');text('#g2','沉');snap('duplicate_glyph_ignored',0);text('#g2','默');snap('glyphs',0)
  page.locator('#l3').wait_for(state='visible');page.wait_for_timeout(1200)
  correct=['白玛服下藏海花','进入冰陵沉睡','张起灵来到拉吉寺','上师让他凿石头'];perms=[x for n in range(5) for x in itertools.permutations(correct,n)] if a.exhaustive else [(),tuple(reversed(correct))]
  text('#seqBtns',correct[0]);text('#seqBtns',correct[0]);assert page.locator('#seqDisp').inner_text()=='点击下方开始排列';snap('sequence_toggle_off',0)
  for seq in perms:
   if list(seq)==correct:continue
   for label in seq:text('#seqBtns',label)
   click('#l3 .sb');snap('wrong_sequence_'+str(len(trace)),0)
  for label in correct:text('#seqBtns',label)
  click('#l3 .sb');snap('timeline',1);page.locator('#c4').wait_for(state='visible');page.wait_for_timeout(1200)
  if a.snow:
   for i in range(3):click('#stoneCv2')
   page.wait_for_timeout(1800);assert page.locator('#snowOv').evaluate("e=>e.classList.contains('on')");snap('snow_scene_no_score',1);page.screenshot(path=str(O/'snow.png'));page.wait_for_timeout(9000)
  page.locator('#l4').wait_for(state='visible');page.wait_for_timeout(1000)
  for answer in ['', '石','白玛']:
   page.locator('#a4').fill(answer);click('#l4 .sb');snap('wrong_final_'+answer,1)
  page.screenshot(path=str(O/'final_prompt.png'));page.locator('#a4').fill('石头');click('#l4 .sb');snap('final_not_yet_ending',1);page.wait_for_timeout(1600);snap('ending',1,True);assert not page.locator('#end').is_visible();page.locator('#c5').scroll_into_view_if_needed();page.screenshot(path=str(O/'ending.png'))
  page.reload();judge=Judge.load(R/'judge/sanri-jijing/judge.json','sanri-jijing',R);snap('reload_reset',0);assert page.locator('#landing').is_visible();assert page.evaluate('stoneHits===0 && stoneHits2===0 && Object.keys(localStorage).length===0');page.screenshot(path=str(O/'reset.png'))
  # Fresh browser context must independently reset without state transfer.
  fresh=b.new_context();q=fresh.new_page();q.goto(url);assert q.evaluate('unlocked.every(x=>!x) && stoneHits===0');fresh.close();c.close();b.close()
finally:
 server.terminate();server.wait(timeout=10)
 (O/'ui-trace.json').write_text(json.dumps({'root':str(R),'game_root':str(G),'url':url,'exhaustive':a.exhaustive,'snow':a.snow,'trace':trace,'page_errors':errors,'requests':requests,'blocked_external_requests':blocked},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'checks':len(trace),'page_errors':errors,'blocked_external_requests':blocked,'last':trace[-1]['stage'] if trace else None},ensure_ascii=False))
