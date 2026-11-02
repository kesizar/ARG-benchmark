"""Private deterministic source-audit planner; returns UI clicks, never mutates browser state.

LCG is the configured harness RNG. Rendering particle RNG consumption is included.
The verifier compares every predicted board with the live DOM before clicking.
"""
import random
BASE='木人口日火水土又一';SECOND='林从吕昌炎沝圭双二';THIRD='森众品晶焱淼垚叒三';NEXT=dict(zip(BASE+SECOND,SECOND+THIRD))
def rnd(s):s=(1664525*s+1013904223)&0xffffffff;return s,s/4294967296
def advance(s,n):
 for _ in range(n):s,_=rnd(s)
 return s
def groups(b):
 todo=set(range(36));out=[]
 while todo:
  n=min(todo);todo.remove(n);g=[n];stack=[n]
  while stack:
   n=stack.pop();r,c=divmod(n,6)
   for rr,cc in [(r+1,c),(r-1,c),(r,c+1),(r,c-1)]:
    i=rr*6+cc
    if 0<=rr<6 and 0<=cc<6 and i in todo and b[i]==b[n]:todo.remove(i);g.append(i);stack.append(i)
  if len(g)>=2:out.append(g)
 return out
def ensure(b,s):
 if groups(b):return b,s
 s,x=rnd(s);r=int(x*6);s,x=rnd(s);c=int(x*5);s,x=rnd(s);ch=BASE[int(x*9)];b[r*6+c]=ch;b[r*6+c+1]=ch;return b,s
def step(board,s,g,n):
 b=list(board);ch=b[n];high=ch not in BASE
 if high:s=advance(s,72)
 for i in g:b[i]=None
 if ch in NEXT:b[n]=NEXT[ch]
 for c in range(6):
  stack=[b[r*6+c] for r in range(5,-1,-1) if b[r*6+c]]
  for r in range(5,-1,-1):
   if stack:b[r*6+c]=stack.pop(0)
   else:s,x=rnd(s);b[r*6+c]=BASE[int(x*9)]
 b,s=ensure(b,s)
 if high:s=advance(s,54)
 return tuple(b),s
def infer(board,seed):
 s=seed
 for offset in range(3000):
  state=s;guess=[]
  for _ in range(36):state,x=rnd(state);guess.append(BASE[int(x*9)])
  guess,state=ensure(guess,state)
  if guess==board:return state,offset
  s,_=rnd(s)
 raise AssertionError('Unable to align initial visible board with configured RNG')
def plan(board,seed,width=500,goal='practice'):
 state,offset=infer(board,seed);beam=[(tuple(board),state,[],0)];rng=random.Random(seed)
 for depth in range(40):
  candidates=[];dedup=set()
  for b,s,path,clears in beam:
   for g in groups(b):
    for n in g:
     nb,ns=step(b,s,g,n);ident=(nb,ns)
     if ident in dedup:continue
     dedup.add(ident);nc=clears+(b[n] in THIRD);newpath=path+[(n,list(nb))]
     triples=sum(ch in THIRD for ch in nb);seconds=sum(ch in SECOND for ch in nb)
     # Keep a variety of routes. Near the end strictly minimize surviving triples.
     adjacency=sum(1 for gg in groups(nb) if nb[gg[0]] in THIRD)
     future=triples*3-adjacency*5-seconds*.025-nc*1.5 if goal=='practice' else triples*.1-adjacency*10-nc*20-seconds*.02
     if depth<32:future+=rng.random()*3
     candidates.append((future,nb,ns,newpath,nc))
  if depth==39:
   valid=[x for x in candidates if (not any(ch in THIRD for ch in x[1])) if goal=='practice'] if goal=='practice' else [x for x in candidates if x[4]>0 and any(ch in THIRD for ch in x[1])]
   if valid:
    best=min(valid,key=lambda x:x[0]);return {'offset':offset,'width':width,'path':best[3],'clears':best[4]}
  candidates.sort(key=lambda x:x[0]);beam=[(b,s,path,clear) for _,b,s,path,clear in candidates[:width]]
 raise AssertionError('No 40-move plan in beam for '+goal)
