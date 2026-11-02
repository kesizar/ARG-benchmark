"""Private deterministic original-rule planning, UI replay verifies every event."""
def rand(s):s=(1664525*s+1013904223)&0xffffffff;return s,s/4294967296
def hunt_order(seed):
 s=seed
 for _ in range(130):
  for _ in range(3):s,_=rand(s)
  s,v=rand(s)
  if v>=.12:s,_=rand(s)
 pool=list(range(24));order=[]
 for _ in range(10):s,v=rand(s);order.append(pool.pop(int(v*len(pool))))
 return order

def effect(state,fx):
 c,l,e,r=state
 return tuple(max(-9 if k=='e' else 0,min(12,x+fx.get(k,0))) for k,x in zip(['c','l','e','r'],[c,l,e,r]))
def ending(s):
 c,l,e,r=s
 return 'burnout' if e<=0 else 'best' if c>=9 and l>=9 and r>=9 else 'great' if c+l+r>=24 else 'normal' if c+l+r>=15 else 'flop'
def hunt_paths(events,order):
 states={(5,5,8,5):[]};found={}
 for day,ei in enumerate(order):
  nxt={}
  for state,path in states.items():
   for ci,ch in enumerate(events[ei]['c']):
    ns=effect(state,ch[1]);np=path+[ci]
    if ns[2]<=0 or day==9:found.setdefault(ending(ns),np)
    else:nxt.setdefault(ns,np)
  states=nxt
 return found
