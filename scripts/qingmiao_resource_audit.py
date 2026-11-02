from pathlib import Path
import json,hashlib,re,urllib.parse
R=Path(__file__).resolve().parents[1];T=R/'tasks/qingmiao-zhongxue';P=json.loads((T/'evidence/resource-probe.json').read_text(encoding='utf8'));M=json.loads((T/'provenance.json').read_text(encoding='utf8'));bad=[];missing=[];external=[];refs=[]
for f in M['files']:
 p=T/'mirror'/f['path']
 if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=f['sha256']:bad.append(f['path'])
for p in (T/'mirror').rglob('*'):
 if p.is_file() and p.suffix in ['.html','.css','.js']:
  text=p.read_text(encoding='utf8')
  for row in re.findall(r'''(?:src|href)\s*=\s*["']([^"'<>]+)["']|url\(["']?([^\)"']+)|["']((?:images/)[^\s"'<>]+)["']''',text):
   ref=next(x for x in row if x).strip()
   if ref.startswith(('data:','javascript:','#','mailto:')) or '${' in ref or ref=='$1':continue
   if ref.startswith(('https:','http:')):external.append({'file':str(p.relative_to(T)),'ref':ref});continue
   resolved=T/'mirror'/ref.lstrip('/') if ref.startswith('/') else p.parent/ref
   resolved=Path(urllib.parse.unquote(str(resolved).split('?')[0].split('#')[0]));resolved=resolved/'index.html' if resolved.is_dir() else resolved;refs.append(str(resolved))
   if not resolved.is_file():missing.append({'file':str(p.relative_to(T)),'ref':ref})
out={'pass':not bad and not missing,'probe_resource_count':len(P['resources']),'original_probe_failures':{k:v for k,v in P['resources'].items() if 'error' in v},'failure_resolution':'Original avatar typo images/tx.png=label corrected to original existing images/tx.png. See localization.diff.','unfetched':P['unfetched_candidates'],'mirror_files':len(M['files']),'hash_mismatch':bad,'checked_references':len(refs),'missing_references':missing,'external_literal_references':external,'fallback_scope':'Original blog placeholder.com error-handler and chat Unsplash unmapped-user-.jpg fallback are not story materials. Normal story images resolve locally. Runtime host policy blocks external fallback requests.'}
(T/'evidence/resource-closure.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in out.items() if k not in ['external_literal_references','original_probe_failures']},ensure_ascii=False))
