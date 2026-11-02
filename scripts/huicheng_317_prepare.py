from pathlib import Path
import hashlib,json,re,urllib.request
R=Path(__file__).resolve().parents[1]; T=R/'tasks/huicheng-317'; A=T/'audit'; M=T/'mirror'
s=(A/'original.html').read_text(encoding='utf-8')
urls=re.findall(r'https://media\.doubao\.com/[^\s\'"<>]+',s)
report=[]
for i,u in enumerate(dict.fromkeys(urls)):
    try:
        with urllib.request.urlopen(u,timeout=35) as r: b=r.read(); status=r.status; typ=r.headers.get('Content-Type')
        f=f'asset-{i}.jpg'; (M/f).write_bytes(b); s=s.replace(u,f)
        report.append(dict(url=u,status=status,content_type=typ,bytes=len(b),file=f,sha256=hashlib.sha256(b).hexdigest()))
    except Exception as e:report.append(dict(url=u,error=str(e)))
(A/'resource-probe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
if any('error' in x for x in report): raise SystemExit(2)
# Remove publisher chrome, SDK, tracking, restrictive remote CSP and cosmetic webfont.
s=re.sub(r'<body>.*?<div class="bg-scene">','<body>\n<div class="bg-scene">',s,flags=re.S)
s=re.sub(r'<script src="https://html2.link/page-sdk.js".*?</script>','',s)
s=re.sub(r'<meta http-equiv="Content-Security-Policy"[^>]*>','',s)
s=re.sub(r'<link rel="icon" type="image/svg\+xml"[^>]*>','',s)
s=re.sub(r'<link rel="stylesheet" href="https://miaoda.feishu.cn/[^>]*>','',s)
(M/'index.html').write_text(s,encoding='utf-8')
import difflib
(A/'localization.diff').write_text(''.join(difflib.unified_diff((A/'original.html').read_text(encoding='utf-8').splitlines(True),s.splitlines(True),fromfile='original.html',tofile='mirror/index.html')),encoding='utf-8')
c=json.loads((R/'configs/huicheng-317.json').read_text(encoding='utf-8')); (A/'original-config.json').write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf-8')
c.update(runtime_layer='L1',entry_url='http://127.0.0.1:8821/index.html',allow_hosts=['127.0.0.1:8821'],account_requirement='none')
c['local_serve']=dict(enabled=True,command=['python','scripts/serve_static.py','--root','tasks/huicheng-317/mirror','--port','8821'],cwd='.',ready_url=c['entry_url'],ready_timeout_s=30,port=8821)
c['notes_for_report']=['Original narrative and game JavaScript unchanged. Cosmetic online font uses installed fallback; publisher chrome/telemetry removed. A/B/D narrative endings normal; C breaks the cycle; no model solvability claim.']
(R/'configs/huicheng-317.json').write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf-8')
