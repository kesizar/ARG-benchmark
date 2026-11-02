import json, threading, os
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from playwright.sync_api import sync_playwright

root=Path(os.environ.get('TYPEHELP_ROOT','data/preparation/type-help-0017'))
port=int(os.environ.get('TYPEHELP_PORT','8851'))
graph=json.loads(Path('data/preparation/type-help-0017/scene-graph.json').read_text(encoding='utf8'))
judge=json.loads(Path(os.environ.get('TYPEHELP_JUDGE','judge/type-help-william-rous-0017/judge.json')).read_text(encoding='utf8'))
spec=json.loads(Path(os.environ.get('TYPEHELP_SPEC','judge/type-help-william-rous-0017/checkpoint-spec.json')).read_text(encoding='utf8'))
scored=set(spec['critical_candidates'].values())
names=sorted(x['name'] for x in graph['scene_data'] if x['name'] not in ['00-dream','00-final-note','00-readme'])
server=ThreadingHTTPServer(('127.0.0.1',port),partial(SimpleHTTPRequestHandler,directory=str(root)))
threading.Thread(target=server.serve_forever,daemon=True).start()
out={'source_assisted':True,'port':port,'steps':[],'errors':[],'external_requests':[]}
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe')
    context=browser.new_context(); page=context.new_page()
    def intercept(route):
        if not route.request.url.startswith(f'http://127.0.0.1:{port}/'):
            out['external_requests'].append(route.request.url); route.abort()
        else: route.continue_()
    page.route('**/*',intercept); page.on('pageerror',lambda e:out['errors'].append(str(e)))
    page.goto(f'http://127.0.0.1:{port}/'+os.environ.get('TYPEHELP_FILE','original.html'),wait_until='networkidle'); page.get_by_role('link',name='(Skip intro)').click()
    def state(): return page.evaluate('({passage:SugarCube.State.passage,cache:SugarCube.State.variables.cache,complete:SugarCube.State.variables.is_complete,finalMessage:SugarCube.State.variables.final_message_viewed})')
    def command(s):
        f=page.locator('input[type=text]'); f.fill(s); f.press('Enter'); page.wait_for_timeout(50)
        return state()
    def scores():
        return page.evaluate('(exprs) => exprs.map(e => !!eval(e))',[h['expr'] for h in judge['hooks'].values()])
    out['initial_hook_values']=scores()
    command('99-NO-999'); out['invalid_hook_values']=scores()
    for n in names:
        st=command(n); vals=scores(); expected=sum(x in scored for x in st['cache'])
        out['steps'].append({'command':n,'present':n in st['cache'],'count':len(st['cache']),'scored_count':sum(vals[:len(scored)]),'expected_scored_count':expected})
    out['all_hook_values']=scores(); out['before_list']=state(); out['after_list']=command('list')
    command('inbox'); page.get_by_role('link',name='Final',exact=True).click(); page.wait_for_timeout(200)
    out['final_message']=state(); out['final_note']=command('00-final-note'); out['ending']=command('help')
    page.wait_for_timeout(4000); out['ending_text']=page.locator('#passages').inner_text(); out['ending_hook_values']=scores()
    context.close(); context=browser.new_context(); page=context.new_page(); page.goto(f'http://127.0.0.1:{port}/'+os.environ.get('TYPEHELP_FILE','original.html')); page.wait_for_timeout(500)
    out['reset_state']=state(); browser.close()
server.shutdown()
out['all_scenes_added']=all(x['present'] for x in out['steps'])
out['all_incremental_scores_match']=all(x['scored_count']==x['expected_scored_count'] for x in out['steps'])
Path(os.environ.get('TYPEHELP_OUTPUT','data/preparation/type-help-0017/full-ui.json')).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'port':port,'all_scenes_added':out['all_scenes_added'],'incremental_match':out['all_incremental_scores_match'],'initial_scored':sum(out['initial_hook_values'][:len(scored)]),'invalid_scored':sum(out['invalid_hook_values'][:len(scored)]),'final_scored':sum(out['all_hook_values'][:len(scored)]),'ending_hook':out['ending_hook_values'][-2],'complete_hook':out['ending_hook_values'][-1],'reset':out['reset_state'],'errors':out['errors'],'external_requests':out['external_requests']}))
