from pathlib import Path
import asyncio,json,sys,subprocess,time,zipfile,hashlib
R=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(R))
from playwright.async_api import async_playwright
from harness.judge import Judge
T=R/'tasks/huicheng-317'; A=T/'audit'; J=R/'judge/huicheng-317'

def setup():
    old=J/'judge.json'
    hooks={}
    for k in 'ABCD':hooks['end_'+k.lower()]={'type':'js_truthy','expr':f"document.querySelector('#ending').classList.contains('show') && document.querySelector('#endTag').textContent.startsWith('结局 {k} ·')"}
    hooks['dragged']={'type':'js_truthy','expr':"document.querySelector('#ending').classList.contains('show') && document.querySelector('#endTag').textContent==='过早结局 · 被拖走'"}
    hooks['archive_lock']={'type':'js_truthy','expr':"(document.querySelector('#mini').classList.contains('show') || document.querySelector('#scTitle').textContent==='档案室 · 内部') && ['2600','suburb'].includes(document.querySelector('#miniInput').value.trim().toLowerCase()) && document.querySelector('#miniOut').textContent==='锁舌弹开。档案室的门，为你打开了。'"}
    j=dict(hooks=hooks,checkpoints=[dict(id='archive_lock',hook='archive_lock',op='truthy',role='optional')],events={},routes=[dict(id='end_'+k.lower(),tier='normal',gates=[],ending=dict(hook='end_'+k.lower(),op='truthy')) for k in 'ABCD']+[dict(id='dragged',tier='bad',gates=[],ending=dict(hook='dragged',op='truthy'))],ending=dict(hook='end_c',op='truthy'),answer_sha256=[],request_milestones=[],submit_conclusion=dict(enabled=False))
    old.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
    (J/'checkpoint-spec.json').write_text(json.dumps(dict(reasoning_points=[dict(id='archive_lock',answer=['2600','suburb'],evidence='original.html:401-408,553-566; board says next departure26:00',role='optional',latch='Judge checkpoint first positive observation',routes='All routes may bypass through tunnel; suburb has no visible clue and is undisclosed alternate')],endings={k:'normal: original supplies no ranked good/bad tier' for k in 'ABCD'},failure='sanity0 before act3; setAct never3, but act4 protects',risks=['Repeated bus/city locations count again; no inference required.','C offered without archive or burnedNeg prerequisite.','S.act remains1 during act3; sanity0 driver can create premature ending then continue choices.','Replay resets current state but retains localStorage endings, runNum fixed until reload.','Mini output retained between replay; judge requires visible modal yet new modal stale success must be fixed/guarded.']),ensure_ascii=False,indent=2),encoding='utf-8')

class H:
    def __init__(self,p):self.p=p
    async def page_expr(self,e):return await self.p.evaluate(e)

async def main():
    log=[]; server=subprocess.Popen([sys.executable,str(R/'scripts/serve_static.py'),'--root',str(T/'mirror'),'--port','8821'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
      async with async_playwright() as pw:
        browser=await pw.chromium.launch(headless=True,channel="msedge")
        ctx=await browser.new_context(viewport={'width':1366,'height':900},reduced_motion='reduce')
        p=await ctx.new_page(); await p.clock.install(); await p.goto('http://127.0.0.1:8821/index.html'); await p.clock.fast_forward(2500)
        async def tick():await p.clock.run_for(25000)
        async def click(text):
            await p.get_by_role('button',name=text,exact=True).click();await tick();log.append(dict(action=text,title=await p.locator('#scTitle').inner_text(),end=await p.locator('#endTag').inner_text()))
        async def start():
            await p.reload();await p.clock.run_for(2500);await p.locator('#boot').click();await tick();await click('02走向大厅')
        async def enter():
            await click('②大厅尽头 · 结着雾的窗');await click('擦开玻璃，看出去');await click('②转身离开，不再看')
            await click('④站台尽头 · 那道隧道');await click('②倒放报站，听清那句话');await click('→我感觉知道得够多了');await click('①走向车门');await click('它朝你伸出手')
        # Initial negatives and all branch actions are replayed solely through UI.
        await start(); judge=Judge.load(J/'judge.json','huicheng-317',R); vals=await judge.read(H(p));assert not any(vals.values());log.append(dict(initial_negative=vals))
        for action,reply in [('①候车区 · 发车时刻牌','①盯着 317 那行字'),('①候车区 · 发车时刻牌','②移开视线，只看别的线路'),('⑤长椅 · 再检查随身物','←回到大厅')]:await click(action);await click(reply)
        await click('③维修间 · 档案室');await click('←先回大厅');await click('③维修间 · 档案室');await click('①输入四位密码')
        await p.locator('#miniInput').fill('0000');await p.locator('#miniOk').click();assert not (await judge.read(H(p)))['archive_lock'];log.append(dict(wrong_password_negative=True))
        await p.locator('#miniInput').fill('2600');await p.locator('#miniOk').click();assert (await judge.read(H(p)))['archive_lock'];judge.update(1);await tick();await click('①带走这卷胶片')
        await click('③维修间 · 档案室');await click('②烧掉这卷胶片');await click('③维修间 · 档案室');await click('③只看，不碰')
        for a in ['①走近隧道口','③用板材堵上这道缝']:await click('④站台尽头 · 那道隧道');await click(a)
        await enter();await click('C烧掉中枢站总档，掐断循环');assert (await judge.read(H(p)))['end_c'];await p.screenshot(path=str(A/'ending-C.png'));log.append(dict(checkpoint_latched=judge.checkpoints))
        await click('重头再来');assert not any((await judge.read(H(p))).values());log.append(dict(replay_negative=True))
        await start();await enter();await click('B逃回出口，删掉所有影像');assert (await judge.read(H(p)))['end_b'];await p.screenshot(path=str(A/'ending-B.png'))
        for end in ['A','D']:
            await start();await enter();await click('A上车。回到那座城')
            for a in ['①驾驶座 · 那本日志','②车窗 · 望向隧道','③投币箱 · 车票','④乘客 · 它们不看你']:await click(a);await click('←回到车厢')
            await click('→到站了，下车')
            for a in (['①中心车站 · 返程时刻表','②八十层的瓷砖楼 · 你的公寓','③楼顶的小学 · 涂鸦'] if end=='A' else ['④二十三楼的菜市场 · 记忆摊位']*3):await click(a);await click('←回到中心车站')
            await click('收起手机，留下' if end=='A' else '按下返程');assert (await judge.read(H(p)))['end_'+end.lower()];await p.screenshot(path=str(A/f'ending-{end}.png'))
        await start();await click('③维修间 · 档案室');await click('①输入四位密码');await p.locator('#miniInput').fill('suburb');await p.locator('#miniOk').click();assert not (await judge.read(H(p)))['archive_lock'];log.append(dict(suburb_unreachable_maxlength4=True,actual=await p.locator('#miniInput').input_value()));await p.locator('#miniInput').fill('2600');await p.locator('#miniOk').click();assert (await judge.read(H(p)))['archive_lock'];await tick();await click('③只看，不碰')
        await click('③维修间 · 档案室');await click('③只看，不碰')
        await p.reload();await p.clock.run_for(2500);await p.locator('#boot').click();await tick();await click('01检查口袋里的东西')
        await click('②大厅尽头 · 结着雾的窗');await click('擦开玻璃，看出去');await click('①再看一眼，确认它还在')
        # Fresh-context failure: fifty wrong submissions exhaust sanity.
        await start();await click('③维修间 · 档案室');await click('①输入四位密码');await p.locator('#miniInput').fill('0000')
        for _ in range(50):await p.locator('#miniOk').click()
        vals=await judge.read(H(p));assert vals['dragged'] and not vals['archive_lock'] and not any(vals['end_'+x] for x in 'abcd');await p.screenshot(path=str(A/'failure.png'));log.append(dict(failure_values=vals))
        await ctx.clear_cookies();await p.evaluate('localStorage.clear()');await p.reload();assert await p.evaluate('localStorage.length')==0;log.append(dict(hard_reset=True))
        await browser.close()
    finally:
      server.terminate();(A/'ui-evidence.json').write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8')
    print('UI acceptance passed',len(log))

if __name__=='__main__':
    if '--setup' in sys.argv:setup()
    else:asyncio.run(main())
