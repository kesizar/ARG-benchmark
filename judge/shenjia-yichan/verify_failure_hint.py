"""Extra branch acceptance; import the evaluator from the deployed package."""
import asyncio,importlib.util,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
sp=importlib.util.spec_from_file_location('shen',R/'judge/shenjia-yichan/verify_sample.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
async def main():
 O=R/'judge/shenjia-yichan/verification';c=v.load_config(R/'configs/shenjia-yichan.json');port=v.a.port;c['entry_url']=f'http://127.0.0.1:{port}/index.html';c['allow_hosts']=[f'127.0.0.1:{port}'];c['local_serve'].update(port=port,ready_url=c['entry_url']);c['local_serve']['command'][-1]=str(port);c['settle_ms']=100;s=v.LocalServer();h=v.BrowserHarness(c,O);d={'deployment_root':str(R),'state_injection':False,'kind':'three_real_failed_batches_unlock_original_hint'}
 try:
  s.start(c,R,O/'hint-server.log');assert s.owned;await h.start();await h.reset();x=v.Audit(h);await x.begin();await x.open_tree()
  for n in range(3):
   for i,m in enumerate(v.MEMBERS[:3]):await x.place(m['id'],v.MEMBERS[(i+1)%3]['name'])
   await x.submit();assert not x.j.checkpoints and not x.j.side and not x.j.ending_reached
  hint=await h.page.locator('#batch-hint').inner_text();assert hint.strip();d.update(hint=hint,trace=x.trace);d['pass']=True
 finally:(O/'three-failure-hint-acceptance.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();s.stop()
 print('SHENJIA THREE FAILURE HINT PASS',flush=True)
if __name__=='__main__':asyncio.run(main())
