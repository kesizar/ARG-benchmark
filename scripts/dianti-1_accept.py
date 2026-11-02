from pathlib import Path
import asyncio,json,subprocess,sys,time
from playwright.async_api import async_playwright
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from harness.judge import Judge
A=R/'tasks/dianti-1/audit'
class Adapter:
 pending=None
 def __init__(self,p):self.p=p
 async def page_expr(self,e):return await self.p.evaluate(e)
async def exercise(root,port,label):
 output=[];requests=[];errors=[]
 import importlib.util
 judge_path=root/'judge/dianti-1/judge.json' if (root/'judge/dianti-1/judge.json').exists() else R/'judge/dianti-1/judge.json'
 module_path=root/'harness/judge.py' if (root/'harness/judge.py').exists() else R/'harness/judge.py'
 spec=importlib.util.spec_from_file_location('independent_judge',module_path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);Judge=mod.Judge
 game_root=root/'tasks/dianti-1/mirror' if (root/'tasks/dianti-1/mirror').exists() else root
 server_script=root/'scripts/serve_static.py' if (root/'scripts/serve_static.py').exists() else R/'scripts/serve_static.py'
 server=subprocess.Popen([sys.executable,str(server_script),'--root',str(game_root),'--port',str(port)],stdout=open(A/(label+'-server.log'),'w'),stderr=subprocess.STDOUT)
 try:
  async with async_playwright() as pw:
   b=await pw.chromium.launch(channel='msedge',headless=True)
   c=await b.new_context(viewport={'width':1366,'height':900},permissions=['clipboard-read','clipboard-write'],service_workers='block')
   async def route(r):
    requests.append(r.request.url)
    await (r.continue_() if r.request.url.startswith(f'http://127.0.0.1:{port}/') else r.abort())
   await c.route('**/*',route);p=await c.new_page();p.set_default_timeout(4000);p.on('pageerror',lambda e:errors.append(str(e)))
   j=None;step=0
   async def snap(stage):
    nonlocal step
    step+=1;await j.read(Adapter(p));j.update(step);score=j.score()
    output.append({'stage':stage,'score':score,'text':await p.locator('body').inner_text()});(A/(label+'-ui-trace.json')).write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8');return score
   async def fresh():
    nonlocal j
    await p.goto(f'http://127.0.0.1:{port}/');j=Judge.load(judge_path,'dianti-1',root)
    assert not (await snap('fresh'))['ending_reached']
   async def command(v):
    await p.locator('#termin').fill(v);await p.locator('#termin').press('Enter')
   async def close(id):await p.locator(f'[data-close="{id}"]').click()
   async def reset():
    await p.get_by_role('button',name='🔄 重新挑战').click();j2=Judge.load(judge_path,'dianti-1',root)
    assert not await p.evaluate('STATE.ended || STATE.wrongCount || STATE.terminalUnlocked || STATE.noteTaken || STATE.boardDecoded || STATE.clues.size')
    return j2
   await fresh()
   for v in ['','help','?','status','connect','connect 192.168.1.44 8080','connect 192.168.1.43 80','decrypt','decrypt ABC x','decrypt ABC 1','unknown']:
    await command(v);s=await snap('terminal_negative_or_info:'+v);assert s['checkpoints_reached']==0 and not s['ending_reached']
   await command('clear');assert 'Unknown command' not in await p.locator('#termout').inner_text()
   await close('m-phone');await p.locator('#o-screen').click()
   p.once('dialog',lambda d:d.accept());await p.locator('#btn-helpascii').click();await p.locator('#btn-copyascii').click();await close('m-screen')
   # Original main screen is the usable ASCII clue; modal logpre is never populated.
   await p.wait_for_timeout(8500);assert '80 79 82 84 63' in await p.locator('#screen').inner_text();await snap('ascii_visible')
   await p.locator('#o-vent').click();await p.locator('#btn-takenote').click();assert await p.locator('#btn-takenote').is_disabled();await snap('note');await close('m-vent')
   await p.locator('#o-board').click();await p.locator('#btn-decodehex').click();assert '8080' in await p.locator('#boardresult').inner_text();await snap('board_auto_solution');await close('m-board')
   await p.locator('#o-poster').click();assert '192.168.1.43' in await p.locator('#m-poster').inner_text();await close('m-poster')
   for n in range(1,26):await p.locator(f'.fk[data-n="{n}"]').click()
   await p.locator('#o-phone').click();await command('connect 192.168.1.43 8080');s=await snap('connect_positive');assert s['checkpoints_reached']==0 and 'connect' in s['diagnostic'] and not s['ending_reached']
   await command('decrypt WKH HOHYDWRU NHB LV NHBV 2');s=await snap('wrong_shift');assert 'plaintext' not in s['diagnostic']
   await command('decrypt WKH HOHYDWRU NHB LV NHBV 3');s=await snap('plaintext_positive');assert 'plaintext' in s['diagnostic'];await command('clear');await close('m-phone')
   await p.locator('#o-panelbtn').click();await p.locator('#btn-submitpw').click();assert (await snap('empty_password'))['checkpoints_reached']==0
   await p.locator('#pwin').fill('WRONG');await p.locator('#btn-submitpw').click();assert not (await snap('wrong_password'))['ending_reached']
   await p.locator('#pwin').fill(' keys ');await p.locator('#pwin').press('Enter');s=await snap('password_positive');assert s['checkpoints_reached']==0 and 'password' in s['diagnostic']
   await p.wait_for_timeout(1500);s=await snap('normal_ending');assert s['ending_tier']=='normal' and s['route_id']=='escape';await p.screenshot(path=str(A/(label+'-normal.png')))
   j=await reset();assert (await snap('ui_reset_normal'))['checkpoints_reached']==0
   await close('m-phone');await p.locator('#o-panelbtn').click();await p.locator('#pwin').fill('KEYS');await p.locator('#btn-submitpw').click();await p.wait_for_timeout(1500);s=await snap('direct_password_bypass');assert s['ending_reached'] and s['checkpoints_reached']==0 and 'password' in s['diagnostic']
   j=await reset();await command('egg');s=await snap('egg_ending');assert s['ending_tier']=='normal' and s['checkpoints_reached']==0;await p.screenshot(path=str(A/(label+'-egg.png')))
   j=await reset();await close('m-phone');await p.locator('#o-panelbtn').click()
   for i in range(3):
    await p.locator('#pwin').fill('WRONG');await p.locator('#btn-submitpw').click();await p.wait_for_timeout(900);s=await snap('wrong_attempt_'+str(i+1));assert s['checkpoints_reached']==0;assert not s['ending_reached'] and s['failure_reached']==(i==2)
   assert s['failure_id']=='fall';await p.screenshot(path=str(A/(label+'-fall.png')))
   j=await reset();assert not (await snap('ui_reset_bad'))['ending_reached']
   assert not errors,errors
   assert all(u.startswith(f'http://127.0.0.1:{port}/') for u in requests),requests
   await b.close()
 finally:server.terminate();server.wait(timeout=10)
 (A/(label+'-summary.json')).write_text(json.dumps({'passed':True,'stages':len(output),'page_errors':errors,'requests':sorted(set(requests)),'root':str(root),'port':port},ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':asyncio.run(exercise(Path(sys.argv[1]).resolve() if len(sys.argv)>1 else R,int(sys.argv[2]) if len(sys.argv)>2 else 8811,sys.argv[3] if len(sys.argv)>3 else 'workspace'))
