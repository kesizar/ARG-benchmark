"""Curator resource smoke test; native browser player actions, no game-state writes."""
import asyncio,json,sys,argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--port',type=int,default=8831);a=p.parse_args();R=a.root.resolve();sys.path.insert(0,str(R))
from harness.config import load_config
from harness.browser_harness import BrowserHarness
from harness.serve_local import LocalServer
async def main():
 out=R/'judge/yongyuan-xiatian/verification/media';out.mkdir(parents=True,exist_ok=True);cfg=load_config(R/'configs/yongyuan-xiatian.json');cfg['allow_hosts']=[f'127.0.0.1:{a.port}'];cfg['local_serve']['command'][-1]=str(a.port);cfg['local_serve']['port']=a.port;cfg['local_serve']['ready_url']=f'http://127.0.0.1:{a.port}/index.html';cfg['entry_url']=cfg['local_serve']['ready_url'];cfg['settle_ms']=80;s=LocalServer();h=BrowserHarness(cfg,out);rows=[]
 try:
  s.start(cfg,R,out/'server.log');await h.start();await h.reset()
  for name in ['mon_dongpo','qingxi_promo','qingxi_sea']:
   await h.page.goto(f'http://127.0.0.1:{a.port}/game/assets/_will/{name}.mp4');await h.page.locator('video').wait_for();await h.page.wait_for_timeout(1500)
   read="()=>{const v=document.querySelector('video');return {duration:v.duration,width:v.videoWidth,height:v.videoHeight,time:v.currentTime,paused:v.paused,error:v.error?{code:v.error.code,message:v.error.message}:null}}"
   d=await h.page.evaluate(read)
   if d['paused']:
    b=await h.page.locator('video').bounding_box();assert await h.act({'op':'click','x':b['x']+b['width']/2,'y':b['y']+b['height']/2})=='ok'
   await h.page.wait_for_timeout(2000);d=await h.page.evaluate(read);assert d['duration']>0 and d['width']>0 and d['height']>0 and d['time']>0 and not d['error'],d;await h.page.screenshot(path=str(out/f'{name}.png'));rows.append({'file':name+'.mp4',**d})
  assert not h.blocked;(out/'acceptance.json').write_text(json.dumps({'pass':True,'kind':'native_player_resource_decode_smoke_not_gameplay_or_model_score','videos':rows},indent=2),encoding='utf-8');print(rows)
 finally:
  try:await asyncio.wait_for(h.close(),15)
  except asyncio.TimeoutError:pass
  s.stop()
asyncio.run(main())
