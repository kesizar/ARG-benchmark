import urllib.request,urllib.parse,pathlib,json
q=urllib.parse.urlencode({'search_type':'video','keyword':'邮轮连环杀人事件','page':1})
u='https://api.bilibili.com/x/web-interface/search/type?'+q
r=pathlib.Path('judge/youlun-xia/recovery')
try:
 with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.bilibili.com/'}),timeout=25) as x:b=x.read()
 (r/'prequel-search.body').write_bytes(b);print(b[:120].decode('utf-8','replace').encode('ascii','backslashreplace').decode())
except Exception as e:(r/'prequel-search-error.txt').write_text(str(e),encoding='utf-8');print(str(e))
