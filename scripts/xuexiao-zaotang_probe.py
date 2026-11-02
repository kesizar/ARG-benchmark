from pathlib import Path
import httpx,json,time
R=Path(__file__).resolve().parents[1];base='https://0e59bf37df9e4a9c9abb460520042af7.app.workbuddy.link/'
rows=[]
for p in ['index.html','profile.html','start.html']:
 t=time.time()
 try:
  r=httpx.get(base+p,timeout=18,follow_redirects=True,verify=False)
  rows.append({'path':p,'status':r.status_code,'bytes':len(r.content),'url':str(r.url)})
  if r.status_code==200:(R/'tasks/xuexiao-zaotang/evidence'/('live-'+p)).write_bytes(r.content)
 except Exception as e:rows.append({'path':p,'error':type(e).__name__+': '+str(e)})
 rows[-1]['elapsed_s']=round(time.time()-t,2)
(R/'tasks/xuexiao-zaotang/evidence/live-probe.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print(json.dumps(rows))
