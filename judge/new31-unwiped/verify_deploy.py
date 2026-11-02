from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from threading import Thread
from functools import partial
from playwright.sync_api import sync_playwright
from pathlib import Path
import json
root=Path('tasks/new31-unwiped/deploy/resource').resolve(); srv=ThreadingHTTPServer(('127.0.0.1',8953),partial(SimpleHTTPRequestHandler,directory=str(root))); Thread(target=srv.serve_forever,daemon=True).start()
try:
 with sync_playwright() as pw:
  b=pw.chromium.launch(headless=True,executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe'); page=b.new_page(); page.route('https://**/*',lambda r:r.abort()); page.goto('http://127.0.0.1:8953/index.html'); assert page.title()=='UNWIPED'; page.get_by_role('button',name='Start',exact=True).click(); assert page.get_by_text('click to skip').is_visible(); b.close()
 Path('judge/new31-unwiped/verification/deploy-smoke.json').write_text(json.dumps({'resource_port':8953,'resource':'independent unpack loaded and Start opened intro; HTTPS blocked','evaluation_port':8952,'evaluation':'independent unpack run_one script give_up exited 0','limitations':'not full flows on extracted packages'},indent=2),encoding='utf-8'); print('resource smoke passed')
finally: srv.shutdown(); srv.server_close()
