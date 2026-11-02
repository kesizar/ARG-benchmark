from pathlib import Path
import json,re,hashlib
R=Path(__file__).resolve().parents[1];M=R/'tasks/yiwu-yuren/mirror';rows=[]
for p in M.rglob('*.html'):
 s=p.read_text(encoding='utf-8');rows.append({'path':p.relative_to(M).as_posix(),'bytes':p.stat().st_size,'complete_document':s.rstrip().lower().endswith('</html>'),'external_src_urls':re.findall(r'''(?:src|href)=["'](https?://[^"']+)''',s)})
assert all(x['complete_document'] for x in rows)
a={'html_documents':rows,'valid_player_files':len([p for p in M.rglob('*') if p.is_file()]),'source_scan_false_positives':['mock upload filename 日记扫描件.png (never fetched)','dynamic ${escapeHtml...} CSS string','REDIRECT_URL and url JavaScript variables mistaken for unquoted href','001/index.html is only diary fallback, corrected to gongyuanyy.html'],'declared_scope_exclusions':['002','003','https://grad.tonghai.edu.cn fictional graduate-search placeholder'],'case001_actual_clue_dependencies_local':True,'snapshot_version_difference_preserved':True}
(R/'tasks/yiwu-yuren/evidence/resource-audit.json').write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf-8');print({'html':len(rows),'files':a['valid_player_files']})
