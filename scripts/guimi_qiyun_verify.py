from pathlib import Path
import json,sys,threading,functools,http.server,hashlib,subprocess,random,copy
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];T=R/'tasks/guimi-qiyun';O=R/'runs/guimi-qiyun';O.mkdir(exist_ok=True)
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def server(root,port):
 class Quiet(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*a):pass
 s=http.server.ThreadingHTTPServer(('127.0.0.1',port),functools.partial(Quiet,directory=str(root)));threading.Thread(target=s.serve_forever,daemon=True).start();return s
def main():
 print('start',flush=True)
 srv=server(T/'mirror',8831); traces=[];errors=[]
 print('server-ready',flush=True)
 with sync_playwright() as pw:
  print('playwright-ready',flush=True)
  b=pw.chromium.launch(channel='msedge',headless=True);c=b.new_context(viewport={'width':1366,'height':900});p=c.new_page();p.goto('http://127.0.0.1:8831/');p.on('pageerror',lambda e:errors.append(str(e)))
  data=p.evaluate('({chapters:CHS,logs:LOGS,replies:WX_REPLIES,messages:WX_BY_CH,mail:MAIL_BY_CH})');write(T/'audit/content-map.json',data)
  # Read-only source upper bound, allowing all mutually exclusive chapter choices to take their best contribution separately.
  bounds={v:sum(max([0]+[(op.get('r',{}).get('view',{}).get(v,0)) for op in ch.get('opts',[])]) for ch in data['chapters'])+sum(max([0]+[op.get('r',{}).get('view',{}).get(v,0) for op in reps]) for reps in data['replies'].values()) for v in ['boss','lead','col','bf','fam']}
  write(T/'audit/reachability.json',{'optimistic_view_upper_bounds':bounds,'perfect_requires':'4 viewpoints >=60','impossible':'bf and fam maxima below60, so <=3 qualifying people; perfect and nested egg unreachable without modifying game','method':'sum each chapter maximum positive contribution + each reply maximum; ignores penalties/preconditions, so optimistic upper bound','other_mutation_sites':'applyResult is only view writer; initial/reset view empty; verified source functions'})
  cfg=json.loads((R/'judge/guimi-qiyun/judge.json').read_text(encoding='utf-8'))
  def hooks():return {k:p.evaluate(h['expr']) for k,h in cfg['hooks'].items()}
  assert not any(hooks().values())
  def collect():
   for el in p.locator('#chapterArea .clue[data-e]').all():el.click()
   p.locator('button[onclick="openLog()"]').click()
   while p.locator('#paneLog .compare-btn').count():p.locator('#paneLog .compare-btn').first.click()
   p.locator('#paneLog .ph-x').click()
   p.locator('button[onclick="openMail()"]').click()
   for el in p.locator('#paneMail .attach-btn:enabled').all():el.click()
   p.locator('#paneMail .ph-x').click()
   p.locator('button[onclick="openWx()"]').click()
   for i in range(p.locator('#wxList .wx-chat').count()):
    p.locator('#wxList .wx-chat').nth(i).click()
    while p.locator('#paneWxChat .extract').count():p.locator('#paneWxChat .extract').first.click()
    # Both mutually exclusive replies covered in separate full episodes.
    while p.locator('#paneWxChat .reply-btn').count():
     row=p.locator('#paneWxChat .reply-row').first;row.locator('.reply-btn').nth(min(reply_index,row.locator('.reply-btn').count()-1)).click()
    p.locator('#paneWxChat .ph-x').click()
   p.locator('#paneWx .ph-x').click()
  def run(name,seq,investigate,reply=0):
   nonlocal reply_index
   reply_index=reply;p.reload();assert p.locator('#tEv').inner_text()=='0';assert not any(hooks().values());p.locator('#btnStart').click();steps=[]
   for i,ch in enumerate(data['chapters']):
    if investigate:collect()
    before=p.evaluate('JSON.parse(JSON.stringify(S))');opts=ch.get('opts',[]);idx=min(seq[i],len(opts)-1)
    if opts:
     label=p.locator('#chapterArea .opt').nth(idx).inner_text();p.locator('#chapterArea .opt').nth(idx).click();face=p.locator('.face-box').inner_text();after=p.evaluate('JSON.parse(JSON.stringify(S))')
     steps.append({'chapter':i+1,'choice':idx,'label':label,'before':before,'after':after,'face':face})
     assert not any(hooks().values());p.locator('#chapterArea button[onclick="nextChapter()"]').click()
    else:p.locator('#btnNext').click()
   h=hooks();assert sum(h[k] for k in ['perfect','clean','bitter','both','killed'])==1
   title=p.locator('#endTitle').inner_text();p.screenshot(path=str(O/(name+'.png')),full_page=True);traces.append({'episode':name,'investigate':investigate,'reply_index':reply,'steps':steps,'ending':title,'hooks':h,'state':p.evaluate('JSON.parse(JSON.stringify(S))')})
   return title
  reply_index=0
  for investigate in [False,True]:
   for index in range(3):run(('collect' if investigate else 'bare')+'-'+str(index),[index]*30,investigate,index%2)
  # Find intermediate endings by visible action schedules, not by injecting state.
  seen={t['ending'] for t in traces}
  for n in [3,6,10,14,18,22]:
   if any('鱼死网破' in x for x in seen) and any('被反杀' in x for x in seen) and any('惨胜' in x for x in seen):break
   seq=[0 if i<n else 2 for i in range(30)];seen.add(run('mixed-'+str(n),seq,False))
  p.reload();p.locator('#btnStart').click();p.locator('#chapterArea .opt').first.click();assert '代价' in p.locator('.face-box').inner_text();assert p.locator('#tEv').inner_text()=='0';p.screenshot(path=str(O/'missing-evidence-failure.png'),full_page=True)
  # AP bypass demonstrated through ordinary toolbar, no function calls.
  p.reload();p.locator('#btnStart').click();ap=p.evaluate('S.ap');p.locator('#pbLog').click();p.locator('#paneLog .ph-x').click();assert p.evaluate('S.ap')==ap-1;p.locator('button[onclick="openLog()"]').click();p.locator('#paneLog .ph-x').click();assert p.evaluate('S.ap')==ap-1
  p.reload();assert p.evaluate('S.ch===0 && S.evid.length===0 && S.holes.length===0 && !S.done');assert not any(hooks().values());p.screenshot(path=str(O/'refresh-reset.png'))
  c.close();c=b.new_context();p=c.new_page();p.goto('http://127.0.0.1:8831/');assert p.evaluate('S.ch===0 && S.evid.length===0 && S.alert===20 && !S.done');c.close();b.close()
 srv.shutdown();write(O/'ui-evidence.json',{'method':'normal Playwright locator clicks only; read-only evaluator state snapshots; no game writes, no direct game function calls; source schedules only engineering regression, no independent-solving claim','episodes':traces,'pageerrors':errors,'reset':'refresh and fresh context checked','AP':'probe spends one; toolbar accesses same pane free','paid_api_calls':0})
 print(json.dumps({'view_bounds':bounds,'episodes':len(traces),'endings':sorted({t['ending'] for t in traces}),'errors':errors},ensure_ascii=True))
if __name__=='__main__':main()
