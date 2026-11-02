"""Normal local browser UI smoke test using native video keyboard seeking.
Not a claim of full audiovisual playback or original-player equivalence.
"""
import asyncio,json,pathlib,threading,collections,sys
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
from playwright.async_api import async_playwright
from evaluate import evaluate,GRAPH
from serve import Handler
ROOT=pathlib.Path(__file__).resolve().parents[2]
def path_to(cid):
    queue=collections.deque([(1,[])]);seen=set()
    while queue:
        edge,path=queue.popleft()
        if edge in seen:continue
        seen.add(edge)
        if GRAPH[edge]['leaf'] and GRAPH[edge]['cid']==cid:return path
        for q in GRAPH[edge]['questions']:
            for c in q['choices']:queue.append((c['id'],path+[c['option']]))
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
async def main():
    port=int(sys.argv[1]) if len(sys.argv)>1 else 8821
    game_root=pathlib.Path(sys.argv[2]).resolve() if len(sys.argv)>2 else ROOT/'tasks/youlun-xia'
    server=ThreadingHTTPServer(('127.0.0.1',port),partial(Handler,directory=str(game_root)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    results=[]
    try:
      async with async_playwright() as p:
        browser=await p.chromium.launch(channel='msedge',headless=True)
        context=await browser.new_context(viewport={'width':1280,'height':900})
        page=await context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        await page.goto(f'http://127.0.0.1:{port}/index.html')
        async def finish_segment():
            v=page.locator('video');await v.wait_for();await page.wait_for_function('(()=>{const v=document.querySelector("video");return v.readyState>=2 && v.seekable.length && v.seekable.end(v.seekable.length-1)>=v.duration-.1})()')
            await page.get_by_role('slider',name='本段进度').focus();await page.keyboard.press('Home');await page.keyboard.press('End')
            try:await page.wait_for_function('document.querySelectorAll("#choices button").length>0 || window.__youlunState?.events.some(e=>e.type==="leaf" && e.edge===window.__youlunState.edge)',timeout=5000)
            except Exception:
                print(await page.evaluate('({state:window.__youlunState, slider:document.querySelector("#seek").value, active:document.activeElement.outerHTML,video:{time:document.querySelector("video").currentTime,duration:document.querySelector("video").duration,paused:document.querySelector("video").paused,error:document.querySelector("video").error?.message}})'),flush=True)
                await page.screenshot(path=str(ROOT/'judge/youlun-xia/recovery/local-debug.png'))
                # Keyboard End is native media-control seek; Space starts a paused segment.
                await page.get_by_role('slider',name='本段进度').focus();await page.keyboard.press('Home');await page.keyboard.press('End')
                await page.wait_for_function('document.querySelectorAll("#choices button").length>0 || window.__youlunState?.events.some(e=>e.type==="leaf" && e.edge===window.__youlunState.edge)',timeout=5000)
        for cid in [142802675,142802702,142802705,142802726,142803151,142813414]:
            await page.get_by_role('button',name='重新开始',exact=True).click()
            initial=await page.evaluate('window.__youlunState');assert evaluate(initial)['score']==0
            route=path_to(cid)
            for option in route:
                await finish_segment();await page.get_by_role('button',name=option,exact=True).click()
            await finish_segment()
            state=await page.evaluate('window.__youlunState');verdict=evaluate(state)
            assert verdict['terminal_cid']==cid and verdict['score']==int(cid==142813414),verdict
            await page.screenshot(path=str(ROOT/f'judge/youlun-xia/recovery/ui-{cid}.png'))
            results.append({'cid':cid,'route':route,'state':state,'verdict':verdict})
        await page.get_by_role('button',name='重新开始',exact=True).click()
        reset=await page.evaluate('window.__youlunState');assert reset['edge']==1 and len(reset['events'])==1 and evaluate(reset)['score']==0
        out={'port':port,'browser':browser.version,'runs':results,'reset':reset,'errors':errors,'method':'visible progress slider Home/End keys and visible choice/reset clicks; no evaluate writes','scope':'six terminal-video sample routes, not all edges; local adaptation only'}
        (ROOT/'judge/youlun-xia/recovery/local-ui.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
        await browser.close();print({'runs':len(results),'reset':True,'errors':errors})
    finally:server.shutdown()
asyncio.run(main())
