import json
import threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
from pathlib import Path
from playwright.sync_api import sync_playwright

out = {'url':'http://127.0.0.1:8851/original.html','external_requests':[], 'errors':[]}
judge=json.loads(Path('judge/type-help-william-rous-0017/judge.json').read_text(encoding='utf8'))
server = ThreadingHTTPServer(('127.0.0.1',8851),partial(SimpleHTTPRequestHandler,directory='data/preparation/type-help-0017'))
threading.Thread(target=server.serve_forever, daemon=True).start()
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe')
    context = browser.new_context()
    page = context.new_page()
    def route(r):
        if not r.request.url.startswith('http://127.0.0.1:8851/'):
            out['external_requests'].append(r.request.url)
            r.abort()
        else: r.continue_()
    page.route('**/*', route)
    page.on('pageerror', lambda e: out['errors'].append(str(e)))
    page.goto(out['url'], wait_until='networkidle', timeout=30000)
    page.wait_for_timeout(2000)
    out['initial'] = page.locator('body').inner_text()[:3000]
    out['initial_links'] = page.locator('a').all_text_contents()
    page.get_by_role('link', name='(Skip intro)').click()
    page.wait_for_timeout(2000)
    out['after_skip'] = page.locator('body').inner_text()[:3000]
    out['inputs'] = page.locator('input').count()
    def command(s):
        field=page.locator('input[type=text]')
        field.fill(s); field.press('Enter'); page.wait_for_timeout(300)
        return {'text':page.locator('#passages').inner_text()[:3500], 'state':page.evaluate('({passage: SugarCube.State.passage, cache: SugarCube.State.variables.cache, complete: SugarCube.State.variables.is_complete, previous: SugarCube.State.variables.previous_scene})'), 'hooks':dict(zip(judge['hooks'],page.evaluate('(xs)=>xs.map(x=>!!eval(x))',[v['expr'] for v in judge['hooks'].values()]))) }
    out['invalid'] = command('99-NO-999')
    out['readme'] = command('00-readme')
    out['scene'] = command('26-EN-1')
    out['dream'] = command('00-dream')
    for letter in 'abcdefghijkl': out['hangman_last'] = command('hangman '+letter)
    out['after_hangman'] = command('list')
    out['shortcut_final_note'] = command('00-final-note')
    out['shortcut_end'] = command('help')
    context.close()
    context=browser.new_context()
    page=context.new_page(); page.goto(out['url'],wait_until='domcontentloaded'); page.wait_for_timeout(1000)
    out['fresh_context'] = page.locator('#passages').inner_text()[:1500]
    browser.close()
Path('data/preparation/type-help-0017/smoke.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
server.shutdown()
print(json.dumps(out,ensure_ascii=True,indent=2))
