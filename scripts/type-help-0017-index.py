import re, json, html, hashlib
from pathlib import Path

p = Path('data/preparation/type-help-0017')
raw = (p/'original.html').read_bytes()
s = raw.decode('utf-8')
passages = []
for m in re.finditer(r'<tw-passagedata\b([^>]*)>(.*?)</tw-passagedata>', s, re.S):
    attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', m.group(1)))
    body = html.unescape(m.group(2))
    passages.append({'pid':attrs.get('pid'), 'name':html.unescape(attrs.get('name','')), 'tags':attrs.get('tags',''), 'links':re.findall(r'\[\[([^\]]+)\]\]', body), 'macros':re.findall(r'<<(?:if|elseif|set|goto|link|textbox|button)\b[^>]*>>', body), 'body':body})
index = {'sha256':hashlib.sha256(raw).hexdigest(), 'bytes':len(raw), 'passage_count':len(passages), 'storydata':re.findall(r'<tw-storydata\b[^>]*>',s), 'external_scripts':re.findall(r'<script[^>]+src=[^>]+>',s), 'passages':passages}
(p/'source-index.json').write_text(json.dumps(index, ensure_ascii=False, indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in index.items() if k != 'passages'},ensure_ascii=False,indent=2))
print('end candidates:', [x['name'] for x in passages if re.search(r'end|death|win|lose|fail|game over',x['name'],re.I)])
