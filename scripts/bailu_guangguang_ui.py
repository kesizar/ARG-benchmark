import asyncio,json,pathlib,sys,subprocess
from types import SimpleNamespace
REPO=pathlib.Path(__file__).resolve().parents[1]
TARGET=pathlib.Path(sys.argv[1]).resolve() if len(sys.argv)>1 else REPO
EVAL=TARGET if (TARGET/'harness').exists() else TARGET.parent/'unpacked-prepared'
sys.path.insert(0,str(EVAL))
from harness.judge import Judge
from playwright.async_api import async_playwright
R=pathlib.Path(__file__).resolve().parents[1];D=R/'runs/bailu-guangguang';rows=[]
async def run(root=R,port=8811,full=True):
 server=subprocess.Popen([sys.executable,str(root/'scripts/serve_static.py'),'--root',str(root/'tasks/bailu-guangguang/mirror'),'--port',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  async with async_playwright() as pw:
   b=await pw.chromium.launch(channel='msedge',headless=True);ctx=await b.new_context(viewport={'width':1440,'height':1000});p=await ctx.new_page();external=[];errors=[]
   async def route(rt):
    if rt.request.url.startswith(('http://127.0.0.1:', 'data:','about:')):await rt.continue_()
    else:external.append(rt.request.url);await rt.abort()
   await ctx.route('**/*',route);p.on('pageerror',lambda e:errors.append(str(e)));await p.goto(f'http://127.0.0.1:{port}/index.html');await p.get_by_text('② 不添加提示（挑战模式）',exact=True).click();await p.get_by_role('button',name='进入网站（无提示挑战）',exact=True).click()
   jc=json.loads((root/'judge/bailu-guangguang/judge.json').read_text(encoding='utf8')) if (root/'judge/bailu-guangguang/judge.json').exists() else json.loads((EVAL/'judge/bailu-guangguang/judge.json').read_text(encoding='utf8'));judge=Judge(jc,'bailu-guangguang');h=SimpleNamespace(page_expr=p.evaluate)
   async def snap(label):
    await p.wait_for_timeout(100);await judge.read(h);judge.update(len(rows));s=await p.evaluate('JSON.parse(localStorage.getItem("egret_bureau_save_v1"))');rows.append({'deployment':port,'label':label,'state':s,'hooks':dict(judge.values),'result':judge.score()})
   async def nav(hash):await p.locator('a[href="'+hash+'"]').first.click()
   await snap('initial');await nav('#/volunteer');await p.locator('input[type=password]').fill('000');await p.get_by_role('button',name='登 录',exact=True).click();await snap('wrong-login');assert not judge.values['login'];await p.locator('input[type=password]').fill('2 4 5');await p.get_by_role('button',name='登 录',exact=True).click();await snap('login');assert judge.values['login'];assert await p.get_by_role('button',name='🚀 重新发布路线页',exact=True).is_disabled();assert await p.get_by_role('button',name='✉ 发布感谢信并打开重新开放日页面',exact=True).is_disabled()
   await nav('#/trails');await nav('#/trails/T-04');await snap('trail-gap');await nav('#/maintenance');await nav('#/archive/log24');await p.get_by_role('button',name='📌 钉到证据板',exact=True).click();await nav('#/maintenance');await nav('#/archive/t04_draft');await snap('draft');await nav('#/volunteer');assert await p.get_by_role('button',name='🚀 重新发布路线页',exact=True).is_enabled();await p.get_by_role('button',name='🚀 重新发布路线页',exact=True).click();await snap('republished');assert judge.values['republish']
   await nav('#/ending');await snap('partial-ending');assert not judge.values['ending'];await nav('#/markers')
   for n,answer in enumerate(['慢慢走','看花不摘花','听风','过桥慢行','欢迎回来'],1):
    row=p.locator('tr').filter(has=p.locator('td',has_text='Y-'+str(n))).last
    await row.locator('input').fill('错误');await row.get_by_role('button',name='点亮',exact=True).click();await snap('wrong-marker-'+str(n));assert not judge.values['marker_'+str(n)]
    await row.locator('input').fill('「'+answer+'」！');await row.get_by_role('button',name='点亮',exact=True).click();await snap('marker-'+str(n));assert judge.values['marker_'+str(n)]
   await nav('#/volunteer');await p.get_by_role('button',name='✉ 发布感谢信并打开重新开放日页面',exact=True).click();await snap('final');assert judge.values['ending'];await p.screenshot(path=str(D/f'ending-{port}.png'),full_page=True)
   # Unscored exploration branches and resources: normal link/button actions only.
   for dest in ['#/about','#/notices','#/spots','#/trails','#/logs','#/calendar','#/album','#/guestbook','#/maintenance','#/passport','#/help']:
    await nav(dest)
    images=await p.locator('img').evaluate_all('(xs)=>xs.map(i=>({src:i.currentSrc,ok:i.complete&&i.naturalWidth>0}))')
    assert all(i['ok'] for i in images),dest
    if dest=='#/notices':
     await p.get_by_role('button',name='查看本页源代码',exact=True).click();assert '听风' in await p.locator('body').inner_text();await p.get_by_role('button',name='关闭 ×',exact=True).click()
    if dest=='#/guestbook':
     await p.get_by_placeholder('例如：路过的旅人').fill('验收旅人');await p.locator('textarea').fill('谢谢志工');await p.get_by_role('button',name='发 表',exact=True).click();await p.get_by_role('button',name='📌 把这条留言钉到证据板',exact=True).click()
    await snap('side-'+dest)
   for n in range(1,7):
    await nav('#/ending' if n==6 else '#/spots');await nav('#/spots/S-0'+str(n));await p.get_by_role('button',name='🎫 在纪念护照上盖章',exact=True).click()
   await snap('six-stamps');assert len(rows[-1]['state']['stamps'])==6;assert len(rows[-1]['state']['guestbook'])==1
   await nav('#/ending')
   await p.reload();await snap('reload-persistence');assert judge.values['ending']
   p.once('dialog',lambda d:d.accept());await p.get_by_role('button',name='重置进度，再来一次',exact=True).click();judge=Judge(jc,'bailu-guangguang');await snap('reset');assert not any(judge.values.values());assert rows[-1]['state']['stamps']==[] and rows[-1]['state']['guestbook']==[];assert await p.get_by_text('② 不添加提示（挑战模式）',exact=True).is_visible();await p.screenshot(path=str(D/f'reset-{port}.png'),full_page=True)
   rows.append({'deployment':port,'external_requests':external,'page_errors':errors});assert not external and not errors;await b.close()
 finally:server.terminate();server.wait(timeout=10)
if __name__=='__main__':
 try:asyncio.run(run(pathlib.Path(sys.argv[1]).resolve() if len(sys.argv)>1 else R,int(sys.argv[2]) if len(sys.argv)>2 else 8811))
 finally:(D/('ui-'+(sys.argv[2] if len(sys.argv)>2 else '8811')+'.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
