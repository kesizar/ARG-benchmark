from pathlib import Path
import re,json,hashlib,difflib
R=Path(__file__).resolve().parents[1];T=R/'tasks/guangying-she';M=T/'mirror';M.mkdir(exist_ok=True)
s=(T/'document-2.html').read_text(encoding='utf8')
t=re.sub(r'<link\b[^>]*>', '', s)
t=re.sub(r'<script\b[^>]*\bsrc="[^"]+"[^>]*>\s*</script>', '', t)
(M/'index.html').write_text(t,encoding='utf8')
(T/'localization.diff').write_text(''.join(difflib.unified_diff(s.splitlines(True),t.splitlines(True),fromfile='original',tofile='local')),encoding='utf8')
print(json.dumps({'original_bytes':len(s.encode()),'local_bytes':len(t.encode()),'patches':'remove external fonts, favicon links and Cloudflare analytics only','remote_urls':list(set(re.findall(r'https?://[^\s<>\"\x27]+',t)))},ensure_ascii=True))
