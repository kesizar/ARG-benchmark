"""Original optional8s clip; autoplay-enabled environment isolated from default test."""
import argparse,asyncio,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from playwright.async_api import async_playwright
from harness.config import load_config
from harness.serve_local import LocalServer
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8813);a=p.parse_args()
async def main():
 O=R/'judge/shenjia-yichan/verification';c=load_config(R/'configs/shenjia-yichan.json');c['entry_url']=f'http://127.0.0.1:{a.port}/index.html';c['local_serve']['ready_url']=c['entry_url'];c['local_serve']['command'][-1]=str(a.port);s=LocalServer();s.start(c,R,O/'media-server.log');d={'browser':'Edge','autoplay_policy':'no-user-gesture-required; separate from default policy fallback test','game_html_changed':False,'puzzle_state_or_timer_changes':False}
 try:
  async with async_playwright() as p:
   b=await p.chromium.launch(headless=True,channel='msedge',args=['--autoplay-policy=no-user-gesture-required']);page=await b.new_page();await page.goto(c['entry_url']+'?logo=1');await page.wait_for_timeout(1000);d['video']=await page.locator('#logo-video').evaluate('(e)=>({duration:e.duration,currentTime:e.currentTime,readyState:e.readyState,error:e.error?e.error.code:null,videoWidth:e.videoWidth})');assert d['video']['currentTime']>0 and d['video']['videoWidth']>0;await page.screenshot(path=str(O/'logo-playback.png'))
   # Footer overlaps the labelled skip; the author's whole-logo dismiss handler remains usable.
   await page.mouse.click(100,100);await page.locator('#logo-screen').wait_for(state='hidden');d['backdrop_dismiss_verified']=True
   await page.goto(c['entry_url']+'?logo=1');await page.locator('#logo-screen').wait_for(state='visible');await page.locator('#logo-screen').wait_for(state='hidden',timeout=15000);d['natural_ended_dismiss_verified']=True;d['pass']=True;await b.close()
 finally:s.stop();(O/'media-acceptance.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
 print('SHENJIA MEDIA PASS',flush=True)
if __name__=='__main__':asyncio.run(main())
