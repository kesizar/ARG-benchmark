"""Normal UI regression; page evaluation is restricted to the independent judge."""
import asyncio,json,sys,argparse,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from harness.judge import Judge
from playwright.async_api import async_playwright
class Adapter:
 def __init__(self,page):self.page=page
 async def page_expr(self,expr):return await self.page.evaluate(expr)
async def run(port,out):
 out.mkdir(parents=True,exist_ok=True);log=[]
 proc=subprocess.Popen([sys.executable,str(ROOT/'scripts/serve_static.py'),'--root',str(ROOT/'tasks/meiyou-cuo/mirror'),'--port',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  await asyncio.sleep(.8)
  async with async_playwright() as p:
   b=await p.chromium.launch(channel='msedge',headless=True);ctx=await b.new_context(viewport={'width':1366,'height':900});page=await ctx.new_page();requests=[];errors=[]
   page.on('request',lambda q:requests.append(q.url));page.on('pageerror',lambda e:errors.append(str(e)))
   judge=Judge.load(ROOT/'judge/meiyou-cuo/judge.json','meiyou-cuo',ROOT)
   async def mark(name,end=False):
    await judge.read(Adapter(page));judge.update(len(log));assert judge.ending_reached==end,(name,judge.score());log.append({'name':name,'score':judge.score()})
   async def click(sel):await page.locator(sel).filter(visible=True).first.click()
   async def closemodal():
    if await page.locator('#modal.show').count():await click('#modal .modal-foot button')
   await page.goto(f'http://127.0.0.1:{port}/index.html');await mark('initial-hidden-ending-negative')
   for i in range(9):
    await click(f'[onclick="openFakePost({i})"]');await page.locator('#fakeReplyInput').fill('test');await click('[onclick="fakeSubmitReply()"]');await mark(f'irrelevant-post-{i}');await closemodal()
   await click('[onclick="showPost()"] >> nth=0');await click('[onclick="submitReply()"]');await mark('empty-forum-reply-negative');await page.locator('#replyInput').fill('不是她做的');await click('[onclick="submitReply()"]');await closemodal();await mark('forum-reply-no-score')
   await click('[onclick="openTimeMachine()"]');await page.locator('#pwdInput').fill('definitely-wrong');await click('.login-btn');await mark('arbitrary-password-accepted-no-score')
   for kind in ['self','teacher','leader','witness','unknown','system']:
    await click(f'[onclick="openChat(\'{kind}\')"] >> nth=0');await page.locator('#chatInput').fill('发生了什么');await click('[onclick="sendMsg()"]');await page.wait_for_timeout(900);assert '对方无响应' in await page.locator('#chatBody').inner_text();await mark('chat-'+kind);await click('[onclick="closeChat()"]')
   await click('[onclick="ensureLogin(); showFiles()"]')
   for i in range(3):
    await page.locator('#filesView .file-row').nth(i).click();assert await page.locator('#filesView .file-preview').nth(i).is_visible();await mark('file-'+str(i))
   await page.screenshot(path=str(out/'files.png'),full_page=True);await click('#filesView [onclick="showMain()"]')
   await click('[onclick="ensureLogin(); showShuoshuo()"]');assert await page.locator('.shuoshuo').count()==7;await mark('seven-shuoshuo')
   await click('[onclick="ensureLogin(); showSpace()"]');assert await page.locator('.feed-item').count()==8
   await page.locator('#feedInput-0').fill('不是你');await click('[onclick="feedReply(0)"]');await page.locator('#spaceSearch').fill('打卡记录');await click('[onclick="spaceSearchClick()"]');await mark('space-comment-search-no-score');await page.screenshot(path=str(out/'space.png'),full_page=True)
   await click('[onclick="ensureLogin(); showEnding()"]');await page.wait_for_timeout(1700);await mark('sole-ending-visible',True);await page.screenshot(path=str(out/'ending.png'),full_page=True)
   await page.reload();judge=Judge.load(ROOT/'judge/meiyou-cuo/judge.json','meiyou-cuo',ROOT);await mark('reload-new-judge-reset')
   await click('[onclick="showPost()"] >> nth=0');await click('[onclick="openTimeMachine()"]');await click('.login-btn');await mark('empty-password-accepted');await click('[onclick="ensureLogin(); showEnding()"]');await page.wait_for_timeout(1700);await mark('early-exit-without-evidence',True)
   await ctx.close();ctx=await b.new_context();page=await ctx.new_page();await page.goto(f'http://127.0.0.1:{port}/index.html');judge=Judge.load(ROOT/'judge/meiyou-cuo/judge.json','meiyou-cuo',ROOT);await mark('fresh-context-reset');await b.close()
   assert not errors,errors;assert all(u.startswith(f'http://127.0.0.1:{port}/') for u in requests),requests
   (out/'acceptance.json').write_text(json.dumps({'passed':True,'normal_ui_only':True,'port':port,'checks':log,'requests':requests,'page_errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
 finally:proc.terminate();proc.wait(timeout=10)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--port',type=int,default=8811);a.add_argument('--out',default='runs/meiyou-cuo/acceptance');v=a.parse_args();asyncio.run(run(v.port,Path(v.out)))
