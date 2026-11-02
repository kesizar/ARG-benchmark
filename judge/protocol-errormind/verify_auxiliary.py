"""Focused actual tab-visibility branch; no synthetic DOM events or state edits."""
import argparse,asyncio,importlib.util,json,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--deployment',required=True);a=p.parse_args();R=Path(a.deployment).resolve();sys.path.insert(0,str(R));sys.argv=['protocol-aux','--port','8811'];sp=importlib.util.spec_from_file_location('pe',R/'judge/protocol-errormind/verify_sample.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
async def main():
 O=R/'judge/protocol-errormind/verification';c=v.load_config(R/'configs/protocol-errormind.json');c['entry_url']='http://127.0.0.1:8811/index.html';c['allow_hosts']=['127.0.0.1:8811'];c['local_serve'].update(port=8811,ready_url=c['entry_url']);c['local_serve']['command'][-1]='8811';s=v.LocalServer();h=v.BrowserHarness(c,O,headless=False);d={'deployment_root':str(R),'synthetic_visibility_events':False,'game_state_injection':False}
 try:
  s.start(c,R,O/'aux-server.log');assert s.owned;await h.start();await h.reset();x=v.Audit(h,c);await x.record({'op':'fresh_context'});await x.click('[onclick="goToLevel(1)"]');await x.screen(1)
  for _ in range(3):await x.click('#l1-btn');await x.wait(1300)
  await x.click('#enter-real');await x.screen(2);await x.hover('#invisible-text');await x.wait(600);await x.click('#l2-btn');await x.screen(3)
  original=h.page;d['initial_visibility']=await original.evaluate('document.visibilityState');cdp=await h.context.new_cdp_session(original);win=await cdp.send('Browser.getWindowForTarget');await cdp.send('Browser.setWindowBounds',{'windowId':win['windowId'],'bounds':{'windowState':'minimized'}})
  try:
   await original.wait_for_function('document.hidden===true',timeout=1500,polling=100);d['away_visibility']=await original.evaluate('document.visibilityState');d['actual_hidden_observed']=True
  except Exception as e:d['actual_hidden_observed']=False;d['visibility_limitation']=repr(e);d['after_minimize_visibility']=await original.evaluate('document.visibilityState')
  await cdp.send('Browser.setWindowBounds',{'windowId':win['windowId'],'bounds':{'windowState':'normal'}});await original.bring_to_front()
  if d['actual_hidden_observed']:
   await original.locator('#tab-warning.show').wait_for(state='visible');d['warning']=await original.locator('#tab-warning').inner_text();await x.click('[onclick="dismissTabWarn()"]');assert not await original.locator('#tab-warning').is_visible()
  assert not x.j.checkpoints and not x.j.ending_reached
  d['visibility_trigger']='actual browser window minimize/restore; no synthetic document events'
  await h.page.reload();await h.page.locator('#screen-0.active').wait_for(state='visible');fresh=v.Audit(h,c);await fresh.record({'op':'normal_reload'});assert not fresh.j.checkpoints and not fresh.j.ending_reached;d['normal_reload_restarts_level0']=True
  d['speech_voices']=await h.page.evaluate("'speechSynthesis' in window?speechSynthesis.getVoices().map(v=>({name:v.name,localService:v.localService,lang:v.lang})):[]");d['trace']=x.trace;d['reset_pass']=True;d['pass']=d['actual_hidden_observed'];d['status']='pass' if d['pass'] else 'optional_visibility_environment_limited'
 except Exception as e:d['pass']=False;d['error']=repr(e);raise
 finally:(O/'auxiliary-acceptance.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();s.stop()
 print('ERRORMIND AUXILIARY '+d.get('status','failed'),flush=True)
if __name__=='__main__':asyncio.run(main())
