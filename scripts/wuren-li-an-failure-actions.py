from pathlib import Path
import asyncio,subprocess,sys,json,copy,zipfile,hashlib,os
from playwright.async_api import async_playwright
R=Path(__file__).resolve().parents[1];T='wuren-li-an';base=R/'runs/wuren-li-an-failure-migration';dest=base/'evaluation';dest.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(R/f'packs/{T}.prepared.zip') as z:z.extractall(dest)
m=json.loads((dest/'BUNDLE-MANIFEST.json').read_text(encoding='utf8'))
for f in m['files']:assert hashlib.sha256((dest/f['path']).read_bytes()).hexdigest()==f['sha256']
with zipfile.ZipFile(R/f'packs/{T}.prepared.zip') as a,zipfile.ZipFile(R/f'packs/{T}.pre-failure-migration.prepared.zip') as b:
 for n in b.namelist():
  if not n.startswith('harness/') and n not in ['BUNDLE-MANIFEST.json',f'judge/{T}/judge.json']+['judge/wuren-li-an/checkpoint-spec.json', 'judge/wuren-li-an/verify_sample.py']:assert a.read(n)==b.read(n),n
async def generate():
 s=subprocess.Popen([sys.executable,str(dest/'scripts/serve_static.py'),'--root',str(dest/f'tasks/{T}/mirror'),'--port','8832'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  async with async_playwright() as pw:
   b=await pw.chromium.launch(channel='msedge',headless=True)
   for mode in ['failure_pd','success']:
    p=await b.new_page(viewport={'width':1366,'height':900});await p.goto('http://127.0.0.1:8832/index.html');actions=[]
    async def click(sel):
     loc=p.locator(sel).first;await loc.wait_for(state='visible');await loc.scroll_into_view_if_needed();await p.wait_for_timeout(450)
     # Record the exact viewport scroll, restore then reproduce with wheel.
     y=await p.evaluate('scrollY');actions.append({'op':'scroll','x':1200,'y':500,'dy':y-(click.prev if hasattr(click,'prev') else 0)});click.prev=y
     box=await loc.bounding_box();x=box['x']+box['width']/2;yy=box['y']+box['height']/2;assert 0<=yy<=900,(sel,box,y);actions.append({'op':'click','x':x,'y':yy});await p.mouse.click(x,yy);await p.wait_for_timeout(450);click.prev=await p.evaluate('scrollY')
    async def fill(sel,value):
     await click(sel);actions.append({'op':'type','text':value});await p.keyboard.type(value);await p.wait_for_timeout(450)
    async def nav(x):await click('#nav button[onclick="go(\''+x+'\')"]')
    async def good(x):await click('button[onclick="answer(\''+x+'\',this,true)"]')
    await fill('#lawyer-name','陈慎言');await click('button[onclick="boot()"]');await click('.mail-item');await click('#mail-detail button[onclick="accept()"]')
    if mode=='failure_pd':await click('button[onclick="answer(\'pd\',this,false)"]')
    else:
     await nav('p-evidence');await click('#ev-will3');await fill('#clue-input','煤气阀门动了手脚');await click('button[onclick="tryDecode()"]');await nav('p-timeline')
     for k in 'edcba':await click('.sort-opt[data-id="'+k+'"]')
     await nav('p-people');await good('pw');await good('pf');await click('.ending-opt[onclick="ending(\'C\')"]')
    print(mode,'actions',len(actions),'bad',await p.locator('#view-bad').get_attribute('class'),'end',await p.locator('#view-ending').get_attribute('class'),flush=True)
    (base/(mode+'-actions.json')).write_text(json.dumps(actions,ensure_ascii=False,indent=2),encoding='utf8');await p.close()
   await b.close()
 finally:s.terminate();s.wait()
asyncio.run(generate())
