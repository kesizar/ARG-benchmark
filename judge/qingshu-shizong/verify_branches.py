"""Authored close/exit branches through ordinary UI; no gameplay state injection."""
from verify_sample import *
async def branches():
 cfg=load_config(R/f'configs/{T}.json');cfg['entry_url']=f'http://127.0.0.1:{a.port}/school.html';cfg['allow_hosts']=[f'127.0.0.1:{a.port}'];cfg['local_serve']['ready_url']=cfg['entry_url'];cfg['local_serve']['command'][-1]=str(a.port);cfg['local_serve']['port']=a.port;cfg['settle_ms']=80;h=BrowserHarness(cfg,OUT);s=LocalServer();r=Replay(h);d={}
 async def reload():
  await h.reset();await h.page.locator('#page_index').wait_for(state='visible');await r.record({'fresh_context_reset_after_trap':True});assert not await h.page.locator('#blackScreen').is_visible()
 try:
  s.start(cfg,R,OUT/'branches-server.log');await h.start();await h.reset()
  await r.click('[onclick="openVolumeKeyPopup()"]');await r.click('[onclick="closeVolumeKeyPopup()"]',True);assert not await h.page.locator('#volumeKeyPopup').is_visible()
  for close in ['silence','Escape']:
   await r.volume();b=await h.page.locator('#finalChoiceInput').bounding_box();top=await h.page.evaluate('p=>{const e=document.elementFromPoint(p.x,p.y);return {id:e.id,insideBlack:!!e.closest("#blackScreen")}}',{'x':b['x']+b['width']/2,'y':b['y']+b['height']/2});assert not top['insideBlack'] and top['id']=='finalChoiceInput';d['choice_visible_hit_target']=top;await h.page.screenshot(path=str(OUT/'choice-visible.png'))
   if close=='silence':await r.key('Tab');await r.key('Tab');await r.key('Enter')
   else:await r.key('Escape')
   assert not await h.page.locator('#choiceMask').is_visible() and await h.page.locator('#blackScreen').is_visible();assert not r.j.route_endings;await reload()
  for close in ['exit','button']:
   await r.volume();await r.choice('help');await r.terminal('help');await r.read('#terminalOutput');await h.page.screenshot(path=str(OUT/'terminal-visible.png'))
   if close=='exit':await r.terminal('exit')
   else:await r.key('Tab');await r.key('Enter')
   assert not await h.page.locator('#terminalModal').is_visible() and await h.page.locator('#blackScreen').is_visible();assert not r.j.route_endings;await reload()
  d.update(pass_=True,negative_checks=r.neg,steps=r.steps,reads=r.reads,blocked=h.blocked);assert not h.blocked
 finally:
  (OUT/'branches.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();s.stop()
if __name__=='__main__':asyncio.run(branches())
