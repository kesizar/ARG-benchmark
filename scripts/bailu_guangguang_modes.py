import asyncio,json,pathlib,sys,subprocess
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from playwright.async_api import async_playwright
from harness.judge import Judge
R=pathlib.Path(__file__).resolve().parents[1];D=R/'runs/bailu-guangguang';out=[]
async def main():
 server=subprocess.Popen([sys.executable,str(R/'scripts/serve_static.py'),'--root',str(R/'tasks/bailu-guangguang/mirror'),'--port','8813'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  async with async_playwright() as pw:
   b=await pw.chromium.launch(channel='msedge',headless=True)
   for mode in ['off','on']:
    c=await b.new_context();p=await c.new_page();await p.goto('http://127.0.0.1:8813/index.html');await p.get_by_text('② 不添加提示（挑战模式）' if mode=='off' else '① 添加提示（推荐初次游玩）',exact=True).click();await p.get_by_role('button',name='进入网站（无提示挑战）' if mode=='off' else '进入网站（开启提示）',exact=True).click()
    if mode=='on':
     await p.get_by_role('button',name='💡 提示',exact=True).click()
     for n in range(2):await p.get_by_role('button',name='还是不明白，再给一点提示 »',exact=True).click()
     await p.get_by_role('button',name='知道了',exact=True).click()
    await p.locator('a[href="#/markers"]').first.click();row=p.locator('tr').filter(has=p.locator('td',has_text='Y-5')).last;await row.locator('input').fill('欢迎回来');await row.get_by_role('button',name='点亮',exact=True).click();await p.locator('a[href="#/volunteer"]').first.click();await p.locator('input[type=password]').fill('245');await p.get_by_role('button',name='登 录',exact=True).click();await p.wait_for_timeout(100)
    state=await p.evaluate('JSON.parse(localStorage.getItem("egret_bureau_save_v1"))');j=json.loads((R/'judge/bailu-guangguang/judge.json').read_text(encoding='utf8'));vals={k:await p.evaluate(h['expr']) for k,h in j['hooks'].items()};assert not state['republished'] and 'Y-5' in state['markers'];assert state['loggedIn'];assert vals['marker_5']==(mode=='off');assert vals['login']==(mode=='off');assert not vals['ending'];out.append({'mode':mode,'state':state,'hooks':vals,'early_Y5_confirmed':True});await c.close()
   await b.close()
 finally:server.terminate();server.wait(timeout=10);(D/'mode-shortcut-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
asyncio.run(main())
