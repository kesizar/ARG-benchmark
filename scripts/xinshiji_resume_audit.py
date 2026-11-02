"""Read-only recovery audit. Does not certify browser completion."""
import functools, hashlib, http.server, json, threading, urllib.request, zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / 'judge/xinshiji/recovery'
sha = lambda b: hashlib.sha256(b).hexdigest()
prov = json.loads((root/'tasks/xinshiji/provenance.json').read_text('utf8'))
files = prov['files']
report = {'record_id':'base664:0315','original_files':len(files),'file_mismatches':[], 'archives':[], 'http_deployments':[], 'prepared':False}
for item in files:
    for folder in ['original','mirror']:
        p = root/'tasks/xinshiji'/folder/item['path']
        if not p.exists() or sha(p.read_bytes()) != item['sha256']:
            report['file_mismatches'].append(str(p))
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
for kind, port in [('resources',8822),('evaluation',8823)]:
    archive = root/f'packs/xinshiji.{kind}.partial.zip'
    base = root/f'runs/xinshiji-independent/{kind}'
    with zipfile.ZipFile(archive) as z:
        bad = z.testzip()
        mismatch = [n for n in z.namelist() if not n.endswith('/') and (not (base/n).exists() or sha((base/n).read_bytes()) != sha(z.read(n)))]
    report['archives'].append({'path':archive.relative_to(root).as_posix(),'sha256':sha(archive.read_bytes()),'crc_error':bad,'extraction_mismatches':mismatch})
    webroot = base if kind == 'resources' else base/'tasks/xinshiji/mirror'
    server = http.server.ThreadingHTTPServer(('127.0.0.1',port),functools.partial(Quiet,directory=str(webroot)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    failures=[]
    for item in files:
        try:
            data = opener.open(f'http://127.0.0.1:{port}/'+item['path'],timeout=5).read()
            assert sha(data)==item['sha256']
        except Exception as e:
            failures.append({'path':item['path'],'error':repr(e)})
            break  # transport failure is not a reason to repeat all 91 requests
    try:
        opener.open(f'http://127.0.0.1:{port}/judge/xinshiji/judge.json',timeout=5)
        judge_exposed=True
    except urllib.error.HTTPError as e: judge_exposed=e.code!=404
    except Exception as e: judge_exposed='unverified: '+repr(e)
    server.shutdown();server.server_close()
    report['http_deployments'].append({'kind':kind,'port':port,'files_tested':len(files) if not failures else 1,'failures':failures,'judge_exposed':judge_exposed,'browser_ui':'blocked: Edge localhost ERR_CONNECTION_TIMED_OUT; HTTP-only is not UI evidence'})
(out/'resume-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=True))
