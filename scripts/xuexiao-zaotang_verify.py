from pathlib import Path
import argparse,asyncio,json,subprocess,sys,time,urllib.request
from playwright.async_api import async_playwright
async def main():
 a=argparse.ArgumentParser();a.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));a.add_argument('--port',type=int,default=8831);a.add_argument('--out',required=True);a.add_argument('--evaluation-root');o=a.parse_args();r=Path(o.root).resolve();er=Path(o.evaluation_root).resolve() if o.evaluation_root else r;out=Path(o.out).resolve();out.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(er));from harness.judge import Judge
 srv=subprocess.Popen([sys.executable,str(er/'scripts/serve_static.py'),'--root',str(r/'tasks/xuexiao-zaotang/mirror'),'--port',str(o.port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);base=f'http://127.0.0.1:{o.port}'
 try:
  for _ in range(60):
   try:urllib.request.urlopen(base+'/index.html',timeout=1);break
   except Exception:time.sleep(.1)
  async with async_playwright() as p:
   b=await p.chromium.launch(channel='msedge',headless=True);ctx=await b.new_context(viewport={'width':1366,'height':900});pg=await ctx.new_page();errors=[];external=[];pg.on('pageerror',lambda e:errors.append(str(e)));pg.on('request',lambda q:external.append(q.url) if not q.url.startswith(base) else None)
   await pg.goto(base+'/index.html');assert await pg.title()=='【求助】学校澡堂深夜有滴水声，水管师傅查了四次都说没问题 - 家居维修 - 知然问答';await pg.screenshot(path=str(out/'entry.png'),full_page=True)
   class H:
    async def dom_texts(self):return [await pg.locator('body').inner_text()]
   j=Judge.load(er/'judge/xuexiao-zaotang/judge.json','xuexiao-zaotang',er);await j.read(H());j.update(0);initial=j.score();assert not j.ending_reached and not j.checkpoints
   await pg.locator('#lzbtn').click();assert await pg.locator('#lzbtn').inner_text()=='显示全部回复';assert await pg.locator('body').evaluate('(x)=>x.classList.contains("onlylz")');await j.read(H());j.update(1);assert not j.ending_reached
   await pg.locator('#lzbtn').click();assert await pg.locator('#lzbtn').inner_text()=='只看楼主';await pg.locator('a.author[href="profile.html"]').first.click();assert '/profile.html' in pg.url;assert '404' in await pg.locator('body').inner_text();await pg.screenshot(path=str(out/'profile-404.png'));await j.read(H());j.update(2);assert not j.ending_reached
   await pg.go_back();await ctx.close();ctx=await b.new_context();pg=await ctx.new_page();await pg.goto(base+'/index.html');storage=await pg.evaluate('({...localStorage})');assert storage=={'argStep':'1'};assert await pg.locator('#lzbtn').inner_text()=='只看楼主';assert await pg.locator('a[href="start.html"]').count()==0
   await ctx.close();await b.close();result={'root':str(r),'port':o.port,'normal_ui':['entry rendered','only-lz on/off','profile author link normal navigation reaches missing 404','browser back','fresh context reset'],'initial_score':initial,'ending_reached':False,'reasoning_points_awarded':0,'required_profile_missing':True,'fresh_storage':storage,'external_requests':external,'runtime_script_errors':errors,'full_game_flow':'BLOCKED missing profile.html/start.html','positive_reasoning_and_endings':'NOT TESTABLE; no fabricated success'};assert not errors and not external;(out/'acceptance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'out':str(out),'entry_acceptance':'pass','full_game':'blocked'}))
 finally:srv.terminate();srv.wait(timeout=10)
if __name__=='__main__':asyncio.run(main())
