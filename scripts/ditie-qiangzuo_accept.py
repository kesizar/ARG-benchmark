from pathlib import Path
import asyncio,json,subprocess,sys,importlib.util
from playwright.async_api import async_playwright
R=Path(__file__).resolve().parents[1];A=R/'tasks/ditie-qiangzuo/audit'
class Adapter:
 pending=None
 def __init__(self,p):self.p=p
 async def page_expr(self,e):return await self.p.evaluate(e)
async def exercise(root,port,label):
 print('accept-start',label,flush=True)
 engine=root/'harness/judge.py' if (root/'harness/judge.py').exists() else R/'harness/judge.py'
 spec=importlib.util.spec_from_file_location('ditie_judge',engine);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 print('judge-loaded',flush=True)
 jp=root/'judge/ditie-qiangzuo/judge.json' if (root/'judge/ditie-qiangzuo/judge.json').exists() else R/'judge/ditie-qiangzuo/judge.json'
 game=root/'tasks/ditie-qiangzuo/mirror' if (root/'tasks/ditie-qiangzuo/mirror').exists() else root
 serve=root/'scripts/serve_static.py' if (root/'scripts/serve_static.py').exists() else R/'scripts/serve_static.py'
 log=open(A/(label+'-server.log'),'w');server=subprocess.Popen([sys.executable,str(serve),'--root',str(game),'--port',str(port)],stdout=log,stderr=subprocess.STDOUT)
 print('server-start',flush=True)
 traces=[];errors=[];requests=[];url=f'http://127.0.0.1:{port}/'
 try:
  async with async_playwright() as pw:
   b=await pw.chromium.launch(channel='msedge',headless=True)
   c=await b.new_context(viewport={'width':1366,'height':900},locale='zh-CN',service_workers='block')
   async def route(r):
    requests.append(r.request.url)
    await (r.continue_() if r.request.url.startswith(url) else r.abort())
   await c.route('**/*',route);p=await c.new_page();p.set_default_timeout(6000);p.on('pageerror',lambda e:errors.append(str(e)))
   await p.goto(url);await p.wait_for_timeout(250)
   j=mod.Judge.load(jp,'ditie-qiangzuo',root)
   async def snap(stage):
    await j.read(Adapter(p));j.update(len(traces)+1);s=j.score()
    state=await p.evaluate("({running:game.isRunning,paused:game.isPaused,time:game.timeLeft,energy:game.energy,moral:game.moral,clashes:game.clashCount,seats:game.seatsWon,kind:game.kindActs,ignored:game.ignoredPriority,route:game.route?.length,speed:game.timeScale})")
    traces.append({'stage':stage,'score':s,'state':state,'visible_text':await p.locator('body').inner_text()});(A/(label+'-ui-trace.json')).write_text(json.dumps(traces,ensure_ascii=False,indent=2),encoding='utf-8');return s
   async def reset():
    nonlocal j
    j=mod.Judge.load(jp,'ditie-qiangzuo',root)
    assert not (await snap('reset_menu'))['ending_reached']
   async def fast():
    for _ in range(3):await p.locator('#speedBtn').click()
   assert not (await snap('initial_hidden_result_negative'))['ending_reached']
   # Every standard difficulty must fail normally when no seat is sought.
   for difficulty in ['easy','med','hard']:
    await p.locator('.btn-'+difficulty+'.difficulty-btn').click();assert not (await snap(difficulty+'_start_negative'))['ending_reached']
    await fast();await p.locator('#gameOverScreen').wait_for(state='visible',timeout=30000)
    s=await snap(difficulty+'_idle_exhaustion');assert s['route_id']=='exhausted' and s['ending_tier']=='bad' and s['checkpoints_reached']==0
    await p.screenshot(path=str(A/(label+'-'+difficulty+'-exhausted.png')))
    await p.locator('#gameOverScreen button').click();await reset()
   await p.locator('.btn-easy.difficulty-btn').click()
   # Easy has a visible vacant seat just left of centre on the top row.
   box=await p.locator('#gameCanvas').bounding_box()
   await p.mouse.click(box['x']+370*box['width']/960,box['y']+135*box['height']/540)
   await p.wait_for_timeout(700)
   assert await p.evaluate('Boolean(game.player.seat)')
   await p.locator('#pauseBtn').click();a=await p.evaluate('game.timeLeft');await p.wait_for_timeout(200);assert await p.evaluate('game.timeLeft')==a
   assert not (await snap('seated_pause_negative'))['ending_reached'];await p.locator('#pauseScreen [data-i18n="resume"]').click()
   await fast();await p.locator('#gameOverScreen').wait_for(state='visible',timeout=30000)
   s=await snap('easy_seated_arrival');assert s['route_id']=='arrived' and s['ending_tier']=='normal' and s['checkpoints_reached']==0
   await p.screenshot(path=str(A/(label+'-arrived.png')))
   await p.locator('#gameOverScreen button').click();await reset()
   # Custom editor is an operation utility, never a reasoning checkpoint.
   await p.locator('.btn-custom').click();await p.locator('#c-easy').click()
   upload=p.locator('input[type="file"]')
   await upload.set_input_files({'name':'bad.json','mimeType':'application/json','buffer':b'[]'})
   await p.wait_for_timeout(150);assert '至少' in await p.locator('#importStatus').inner_text();await snap('custom_import_reject')
   await upload.set_input_files({'name':'route.json','mimeType':'application/json','buffer':'[{"en":"A","zh":"甲"},{"en":"B","zh":"乙"}]'.encode()})
   await p.wait_for_timeout(150);assert await p.locator('.station-row').count()==2
   await p.locator('#saveNameInput').fill('Acceptance');await p.get_by_role('button',name='Save route',exact=True).click();assert await p.locator('.save-name').count()==1
   await p.locator('.save-name').click();await snap('custom_import_save_load')
   await p.locator('.save-list-row .btn-remove').click();assert await p.locator('.save-name').count()==0
   await p.locator('#customScreen [data-i18n="start"]').click();await p.wait_for_timeout(150);assert await p.evaluate('game.route.length===2 && game.totalDuration===18')
   await p.keyboard.press('p');assert await p.locator('#pauseScreen').is_visible();await p.keyboard.press('p')
   await p.locator('#restartBtn').click();await reset();assert not await p.evaluate('game.isRunning')
   await p.locator('.btn-hard.difficulty-btn').click();s=await snap('new_run_counters_reset');assert await p.evaluate('game.seatsWon===0 && game.kindActs===0 && game.ignoredPriority===0 && game.energy>95')
   await p.locator('#restartBtn').click();await reset()
   await p.reload();j=mod.Judge.load(jp,'ditie-qiangzuo',root);assert not (await snap('reload_reset'))['ending_reached']
   assert not errors,errors
   assert all(u.startswith(url) for u in requests),requests
   await b.close()
 finally:server.terminate();server.wait(timeout=10);log.close()
 (A/(label+'-summary.json')).write_text(json.dumps({'passed':True,'stages':len(traces),'page_errors':errors,'requests':sorted(set(requests)),'root':str(root),'port':port,'normal_ui_only':True,'evaluation_reads_only':True,'coverage_limit':'Source maps all mechanics; runtime covers each difficulty exhaustion, easy arrival, pause/speed/menu/restart and custom import/save/load/delete. Random priority yield/ignore and all stars not guaranteed by these runs; no state injection.'},ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':asyncio.run(exercise(Path(sys.argv[1]).resolve() if len(sys.argv)>1 else R,int(sys.argv[2]) if len(sys.argv)>2 else 8831,sys.argv[3] if len(sys.argv)>3 else 'workspace'))
