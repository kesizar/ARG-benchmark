"""Check informational, file, and notes branches from an extracted bundle."""
import argparse,asyncio,importlib.util,json,re,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2]);p.add_argument('--port',type=int,default=8833);a=p.parse_args();root=a.root.resolve();sys.path.insert(0,str(root))
spec=importlib.util.spec_from_file_location('sis_verifier',root/'judge/sis/verify_sample.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
async def main():
 cfg=v.load_config(root/'configs/sis.json');cfg['entry_url']=f'http://127.0.0.1:{a.port}/SIS/index.html';cfg['allow_hosts']=[f'127.0.0.1:{a.port}'];cfg['local_serve'].update({'port':a.port,'ready_url':cfg['entry_url']});cfg['local_serve']['command'][-1]=str(a.port);cfg['settle_ms']=250
 out=root/'judge/sis/verification';server=v.LocalServer();h=v.BrowserHarness(cfg,out)
 try:
  server.start(cfg,root);await h.start();await h.reset();r=v.Replay(h,v.Judge.load(root/cfg['judge_path'],'sis',root));await r.record({'op':'fresh'})
  await r.button('关于');assert await h.page.locator('.about-card').count()==1;await r.click('.about-card .modal-close')
  await r.button('开始');await r.click(h.page.get_by_role('button',name=re.compile('电子捐赠证明.pdf')));await r.button('保存到文件');await r.click(h.page.get_by_role('button',name=re.compile('电子捐赠证明.pdf')));assert '电子捐赠证明.pdf' in await h.page.locator('body').inner_text()
  await r.button('邮箱');await r.click(h.page.get_by_role('button',name=re.compile('捐赠资料存档')));await r.button('文件');await r.click(h.page.get_by_role('button',name=re.compile('捐赠资料存档')));assert await h.page.locator('input[placeholder="捐献者的紧急联系人姓名"]').count()==1
  await r.click(h.page.get_by_role('button',name=re.compile('值得记下的')));assert await h.page.locator('.notes-drawer li').count()>=3;await r.click('.notes-drawer .modal-close')
  assert not r.j.checkpoints and not r.j.side
  (out/'auxiliary-acceptance.json').write_text(json.dumps({'pass':True,'deployment_root':str(root),'about_dialog':True,'file_attachment_navigation':True,'cloud_file_navigation':True,'notes_drawer':True,'unscored_no_points':True,'steps':r.steps},ensure_ascii=False,indent=2),encoding='utf-8');print('auxiliary branches passed')
 finally:await h.close();server.stop()
asyncio.run(main())
