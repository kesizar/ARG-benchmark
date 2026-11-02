from pathlib import Path
import json,hashlib,difflib
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1];d=root/'tasks/xishe-guaitan';u='https://cdn.jsdelivr.net/npm/pinyin-pro@3.25.0/dist/index.js'
with sync_playwright() as p:
 b=p.chromium.launch(channel='msedge',headless=True);page=b.new_page();r=page.goto(u);data=r.body();assert r.status==200
 (d/'mirror/vendor').mkdir(exist_ok=True);(d/'mirror/vendor/pinyin-pro-3.25.0.js').write_bytes(data);b.close()
f=d/'mirror/village-committee.html';orig=f.read_text(encoding='utf-8');(d/'originals').mkdir(exist_ok=True);(d/'originals/village-committee.html').write_bytes(f.read_bytes());new=orig.replace(u,'vendor/pinyin-pro-3.25.0.js');f.write_text(new,encoding='utf-8');(d/'compatibility.diff').write_text(''.join(difflib.unified_diff(orig.splitlines(True),new.splitlines(True),fromfile='original',tofile='localized')),encoding='utf-8')
(d/'vendor-provenance.json').write_text(json.dumps({'url':u,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'change':'Only script URL localized; logic unchanged'},indent=2),encoding='utf-8')
