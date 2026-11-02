"""0365 snapshot audit. Source inspection is evaluator-only, never a model policy."""
from pathlib import Path
import asyncio, hashlib, json, re, subprocess, sys, time, zipfile

ROOT=Path(__file__).resolve().parents[1]
TASK=ROOT/'tasks/anyu-bainian'
OUT=ROOT/'runs/anyu-bainian'

def dump(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def prepare():
    raw=(TASK/'original/index.html').read_text(encoding='utf-8')
    # Keep the snapshot byte-for-byte; missing images and font are explicit conditions.
    (TASK/'mirror/index.html').write_bytes((TASK/'original/index.html').read_bytes())
    dependencies=['assets/cover.jpg']+[f'assets/ch{i}.jpg' for i in range(1,6)]
    dump(TASK/'provenance.json',{'record_id':'base664:0365','task_id':'anyu-bainian',
        'source_url':'https://3c724bb558b34cd9a8b198ca51198cb6.app.workbuddy.host/',
        'snapshot':'ARG-packs/verify-416/bodies/365.html','snapshot_bytes':len(raw.encode()),
        'snapshot_sha256':hashlib.sha256((TASK/'original/index.html').read_bytes()).hexdigest(),
        'changes':[], 'missing_assets':[p for p in dependencies if not (TASK/'mirror'/p).is_file()],
        'external_font':'https://miaoda.feishu.cn/fonts/css2?family=Noto+Serif+SC:wght@400;600;700;900&family=Noto+Sans+SC:wght@300;400;500;700&display=swap',
        'account_requirement':'none in snapshot; live service not verified',
        'readiness':'recovery_only_not_accepted'})
    hooks={f'p{i}':{'type':'localstorage','key':'yanyu_arg_save_v1','mode':'json_path','path':f'solved.{i}'} for i in range(1,31)}
    for code,label in [('A','回声'),('B','传承'),('C','散播')]:
        hooks[code]={'type':'js_truthy','expr':f"document.querySelector('#overlay.show .ending-card h2')?.textContent === '结局 {code} · {label}' && JSON.parse(localStorage.getItem('yanyu_arg_save_v1')||'{{}}').ending === '{code}'"}
    judge={'hooks':hooks,'checkpoints':[{'id':f'p{i}','hook':f'p{i}','op':'truthy','role':'optional'} for i in range(1,29)]+[{'id':'p30','hook':'p30','op':'truthy','role':'optional'}],
        'events':{},'routes':[{'id':code,'tier':'normal','gates':[],'ending':{'hook':code,'op':'truthy'}} for code in ['A','B','C']],
        'ending':None,'answer_sha256':[],'answer_hash_file':None,'request_milestones':[],'submit_conclusion':{'enabled':False,'schema':None},'rubric_path':None}
    dump(ROOT/'judge/anyu-bainian/candidate-judge.json',judge)
    spec={'status':'audit_candidate_not_formal_scoring','route_gates':[],
          'reason':'Original UI homeSearch numeric/keyword routing bypasses all puzzle pages. p29 writes ending without checking solved. No puzzle is mandatory across reachable routes.',
          'endings':{'A':'公开档案 / 回声','B':'封存传承 / 传承','C':'散入噪声 / 散播'},
          'tiers':'normal: source provides three choices without authoritative good/bad ranking',
          'puzzles':list(range(1,29)), 'side_branch':'30 hidden dossier, go(30) sets solved on visit; not a reasoning gate',
          'failure':'Wrong answers generally feedback and retry, no terminal failure found. Some feedback claims retry limits/timers which code does not enforce.',
          'reset_risk':'restart clears S; several globals are restored by page.after. p13.after lacks an unsolved reset. New browser context is authoritative reset; full reset coverage pending.',
          'legacy_judge':'Four transient DOM checkpoint messages were erroneously declared mandatory for all three endings; original retained and not promoted.'}
    dump(ROOT/'judge/anyu-bainian/checkpoint-spec.json',spec)

async def ui(game_root=None,port=8831,out=OUT):
    from playwright.async_api import async_playwright
    server=subprocess.Popen([sys.executable,str(ROOT/'scripts/serve_static.py'),'--root',str(game_root or TASK/'mirror'),'--port',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    result={'scope':'diagnostic normal UI only; not full puzzle acceptance','actions':[],'missing_requests':[]}
    try:
        await asyncio.sleep(.6)
        async with async_playwright() as pw:
            browser=await pw.chromium.launch(channel='msedge')
            context=await browser.new_context(viewport={'width':1366,'height':900})
            base=f'http://127.0.0.1:{port}/'
            await context.route('**/*',lambda r:r.continue_() if r.request.url.startswith(base) else r.abort())
            page=await context.new_page()
            page.on('response',lambda r:result['missing_requests'].append({'url':r.url,'status':r.status}) if r.status>=400 else None)
            async def state():return await page.evaluate("JSON.parse(localStorage.getItem('yanyu_arg_save_v1')||'{}')")
            sys.path.insert(0,str(ROOT))
            from harness.judge import Judge
            class ReadOnly:
                async def local_storage(self,*args):return await page.evaluate('Object.fromEntries(Object.entries(localStorage))')
                async def page_expr(self,expr):return await page.evaluate(expr)
            async def score():
                j=Judge(json.loads((ROOT/'judge/anyu-bainian/candidate-judge.json').read_text(encoding='utf-8')),'anyu-bainian',ROOT)
                await j.read(ReadOnly());j.update(1);return j.score()
            async def click(sel):await page.locator(sel).click(); await page.wait_for_timeout(60)
            async def search(q):
                await page.locator('#homeSearch').fill(q)
                await click('[data-action="homeSearch"]')
            async def home():await click('[data-action="go"][data-page="0"]')
            await page.goto(base+'index.html')
            await click('[data-action="cover"][data-v="start"]')
            await search('3') # numeric is displayed page number minus one
            await page.locator('#pwd').fill('WRONG')
            await click('[data-action="p2"]')
            assert not (await state())['solved']
            assert not (await score())['ending_reached'] and not (await score())['diagnostic']
            result['actions'].append({'case':'wrong_p2','state':await state(),'feedback':await page.locator('#feed2').inner_text()})
            await home(); await search('2')
            await click('[data-action="p1"][data-v="box"]')
            assert not (await state())['solved']
            for v in ['lamp','pc','box']:await click(f'[data-action="p1"][data-v="{v}"]')
            assert (await state())['solved']=={'1':True}
            assert (await score())['diagnostic']=={'p1':1}
            result['actions'].append({'case':'p1_positive_sequence','state':await state()})
            for code in ['A','B','C']:
                await home();await search('传话')
                await click(f'[data-action="p29"][data-v="{code}"]')
                s=await state()
                assert s['ending']==code
                assert set(s['solved']).issubset({'1'})
                scored=await score()
                assert scored['route_id']==code and scored['ending_tier']=='normal' and scored['checkpoints_total']==0
                await page.screenshot(path=str(out/f'shortcut-ending-{code}.png'),full_page=True)
                result['actions'].append({'case':'ending_'+code+'_via_normal_search','state':s,'title':await page.locator('.ending-card h2').inner_text(),'judge':scored})
                await click('[data-action="restart"]')
                assert (await state())['solved']=={} and (await state())['ending'] is None
            await search('2')
            result['actions'].append({'case':'restart_p1','state':await state(),'opened_tin_visible':await page.locator('.tin-stage.open').count()})
            assert await page.locator('.tin-stage.open').count()==0
            await page.screenshot(path=str(out/'restart-p1.png'),full_page=True)
            await context.close()
            context=await browser.new_context()
            page=await context.new_page()
            await context.route('**/*',lambda r:r.continue_() if r.request.url.startswith(base) else r.abort())
            await page.goto(base+'index.html')
            assert await page.evaluate("localStorage.getItem('yanyu_arg_save_v1')") is None
            result['fresh_context_reset']=True
            await browser.close()
    finally:
        server.terminate();server.wait(timeout=10)
        dump(out/'ui-diagnostics.json',result)

if __name__=='__main__':
    prepare()
    asyncio.run(ui())
