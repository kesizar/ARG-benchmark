"""All local graph transitions through visible controls; no playback/content audit claim."""
import asyncio, collections, functools, hashlib, json, pathlib, threading, time
from http.server import ThreadingHTTPServer
from playwright.async_api import async_playwright
from serve import Handler
from evaluate import evaluate

ROOT = pathlib.Path(__file__).resolve().parents[2]
GAME = ROOT / 'tasks/youlun-xia'
OUT = ROOT / 'judge/youlun-xia/recovery/all-graph-ui.json'
G = {int(k): v for k, v in json.loads((GAME/'graph.json').read_text(encoding='utf-8')).items()}
def options(node):
    return [c for q in G[node]['questions'] for c in q['choices']]

async def main():
    server = ThreadingHTTPServer(('127.0.0.1',8822),functools.partial(Handler,directory=str(GAME)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    pending = {(n,i) for n in G for i,c in enumerate(options(n))}
    leaves = {n for n in G if not options(n)}
    result = {'method':'visible slider Home/End, choice buttons and reset only; state reads only',
      'scope':'local adaptation all nodes/arcs; seeks do not establish audiovisual review or original-runtime equivalence',
      'graph_sha256':hashlib.sha256((GAME/'graph.json').read_bytes()).hexdigest(),
      'nodes':{},'transitions':[],'terminals':[],'resets':0,'errors':[],'complete':False}
    def save():
        result['remaining_arcs']=len(pending);result['remaining_leaves']=sorted(leaves)
        OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    def path(start, targets):
        queue=collections.deque([(start,[])]);seen=set()
        while queue:
            n,p=queue.popleft()
            if n in seen: continue
            seen.add(n)
            if n in targets:return p
            for i,c in enumerate(options(n)):queue.append((c['id'],p+[(n,i)]))
        return None
    try:
      async with async_playwright() as p:
        browser=await p.chromium.launch(channel='msedge',headless=True)
        result['browser']=browser.version
        context=await browser.new_context(viewport={'width':1280,'height':900})
        page=await context.new_page()
        page.on('pageerror',lambda e:result['errors'].append(str(e)))
        await page.goto('http://127.0.0.1:8822/index.html')
        current=1;finished=False
        async def finish():
            nonlocal finished
            if finished:return
            await page.wait_for_function('(()=>{const v=document.querySelector("video");return v.readyState>=2&&v.seekable.length&&v.seekable.end(v.seekable.length-1)>=v.duration-.1})()')
            state=await page.evaluate('({edge:window.__youlunState.edge,src:document.querySelector("video").currentSrc,duration:document.querySelector("video").duration})')
            assert state['edge']==current and state['src'].endswith(f"/{G[current]['cid']}.mp4"),state
            await page.get_by_role('slider',name='本段进度').focus()
            await page.keyboard.press('Home');await page.keyboard.press('End')
            await page.wait_for_function('document.querySelectorAll("#choices button").length>0||window.__youlunState.events.some(e=>e.type==="leaf"&&e.edge===window.__youlunState.edge)')
            labels=await page.locator('#choices button').all_text_contents()
            assert labels==[c['option'] for c in options(current)],(current,labels)
            result['nodes'][str(current)]={'cid':G[current]['cid'],'labels':labels,'duration':state['duration']}
            if current in leaves:
                s=await page.evaluate('window.__youlunState');v=evaluate(s)
                assert v['valid'] and v['complete'],v
                result['terminals'].append({'edge':current,'verdict':v,'state':s});leaves.remove(current)
            finished=True
        while pending or leaves:
            await finish()
            own=sorted(i for n,i in pending if n==current)
            if own: route=[(current,own[0])]
            else:
                targets={n for n,i in pending}|leaves
                direct=path(current,targets);restart=path(1,targets)
                if direct is None or (restart is not None and len(restart)+1<len(direct)):
                    await page.get_by_role('button',name='重新开始',exact=True).click()
                    current=1;finished=False;result['resets']+=1
                    s=await page.evaluate('window.__youlunState')
                    assert s['edge']==1 and len(s['events'])==1 and evaluate(s)['score']==0
                    route=restart
                else:route=direct
            assert route is not None
            for n,i in route:
                assert current==n
                await finish();c=options(n)[i]
                await page.locator('#choices button').nth(i).click()
                s=await page.evaluate('window.__youlunState')
                assert s['edge']==c['id'] and evaluate(s)['valid'],(n,i,s)
                result['transitions'].append({'from':n,'index':i,'to':c['id'],'option':c['option'],'event':s['events'][-2]})
                pending.discard((n,i));current=c['id'];finished=False
            if len(result['transitions'])%20==0:save();print({'arcs_left':len(pending),'nodes':len(result['nodes'])},flush=True)
        await finish()
        await page.get_by_role('button',name='重新开始',exact=True).click()
        result['final_reset']=await page.evaluate('window.__youlunState')
        assert evaluate(result['final_reset'])['score']==0
        assert len(result['nodes'])==161 and not result['errors']
        result['complete']=True;save();await browser.close()
        print({'complete':True,'nodes':len(result['nodes']),'unique_arcs':394,'UI_transitions':len(result['transitions']),'leaves':len(result['terminals'])},flush=True)
    except Exception as e:
        result['failure']=repr(e);save();raise
    finally:server.shutdown()

if __name__=='__main__':asyncio.run(main())
