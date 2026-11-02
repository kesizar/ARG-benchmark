from pathlib import Path
import asyncio,hashlib,json,subprocess,sys,tempfile,zipfile,urllib.request
from playwright.async_api import async_playwright
R=Path(__file__).resolve().parents[1];A=R/'tasks/huicheng-317/audit';ID='huicheng-317'
async def main():
    old=json.loads((A/'independent-delivery.json').read_text(encoding='utf-8'));evidence=[]
    async with async_playwright() as pw:
      b=await pw.chromium.launch(channel='msedge',headless=True)
      for item in old:
        kind=item['kind'];port=item['port'];archive=R/'packs'/f'{ID}.{kind}.zip';dest=Path(tempfile.mkdtemp(prefix=f'{ID}-final-{kind}-'));prev=Path(item['extraction'])
        with zipfile.ZipFile(archive) as z:z.extractall(dest)
        changed=[];added=[]
        for f in dest.rglob('*'):
          if f.is_file():
            rel=f.relative_to(dest);p=prev/rel
            if not p.exists():added.append(rel.as_posix())
            elif p.read_bytes()!=f.read_bytes():changed.append(rel.as_posix())
        allowed={f'judge/{ID}/checkpoint-spec.json','BUNDLE-MANIFEST.json'}
        assert set(changed)<=allowed and set(added)<={f'judge/{ID}/verify_sample.py'}
        if kind=='prepared':
          reg=subprocess.run([sys.executable,str(dest/'judge'/ID/'verify_sample.py')],cwd=dest,capture_output=True,text=True);assert reg.returncode==0,reg.stderr
        web=dest if kind=='resources' else dest/'tasks'/ID/'mirror';server=subprocess.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1','--directory',str(web)],cwd=dest,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
          for _ in range(100):
            try:
              with urllib.request.urlopen(f'http://127.0.0.1:{port}/index.html',timeout=1) as r:assert r.status==200
              break
            except Exception:await asyncio.sleep(.1)
          ctx=await b.new_context();p=await ctx.new_page();await p.goto(f'http://127.0.0.1:{port}/index.html');assert await p.title()=='317 · 回程 —— 中枢站';assert await p.locator('#boot').is_visible();assert await p.evaluate('localStorage.length')==0;await ctx.close()
          evidence.append(dict(kind=kind,final_archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),final_extraction=str(dest),changed_files=changed,added_files=added,game_config_judge_runtime_byte_identical=True,full_ui_evidence_reused_from='independent-delivery.json',fresh_context_launch_passed=True,independent_judge_regression_passed=kind=='prepared'))
        finally:server.terminate()
      await b.close()
    (A/'final-package-equivalence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8');print('final bundle equivalence and smoke passed')
asyncio.run(main())
