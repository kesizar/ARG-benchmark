from pathlib import Path
import asyncio,json,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from harness.config import load_config
from harness.browser_harness import BrowserHarness
from harness.serve_local import LocalServer
async def main():
 cfg=load_config(ROOT/'configs/sis.json'); cfg['entry_url']='http://127.0.0.1:8831/SIS/index.html';cfg['allow_hosts']=['127.0.0.1:8831'];cfg['local_serve']['ready_url']=cfg['entry_url'];cfg['local_serve']['port']=8831;cfg['local_serve']['command'][-1]='8831'
 out=ROOT/'runs/sis-inspect';out.mkdir(exist_ok=True);server=LocalServer();h=BrowserHarness(cfg,out)
 try:
  server.start(cfg,ROOT);await h.start();await h.reset();await h.page.get_by_role('button',name='开始',exact=True).click();await h.page.wait_for_timeout(500)
  print((await h.page.locator('body').inner_text())[:15000]);print('BUTTONS',await h.page.locator('button').all_text_contents());await h.page.screenshot(path=str(out/'mail.png'))
 finally:await h.close();server.stop()
asyncio.run(main())
