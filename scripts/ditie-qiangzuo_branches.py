from pathlib import Path
import asyncio,json,subprocess,sys
from playwright.async_api import async_playwright
R=Path(__file__).resolve().parents[1];A=R/'tasks/ditie-qiangzuo/audit'
async def main():
 log=open(A/'branches-server.log','w');s=subprocess.Popen([sys.executable,str(R/'scripts/serve_static.py'),'--root',str(R/'tasks/ditie-qiangzuo/mirror'),'--port','8831'],stdout=log,stderr=subprocess.STDOUT)
 out=[]
 try:
  async with async_playwright() as pw:
   b=await pw.chromium.launch(channel='msedge',headless=True);c=await b.new_context(viewport={'width':1366,'height':900},locale='zh-CN');p=await c.new_page()
   await p.goto('http://127.0.0.1:8831/');await p.wait_for_timeout(200)
   async def canvas(x,y):
    box=await p.locator('#gameCanvas').bounding_box();await p.mouse.click(box['x']+x*box['width']/960,box['y']+y*box['height']/540)
   async def snap(stage):
    a=await p.evaluate("({energy:game.energy,moral:game.moral,clashes:game.clashCount,kind:game.kindActs,ignored:game.ignoredPriority,seats:game.seatsWon,seated:!!game.player?.seat,time:game.timeLeft})");out.append({'stage':stage,'state':a});return a
   # Test the visible orange vacant-seat penalty through ordinary canvas movement.
   for attempt in range(24):
    await p.locator('.btn-easy.difficulty-btn').click()
    seat=await p.evaluate('game.seats.filter(s=>s.isVacant&&s.isPriority).map(s=>({x:s.x+25,y:s.y+25}))[0] || null')
    if seat:
     await canvas(seat['x'],seat['y']);await p.wait_for_timeout(700);a=await snap('orange_vacant_seat_penalty');assert a['seated'] and a['moral']<=70
     await p.locator('#standBtn').click();a=await snap('stand_button');assert not a['seated'];await p.locator('#restartBtn').click();break
    await p.locator('#restartBtn').click()
   else:raise AssertionError('No orange vacant seat sampled')
   # Select a visible NPC and deliberately walk into it; collision reduces moral.
   await p.locator('.btn-hard.difficulty-btn').click()
   npc=await p.evaluate('game.npcs.filter(n=>!n.seat&&!n.isExiting).map(n=>({x:n.x,y:n.y}))[0]')
   await canvas(npc['x'],npc['y']);await p.wait_for_timeout(800);a=await snap('collision');assert a['clashes']>0 and a['moral']<100;await p.locator('#restartBtn').click()
   # Priority arrival is random. Retry whole unmodified runs, never inject events.
   for attempt in range(6):
    await p.locator('.btn-easy.difficulty-btn').click();await canvas(370,135);await p.wait_for_timeout(700)
    assert await p.evaluate('!!game.player.seat')
    for _ in range(3):await p.locator('#speedBtn').click()
    try:await p.locator('#priorityEventAction').wait_for(state='visible',timeout=19000)
    except Exception:
     if await p.locator('#gameOverScreen').is_visible():await p.locator('#gameOverScreen button').click()
     else:await p.locator('#restartBtn').click()
     continue
    await p.locator('#priorityEventAction').click();a=await snap('priority_yield');assert a['kind']>=1 and not a['seated'];await p.screenshot(path=str(A/'workspace-yield.png'))
    await p.locator('#restartBtn').click();break
   else:raise AssertionError('No actionable priority event sampled')
   await b.close()
 finally:s.terminate();s.wait(timeout=10);log.close();(A/'branches-ui-trace.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
 (A/'branches-summary.json').write_text(json.dumps({'passed':True,'normal_ui_only':True,'traces':out,'target_selection':'Evaluator reads only visible actor/seat geometry and status; no state mutation, event injection or RNG replacement.'},ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':asyncio.run(main())
