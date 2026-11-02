"""Narrow regression acceptance for a refreshed independent SIS runtime bundle."""
import argparse,asyncio,hashlib,json,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--port',type=int,default=8833);a=p.parse_args();root=a.root.resolve();sys.path.insert(0,str(root))
from harness.browser_harness import BrowserHarness
from harness.config import load_config
from harness.serve_local import LocalServer

async def main():
 cfg=load_config(root/'configs/sis.json');cfg['entry_url']=f'http://127.0.0.1:{a.port}/SIS/index.html';cfg['allow_hosts']=[f'127.0.0.1:{a.port}'];cfg['local_serve'].update({'port':a.port,'ready_url':cfg['entry_url']});cfg['local_serve']['command'][-1]=str(a.port)
 out=root/'judge/sis/verification';out.mkdir(parents=True,exist_ok=True);server=LocalServer();h=BrowserHarness(cfg,out);r={'kind':'runtime_refresh_targeted_regression_not_full_route_replay','deployment_root':str(root),'port':a.port,'checks':{}}
 try:
  server.start(cfg,root,out/'runtime-refresh-server.log');await h.start();await h.reset();obs=await h.observe('runtime-000.png')
  start=next(e for e in obs['elements'] if e['label']=='开始');assert await h.act({'op':'click','n':start['n']})=='ok'
  obs=await h.observe('runtime-001.png');pdf=next(e for e in obs['elements'] if '电子捐赠证明.pdf' in e['label'] or e['label']=='PDF');assert await h.act({'op':'click','n':pdf['n']})=='ok'
  assert await h.page.locator('.document-view').count()==1;r['checks']['sis_numbered_start_and_pdf_click']=True
  second=await h.context.new_page();await second.goto('about:blank')
  # Separate synthetic test surface, explicitly not a game route or score.
  await second.set_content('''<html><head><title>Wrapped control regression</title></head><body><p style="width:170px;font:20px monospace;line-height:32px;margin:60px">prefix <a id="wrapped" href="#accepted" onclick="document.querySelector('#result').textContent='accepted'">wrapped inline link spans several separated text fragments</a> suffix</p><p id="result"></p></body></html>''')
  obs=await h.observe('runtime-002.png');link=next(e for e in obs['elements'] if 'wrapped inline link' in e['label']);point=await second.evaluate('p=>document.elementFromPoint(p.x,p.y)?.closest("a")?.id',link);assert point=='wrapped'
  assert await h.act({'op':'click','n':link['n']})=='ok';assert await second.locator('#result').text_content()=='accepted';r['checks']['wrapped_inline_numbered_click_hit_fragment']=True
  for target in [0,1,0]:
   assert await h.act({'op':'switch_tab','i':target})=='ok'
   assert await h.act({'op':'key','key':'Escape'})=='ok'
   for repeat in range(2):
    obs=await h.observe(f'runtime-tab-{target}-{repeat}.png');assert next(t['i'] for t in obs['tabs'] if t['active'])==target
    assert h.page==h.context.pages[target]
    if target==0:assert 'PDF' in obs['visible_text'] and await h.page.locator('.document-view').count()==1
    else:assert 'accepted' in obs['visible_text']
   await h.act({'op':'wait','ms':120})
  r['checks']['switch_tab_observation_selection_preserved']=True
  assert not h.blocked;r['checks']['no_external_game_requests']=True;r['runtime_hashes']={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [root/'harness/observe.py',root/'harness/browser_harness.py']};r['pass']=True
 finally:
  (out/'runtime-refresh-acceptance.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();server.stop()
 print('runtime refresh targeted checks passed')
asyncio.run(main())
