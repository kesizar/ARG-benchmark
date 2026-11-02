import json, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

server = subprocess.Popen([sys.executable, '-m', 'http.server', '8811', '--bind', '127.0.0.1', '--directory', 'tasks/huaixia-qiri'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
negative = '--negative' in sys.argv or '--negative-all' in sys.argv
negative_all = '--negative-all' in sys.argv
flee = '--flee' in sys.argv
hidden = '--hidden' in sys.argv
variant = next((x.split('=',1)[1] for x in sys.argv if x.startswith('--variant=')),None)
good = '--good' in sys.argv or hidden or bool(variant)
deduce = '--deduce' in sys.argv or hidden
die = '--die-sanity' in sys.argv
die_yang = '--die-yang' in sys.argv
trace_path = Path('runs/huaixia-qiri/route-'+variant+'.json' if variant else ('runs/huaixia-qiri/route-hidden.json' if hidden else ('runs/huaixia-qiri/route-deduction.json' if deduce else ('runs/huaixia-qiri/route-good.json' if good else ('runs/huaixia-qiri/route-death-sanity.json' if die else ('runs/huaixia-qiri/route-death-yang.json' if die_yang else ('runs/huaixia-qiri/route-flee-negative.json' if flee else ('runs/huaixia-qiri/explore-negative.json' if negative else 'runs/huaixia-qiri/explore-first.json'))))))))
wrong_done = set()
ded_done = set()
ded_wrong_done = False
playthrough = 1
got_double = False
judge_hooks = json.loads(Path('judge/huaixia-qiri/judge.json').read_text(encoding='utf-8'))['hooks'] if '--judge-test' in sys.argv else {}
def probe(page):
 return {k:page.evaluate('() => Boolean('+v['expr']+')') for k,v in judge_hooks.items()}
try:
 time.sleep(1)
 with sync_playwright() as p:
  browser = p.chromium.launch(channel='msedge', headless=True, args=['--no-proxy-server'])
  page = browser.new_page(viewport={'width':1280,'height':1000})
  blocked, errors, states = [], [], []
  page.on('pageerror', lambda e: errors.append(str(e)))
  page.route('**/*', lambda r: r.continue_() if r.request.url.startswith('http://127.0.0.1:8811/') else (blocked.append(r.request.url), r.abort()))
  page.goto('http://127.0.0.1:8811/original.html', wait_until='domcontentloaded', timeout=15000)
  page.get_by_role('button', name='新的七日').click()
  if '--easy' in sys.argv: page.get_by_role('checkbox').check()
  page.get_by_role('button', name='入村').click()
  for step in range(400):
   page.wait_for_timeout(150)
   body = page.locator('body').inner_text()
   buttons = page.get_by_role('button').all_text_contents()
   states.append({'step':step,'body':body,'buttons':buttons,'hooks':probe(page)})
   trace_path.write_text(json.dumps({'states':states,'blocked':blocked,'errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
   if any(x in body for x in ['结局 ·', '返回标题', '重新开始']):
    skip_end = page.get_by_text('点击跳过', exact=True)
    if skip_end.count() and skip_end.first.is_visible(): skip_end.first.click(timeout=3000)
    page.wait_for_timeout(1000)
    states.append({'step':'ending_after_skip','body':page.locator('body').inner_text(),'buttons':page.get_by_role('button').all_text_contents(),'hooks':probe(page)})
    trace_path.write_text(json.dumps({'states':states,'blocked':blocked,'errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
    page.screenshot(path=str(trace_path.with_suffix('.png')))
    if hidden and playthrough==1:
     page.locator('button').filter(has_text='返回标题 · 开始新的周目').click(timeout=3000)
     page.get_by_role('button',name='新的七日').click(timeout=3000)
     page.locator('button').filter(has_text='鬼魂视角').click(timeout=3000)
     page.get_by_role('checkbox').check()
     page.get_by_role('button',name='入村').click(timeout=3000)
     playthrough=2;ded_done.clear();continue
    if '--reset-test' in sys.argv:
     fresh = browser.new_page(viewport={'width':1280,'height':1000})
     fresh.route('**/*', lambda r: r.continue_() if r.request.url.startswith('http://127.0.0.1:8811/') else r.abort())
     fresh.goto('http://127.0.0.1:8811/original.html', wait_until='domcontentloaded', timeout=15000)
     before = {'continue_disabled':fresh.get_by_role('button',name='继续',exact=True).is_disabled(), 'storage_count':fresh.evaluate('localStorage.length'),'hooks':probe(fresh)}
     fresh.get_by_role('button', name='新的七日').click()
     before['ghost_disabled']=fresh.get_by_role('button', name='鬼魂视角').is_disabled()
     before['taoist_disabled']=fresh.get_by_role('button', name='道士视角').is_disabled()
     Path('runs/huaixia-qiri/reset-test.json').write_text(json.dumps(before,ensure_ascii=False,indent=2),encoding='utf-8')
     fresh.close()
    break
   skip = page.get_by_text('点击跳过', exact=True)
   if skip.count() and skip.first.is_visible():
    try: skip.first.click(timeout=1500)
    except Exception: pass
    page.wait_for_timeout(250)
   if deduce and step >= 35 and step % 12 == 0:
    page.get_by_role('button',name='线索',exact=True).click(timeout=3000)
    modal=page.locator('.fixed.inset-0.z-40')
    if not ded_wrong_done:
     clue_buttons=modal.locator('button.text-left')
     if clue_buttons.count()>=3:
      labels=[clue_buttons.nth(i).inner_text().splitlines()[0] for i in range(3)]
      good_sets=[{'纸新娘的脸','老温的话','族谱缺页'},{'婚书内容','棺木刻字','井边红线'},{'守灵七条','阿婆遗言','账本记录'},{'镜中无人','广播新闻','犬吠'}]
      if set(labels) not in good_sets:
       for i in range(3): clue_buttons.nth(i).click(timeout=3000)
       modal.locator('button').filter(has_text='串联线索').click(timeout=3000)
       page.wait_for_timeout(300)
       states.append({'step':'deduce_wrong','clues':labels,'body':page.locator('body').inner_text(),'hooks':probe(page)})
       trace_path.write_text(json.dumps({'states':states,'blocked':blocked,'errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
       ded_wrong_done=True
    for ident, names in [('ded_axiu',['纸新娘的脸','老温的话','族谱缺页']),('ded_minghun',['婚书内容','棺木刻字','井边红线']),('ded_touqi',['守灵七条','阿婆遗言','账本记录']),('ded_self',['镜中无人','广播新闻','犬吠'])]:
     if ident=='ded_self' and playthrough<2: continue
     if ident in ded_done: continue
     choices=[modal.locator('button').filter(has_text=x) for x in names]
     if all(c.count() for c in choices):
      for c in choices: c.first.click(timeout=3000)
      modal.locator('button').filter(has_text='串联线索').click(timeout=3000)
      page.wait_for_timeout(300)
      record={'step':'deduce_'+ident,'body':page.locator('body').inner_text(),'hooks':probe(page)}
      states.append(record);trace_path.write_text(json.dumps({'states':states,'blocked':blocked,'errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
      if '推理成立：' in record['body']: ded_done.add(ident)
      else: break
      modal.locator('button').filter(has_text='收起').click(timeout=3000)
    modal.locator('button').filter(has_text='✕').click(timeout=3000)
   if flee and '今晚就走，出村' in buttons:
    page.get_by_role('button', name='今晚就走，出村').click(timeout=3000)
    continue
   if good and '按退亲仪式的正确次序' not in body:
    special=[]
    if variant=='sacrifice': special=['先把小满背上去','咬牙往上爬','让小满去']
    if variant=='vigil': special=['天黑了，去祠堂']
    if variant=='double': special=['帮老温打下手','连夜送回纸扎铺','请你替我扎一个','接过纸替身','把纸替身推进轿里']
    if variant=='double' and not got_double and '第六日 · 准备' in body: special.insert(0,'纸扎铺')
    if variant=='hp': special=['推开碗，说不饿','撕下纸人脸上的一角','不惊动她，悄悄跟在后面','先把骨头收起来','放开骨头，扑向小满','咬牙往上爬']
    targets=special+(['【鬼魂视角】"我知道我是谁了','【鬼魂视角】看最下一排'] if hidden and playthrough==2 else [])+(['拿起铜镜，看一眼'] if hidden else [])+(['跟母亲说话'] if deduce else [])+['摊牌：','先把骨头收起来','继续收骨头','我不娶，也不让任何人嫁','焚书','用手扯断红线']
    target = next((t for t in targets if any(t in b for b in buttons)),None)
    if target:
     page.locator('button').filter(has_text=target).first.click(timeout=3000)
     if target=='接过纸替身': got_double=True
     continue
   orders = [('按五行相生的顺序', ['木','火','土','金','水']), ('按十二生肖的正确顺序', ['鼠','牛','虎','兔','龙','蛇','马','羊','猴','鸡','狗','猪']), ('按退亲仪式的正确次序', ['净手','请灵','焚书','断线','送归'])]
   match = next((items for prompt,items in orders if prompt in body), None)
   if match:
    if '1'+match[0] not in body:
     wrong = (die and match[0]=='木') or (negative and match[0] not in wrong_done and (negative_all or match[0]=='木'))
     order = list(reversed(match)) if wrong else match
     for item in order:
      page.get_by_role('button', name=item, exact=True).click()
     page.wait_for_timeout(500)
     if wrong: wrong_done.add(match[0])
    confirm = page.locator('button').filter(has_text='确认排列')
    Path('runs/huaixia-qiri/puzzle-dom.json').write_text(json.dumps({'count':confirm.count(),'html':confirm.evaluate_all('(els) => els.map(e => e.outerHTML)'),'body':page.locator('body').inner_text()},ensure_ascii=False,indent=2),encoding='utf-8')
    if confirm.count() and confirm.is_enabled():
     confirm.click(timeout=3000)
     page.wait_for_timeout(400)
    else:
     page.screenshot(path='runs/huaixia-qiri/puzzle-blocked.png')
     break
    continue
   if '丁亥年' in body and page.locator('input[placeholder="____"]').count():
    wrong = die_yang or (negative_all and 'ganzhi' not in wrong_done)
    page.locator('input[placeholder="____"]').fill('1948' if wrong else '1947')
    if wrong: wrong_done.add('ganzhi')
    page.wait_for_timeout(300)
    page.locator('button').filter(has_text='拨动').click(timeout=3000)
    continue
   choices = page.locator('button.btn-choice:visible:not(:disabled):not(.opacity-60)')
   if not choices.count(): choices = page.locator('button.btn-choice:visible:not(:disabled)')
   if not choices.count(): break
   choices.first.click(timeout=5000)
  trace_path.write_text(json.dumps({'states':states,'blocked':blocked,'errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
  browser.close()
finally:
 server.terminate()
