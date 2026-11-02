import urllib.request,pathlib
u='https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=ZCOOL+KuaiLe&family=Noto+Serif+SC:wght@400;700&display=swap'
r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=30)
b=r.read(); pathlib.Path('judge/guiyihui-meimei/font.css').write_bytes(b); print(r.status,len(b))
