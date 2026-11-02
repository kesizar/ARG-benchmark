from pathlib import Path
import asyncio,subprocess,sys,json,zipfile,hashlib,time
from playwright.async_api import async_playwright
R=Path(__file__).resolve().parents[1];T='huicheng-317';base=R/'runs/huicheng-317-failure-migration';dest=base/'evaluation';dest.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(R/f'packs/{T}.prepared.zip') as z:z.extractall(dest)
m=json.loads((dest/'BUNDLE-MANIFEST.json').read_text(encoding='utf8'))
for f in m['files']:assert hashlib.sha256((dest/f['path']).read_bytes()).hexdigest()==f['sha256']
with zipfile.ZipFile(R/f'packs/{T}.prepared.zip') as a,zipfile.ZipFile(R/f'packs/{T}.pre-failure-migration.prepared.zip') as b:
 for n in b.namelist():
  if not n.startswith('harness/') and n not in ['BUNDLE-MANIFEST.json',f'judge/{T}/judge.json',f'judge/{T}/checkpoint-spec.json',f'judge/{T}/verify_sample.py',f'tasks/{T}/README.md']:assert a.read(n)==b.read(n),n
async def generate():
 s=subprocess.Popen([sys.executable,str(dest/'scripts/serve_static.py'),'--root',str(dest/f'tasks/{T}/mirror'),'--port','8833'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  async with async_playwright() as pw:
   b=await pw.chromium.launch(channel='msedge',headless=True)
   for mode in ['failure','success']:
    p=await b.new_page(viewport={'width':1366,'height':900},reduced_motion='reduce');await p.goto('http://127.0.0.1:8833/index.html');actions=[]
    async def click(loc):
     start=time.monotonic();await loc.wait_for(state='visible',timeout=90000);await loc.scroll_into_view_if_needed();await loc.click(trial=True,timeout=90000);elapsed=int((time.monotonic()-start)*1000)+600
     # Conservative idle time preserves original timer progression in the real loop.
     while elapsed>0:
      ms=min(elapsed,9000);actions.append({'op':'wait','ms':ms});elapsed-=ms
     box=await loc.bounding_box();x=box['x']+box['width']/2;y=box['y']+box['height']/2;assert 0<=y<900,(box);actions.append({'op':'click','x':x,'y':y});await p.mouse.click(x,y)
    async def c(t):await click(p.get_by_role('button',name=t,exact=True))
    await click(p.locator('#boot'));await c('02走向大厅');await c('③维修间 · 档案室');await c('①输入四位密码');await click(p.locator('#miniInput'));actions.append({'op':'type','text':'0000' if mode=='failure' else '2600'});await p.keyboard.type('0000' if mode=='failure' else '2600')
    for i in range(50 if mode=='failure' else 1):await click(p.locator('#miniOk'))
    if mode=='success':
     for t in ['③只看，不碰','②大厅尽头 · 结着雾的窗','擦开玻璃，看出去','②转身离开，不再看','→我感觉知道得够多了','①走向车门','它朝你伸出手','C烧掉中枢站总档，掐断循环']:await c(t)
    await p.wait_for_timeout(2500);print(mode,await p.locator('#endTag').inner_text(),len(actions),flush=True);(base/(mode+'-actions.json')).write_text(json.dumps(actions,ensure_ascii=False,indent=2),encoding='utf8');await p.close()
   await b.close()
 finally:s.terminate();s.wait()
asyncio.run(generate())
