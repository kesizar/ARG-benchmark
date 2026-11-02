from pathlib import Path
import zipfile,json,hashlib
root=Path('.').resolve();base=root/'runs/guiyihui-meimei-final-routes';dest=base/'evaluation';dest.mkdir(parents=True,exist_ok=True)
bundle=root/'packs/guiyihui-meimei.prepared.zip'
with zipfile.ZipFile(bundle) as z:
 for info in z.infolist():assert (dest/info.filename).resolve().is_relative_to(dest)
 z.extractall(dest)
m=json.loads((dest/'BUNDLE-MANIFEST.json').read_text(encoding='utf-8'));assert all(hashlib.sha256((dest/x['path']).read_bytes()).hexdigest()==x['sha256'] for x in m['files']);(dest/'judge/guiyihui-meimei/verification').mkdir(exist_ok=True)
s=(root/'scripts/guiyihui-meimei-route-review.py').read_text(encoding='utf-8');start=s.index('  with zipfile.ZipFile(');end=s.index('  async with async_playwright()',start);s=s[:start]+"  log['game_manifest_verified']=True\n"+s[end:];s=s.replace("log['A_debug']={'score':score,'values':j.values,'prev_values':j.prev_values}; assert not score['ending_reached'] and score['ending_tier'] is None;assert any(e['id']=='failure_timeout_A' for e in score['events'])", "assert not score['ending_reached'] and score['ending_tier'] is None and score['failure_reached'] and score['failure_id']=='failure_timeout_A'");(base/'verify-routes.py').write_text(s,encoding='utf-8');(base/'bundle-sha256.txt').write_text(hashlib.sha256(bundle.read_bytes()).hexdigest(),encoding='ascii');print(dest)
