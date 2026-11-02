"""Supplement: exercise the obituary photograph's visible ID reveal through the UI."""
import asyncio,importlib.util,json
from pathlib import Path
S=Path(__file__).with_name('verify_sample.py');spec=importlib.util.spec_from_file_location('private_fengnian_replay',S);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
async def main():
 c=mod.load_config(mod.R/f'configs/{mod.T}.json');c['entry_url']=f'http://127.0.0.1:{mod.A.port}/index.html';c['allow_hosts']=[f'127.0.0.1:{mod.A.port}'];c['local_serve'].update(port=mod.A.port,ready_url=c['entry_url']);c['local_serve']['command'][-1]=str(mod.A.port)
 s=mod.LocalServer();h=mod.BrowserHarness(c,mod.OUT)
 try:
  s.start(c,mod.R,mod.OUT/'media-server.log');await h.start();await h.reset();r=mod.Replay(h);await r.prepare();f=await r.hospital();f=await r.search(f,'王羽','wangyu');await r.click(f,'#toggleImg');assert (await f.locator('#toggleImg').get_attribute('src'))=='wangyu_2.jpg';await r.shot('obituary-ID-reveal');await r.click(f,'#toggleImg');assert (await f.locator('#toggleImg').get_attribute('src'))=='wangyu_1.jpg'
  (mod.OUT/'media-acceptance.json').write_text(json.dumps({'passed':True,'scope':'obituary_photo_flip_and_restore','visible_image_clue':'00023 on wangyu_2.jpg coat','private_source_assisted':True,'state_injection':False,'trace':r.trace},ensure_ascii=False,indent=2),encoding='utf-8')
 finally:await h.close();s.stop()
 print('obituary photo UI reveal and restore passed')
asyncio.run(main())
