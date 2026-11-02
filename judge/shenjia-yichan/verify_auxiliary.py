"""Actual UI checks of ancillary branches and original logo, no score injection."""
import asyncio,importlib.util,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
sp=importlib.util.spec_from_file_location('shen_verify',R/'judge/shenjia-yichan/verify_sample.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
async def main():
 c=v.load_config(R/'configs/shenjia-yichan.json');port=v.a.port;c['entry_url']=f'http://127.0.0.1:{port}/index.html';c['allow_hosts']=[f'127.0.0.1:{port}'];c['local_serve'].update(port=port,ready_url=c['entry_url']);c['local_serve']['command'][-1]=str(port);c['settle_ms']=100
 out=R/'judge/shenjia-yichan/verification';s=v.LocalServer();h=v.BrowserHarness(c,out);report={'deployment_root':str(R),'state_injection':False,'search_groups':[],'auxiliary':[],'page_errors':[],'http_errors':[]}
 try:
  s.start(c,R,out/'aux-server.log');assert s.owned;await h.start();await h.reset();h.page.on('pageerror',lambda e:report['page_errors'].append(str(e)));h.context.on('response',lambda r:report['http_errors'].append({'url':r.url,'status':r.status}) if r.status>=400 else None);x=v.Audit(h);await x.begin()
  inv=json.loads((out/'source-inventory.json').read_text(encoding='utf-8'))
  for group in ([] if v.a.quick else inv['search']):
   await x.type('#address-bar','http://baitong.test/',True);await x.type('#search-input',group['keywords'][0],True)
   targets=await h.page.locator('#browser-content .result-title').evaluate_all('(es)=>es.map(e=>e.getAttribute("onclick"))');expected=["navigateTo('clue:"+id+"')" for id in group['clues']];assert set(expected)<=set(targets),(group,targets);report['search_groups'].append({'keyword':group['keywords'][0],'expected':group['clues'],'result_count':len(targets)})
  for i in range(4):await x.click(f'.bookmark-bar .bookmark:nth-child({i+1})')
  report['auxiliary'].append('four_bookmarks')
  await x.click('#back-btn');await x.click('#forward-btn');await x.click('[onclick="goHome()"]');report['auxiliary'].append('back_forward_home')
  # Notepad is a toolbar button with native prompt.
  selectors=await h.page.locator('[onclick],[ondblclick]').evaluate_all('(es)=>es.map(e=>({tag:e.tagName,onclick:e.getAttribute("onclick"),dbl:e.getAttribute("ondblclick")}))')
  (out/'aux-controls.json').write_text(json.dumps(selectors,ensure_ascii=False,indent=2),encoding='utf-8')
  if await h.page.locator('[onclick="openNotepad()"]:visible').count():
   await x.click('[onclick="openNotepad()"]');assert h.pending;await x.act({'op':'dialog','accept':True,'text':'UI audit note'});await x.click('[onclick="openNotepad()"]');assert h.pending and h.pending.get('default_value')=='UI audit note';await x.act({'op':'dialog','accept':False});report['auxiliary'].append('notepad_prompt_accept_cancel')
  await x.click('#start-btn');await x.click('[onclick='+json.dumps("startMenuAction('help')")+']');await x.material('help');report['auxiliary'].append('help')
  await x.click('#start-btn');await x.click('[onclick='+json.dumps("startMenuAction('shelf')")+']');assert await h.page.locator('#evidence-shelf').is_visible();await x.click('[onclick="toggleEvidenceShelf()"]');report['auxiliary'].append('empty_evidence_shelf')
  await x.click('#start-btn');await x.click('[onclick='+json.dumps("startMenuAction('settings')")+']');assert await h.page.locator('#settings-overlay').is_visible()
  await x.click('#ratio43-toggle');assert await h.page.locator('#game-container.ratio-43').count();await x.click('#ratio43-toggle');assert not await h.page.locator('#game-container.ratio-43').count();await x.click('[onclick="closeSettings()"]');report['auxiliary'].append('ratio_toggle')
  await x.click('#start-btn');await x.click('[onclick='+json.dumps("startMenuAction('fontsize')")+']');assert await h.page.locator('#fontsize-overlay').is_visible()
  for scale in await h.page.locator('.fontsize-btn').evaluate_all('(es)=>es.map(e=>e.getAttribute("data-scale"))'):
   await x.click('.fontsize-btn[data-scale='+json.dumps(scale)+']')
  await x.click('[onclick="confirmFontScale()"]');report['auxiliary'].append('font_scale_choices')
  await x.click('#start-btn');await x.click('[onclick='+json.dumps("startMenuAction('settings')")+']');await x.click('[onclick="confirmResetGame()"]');assert h.pending;await x.act({'op':'dialog','accept':False});assert await h.page.locator('#settings-overlay').is_visible();await x.click('[onclick="confirmResetGame()"]');await x.act({'op':'dialog','accept':True});await h.page.locator('#splash-screen').wait_for(state='visible');assert await h.page.evaluate('localStorage.getItem("shen_family_save")') is None;report['auxiliary'].append('native_in_game_reset_cancel_accept')
  # Original video query route, genuine playback / ended or authored skip.
  await h.page.goto(f'http://127.0.0.1:{port}/index.html?logo=1');await h.page.wait_for_timeout(1500)
  if await h.page.locator('#logo-video').count():
   meta=await h.page.locator('#logo-video').evaluate('(e)=>({duration:e.duration,currentTime:e.currentTime,readyState:e.readyState,error:e.error?e.error.code:null,videoWidth:e.videoWidth})');assert meta['readyState']>=2 and not meta['error'] and meta['videoWidth']>0;report['logo_video']=meta
   await h.page.screenshot(path=str(out/'logo.png'));await h.page.locator('#logo-skip').click();await h.page.locator('#logo-screen').wait_for(state='hidden');report['auxiliary'].append('original_logo_playback_and_skip')
  else:
   assert await h.page.locator('#splash-screen').is_visible();report['auxiliary'].append('original_logo_autoplay_policy_fallback_dismisses_to_splash')
  assert not report['page_errors'] and not report['http_errors'] and not h.blocked;report['pass']=True
 except Exception as e:
  report['pass']=False;report['error']=repr(e)
  if h.page:await h.page.screenshot(path=str(out/'aux-failure.png'))
  raise
 finally:
  (out/'auxiliary-acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();s.stop()
 print('SHENJIA AUX PASS',flush=True)
if __name__=='__main__':asyncio.run(main())
