"""Private receding-horizon planning of currently rendered-equivalent surf objects."""
def choose_y(st):
 ys=[46+i*10 for i in range(35)];dt=.12;start=min(range(len(ys)),key=lambda i:abs(ys[i]-st['y']));states={start:(0,[])}
 for step in range(1,20):
  t=step*dt;nxt={}
  for j,y in enumerate(ys):
   cost=0
   if t>st['inv']:
    for o in st['obs']:
     x=o['x']-o['sp']*t
     if abs(x-130)<34 and abs(y-o['y'])<38:cost+=1500+(38-abs(y-o['y']))*10
   for l in st['lts']:
    x=l['x']-l['sp']*t
    if abs(x-130)<25 and abs(y-l['y'])<23:cost-=150
   best=None
   for i,(old,path) in states.items():
    if abs(ys[i]-y)<=36:
     value=old+cost+abs(ys[i]-y)*.08
     if best is None or value<best[0]:best=(value,path+[j])
   if best is not None:nxt[j]=best
  states=nxt
 best=min(states.values(),key=lambda x:x[0]);return ys[best[1][0]]
