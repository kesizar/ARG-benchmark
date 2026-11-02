"""Auditor-only normal UI acceptance. No model/API call or game-state mutation."""
from pathlib import Path
import argparse, asyncio, json, sys

P=argparse.ArgumentParser();P.add_argument('--root',default=str(Path(__file__).resolve().parents[2]));P.add_argument('--port',type=int,default=8821);P.add_argument('--out',required=True);P.add_argument('--game-root');a=P.parse_args()
ROOT=Path(a.root).resolve();sys.path.insert(0,str(ROOT))
from harness.browser_harness import BrowserHarness
from harness.judge import Judge
from harness.serve_local import LocalServer

async def main():
    out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
    cfg=json.loads((ROOT/'configs/disan-zhongxue.json').read_text('utf-8'))
    url=f'http://127.0.0.1:{a.port}/index.html';cfg.update(entry_url=url,allow_hosts=[f'127.0.0.1:{a.port}'])
    game=a.game_root or 'tasks/disan-zhongxue/mirror'
    cfg['local_serve'].update(command=[sys.executable,str(ROOT/'scripts/serve_static.py'),'--root',game,'--port',str(a.port)],ready_url=url,port=a.port)
    server=LocalServer();h=BrowserHarness(cfg,out,headless=True);events=[];errors=[]
    server.start(cfg,ROOT,out/'server.log')
    assert server.owned, 'Test needs a fresh server it owns'
    step=0;j=None
    async def sample(label):
        nonlocal step
        step+=1;await j.read(h);j.update(step);s=j.score();events.append({'label':label,'state':s,'visible':(await h.page.locator('body').inner_text())[:600]});return s
    async def fresh():
        nonlocal j
        await h.reset();j=Judge.load(ROOT/'judge/disan-zhongxue/judge.json','disan-zhongxue',ROOT)
        h.page.on('pageerror',lambda e:errors.append(str(e)))
        s=await sample('fresh');assert not s['ending_reached'] and not s['diagnostic']
    async def search(k):
        await h.page.locator('#searchInput').fill(k);await h.page.get_by_role('button',name='检索',exact=True).click();return await sample('search:'+k)
    async def gate():
        assert not await h.page.locator('#endPanel').is_visible()
        await h.page.locator('#resultPage').hover()
        for _ in range(6):
            await h.page.mouse.wheel(0,650);await h.page.wait_for_timeout(60)
        assert await h.page.locator('#endPanel').is_visible()
        s=await sample('bottom_unlocked');assert not s['ending_reached'] and s['checkpoints_reached']==0
    try:
        await h.start();await fresh()
        for label,heading in [('学生档案查询','学生档案查询'),('留言板','师生留言板'),('旧日记碎片','旧日记碎片'),('首页公告','校园公告')]:
            await h.page.get_by_role('link',name=label,exact=True).click();assert await h.page.get_by_role('heading',name=heading,exact=True).is_visible();assert not (await sample('navigation:'+label))['ending_reached']
        for k in ('不存在','删除','5月3'):
            s=await search(k);assert not s['diagnostic'] and not s['ending_reached'];assert await h.page.get_by_text('未检索到相关校内文档',exact=True).is_visible()
        await h.page.locator('#searchInput').fill('删除日志');await h.page.locator('#searchInput').press('Enter');assert not (await sample('Enter_has_no_handler'))['diagnostic']
        keys=list(json.loads((ROOT/'judge/disan-zhongxue/checkpoint-spec.json').read_text('utf-8'))['diagnostic_lookup_keys'])
        for n,k in enumerate(keys,1):
            s=await search(k);assert len(s['diagnostic'])==n;assert s['checkpoints_reached']==0 and not s['ending_reached']
            assert (await h.page.locator('#readCount').inner_text())==str(n)
        await gate();await h.page.screenshot(path=str(out/'all-documents-unlocked.png'),full_page=True)
        await h.page.get_by_role('button',name='结局A：全部上报',exact=True).click();s=await sample('full_route_truth');assert s['route_id']=='truth' and s['ending_tier']=='normal'
        await h.page.get_by_role('button',name='关闭归档',exact=True).click();await j.read(h);assert not j.values['truth']
        await h.page.get_by_role('link',name='重置系统',exact=True).click();assert (await h.page.locator('#readCount').inner_text())=='0';assert not await h.page.locator('#fullEndPage').is_visible();assert not await h.page.locator('#endPanel').is_visible();await j.read(h);assert not any(j.values.values());events.append({'label':'reset_hides_stale_dom','hook_values':j.values,'episode_latches_retained':j.score()})
        # Each ending is reachable with only the final document, even at count 1/25.
        for ident,label in [('truth','结局A：全部上报'),('silence','结局B：掩盖封存'),('shard','结局C：只留存碎片')]:
            await fresh();s=await search('  删除日志  ');assert len(s['diagnostic'])==1;await gate()
            await h.page.get_by_role('button',name=label,exact=True).click();s=await sample('minimal_route:'+ident);assert s['ending_reached'] and s['route_id']==ident and s['checkpoints_total']==0
            await h.page.screenshot(path=str(out/(ident+'.png')),full_page=True)
            await h.page.get_by_role('button',name='关闭归档',exact=True).click();await j.read(h);assert not any(j.values[x] for x in ('truth','silence','shard'))
        await fresh();await search('磁盘残留');await search('磁盘残留');assert (await h.page.locator('#readCount').inner_text())=='1'
        await h.page.get_by_role('link',name='重置系统',exact=True).click();await j.read(h);assert not any(j.values.values());await fresh()
        assert not errors,errors;assert not h.blocked,h.blocked
        result={'passed':True,'root':str(ROOT),'game_root':str(game),'port':a.port,'fresh_server_owned':server.owned,'browser':h.browser.version,'normal_ui_actions_only':True,'model_api_used':False,'all_lookup_documents':25,'formal_endings':3,'reasoning_gates':0,'shortest_ending_lookup_count':1,'reset_game_ui':True,'fresh_context_and_judge_reset':True,'wrong_and_partial_keywords_no_score':True,'runtime_errors':errors,'blocked_requests':h.blocked,'requests':h.all_requests,'events':events}
        (out/'acceptance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8');print(json.dumps({k:v for k,v in result.items() if k not in ('events','requests')},ensure_ascii=False))
    finally:
        await h.close();server.stop()

asyncio.run(main())
