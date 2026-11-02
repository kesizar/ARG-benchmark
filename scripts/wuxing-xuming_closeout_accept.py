from pathlib import Path
import json,sys,os,subprocess,time
from playwright.sync_api import sync_playwright
R=Path(os.environ.get('WUXING_ROOT',str(Path(__file__).resolve().parents[1])));M=Path(os.environ.get('WUXING_MIRROR',str(R/'tasks/wuxing-xuming/mirror')));A=Path(os.environ.get('WUXING_OUT',str(R/'runs/wuxing-xuming/acceptance')));A.mkdir(parents=True,exist_ok=True);PORT=os.environ.get('WUXING_PORT','8831');sys.path.insert(0,str(R));from harness.judge import Judge
J=R/'judge/wuxing-xuming/judge.json';log=[];errors=[]
def main():
 server=subprocess.Popen([sys.executable,str(R/'scripts/serve_static.py'),'--root',str(M),'--port',PORT],cwd=R,stdout=open(A/'server.log','w'),stderr=subprocess.STDOUT)
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(channel='msedge',headless=True,timeout=15000);ctx=browser.new_context(viewport={'width':1366,'height':900},service_workers='block');ctx.route('**/*',lambda r:r.continue_() if r.request.url.startswith('http://127.0.0.1:'+PORT+'/') else r.abort());p=ctx.new_page();p.set_default_timeout(7000);p.on('pageerror',lambda e:errors.append(str(e)));j=Judge.load(J,'wuxing-xuming',R)
   def snap(label,expect=None):
    j.values={k:p.evaluate(v['expr']) for k,v in j.cfg['hooks'].items()};j.update(len(log));row={'label':label,'url':p.url,'hooks':j.values.copy(),'score':j.score(),'body':p.locator('body').inner_text()};log.append(row);(A/'ui-trace.json').write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf8')
    if expect is not None:
     for k,v in expect.items():assert bool(j.values[k])==v,(label,k,j.values[k],v)
   def hit(selector,x,y):
    q=p.locator(selector);q.scroll_into_view_if_needed();b=q.bounding_box();p.mouse.click(b['x']+b['width']*x/100,b['y']+b['height']*y/100)
   def act2(branch,negative=False):
    if negative:
     p.locator('#flawBtn').click();snap('flaw_empty',{'flaw':False});p.locator('#quizFlaw input[value="4"]').check();p.locator('#flawBtn').click();snap('flaw_wrong',{'flaw':False});p.locator('#quizFlaw input[value="4"]').uncheck()
    for n in [1,2,3]:p.locator(f'#quizFlaw input[value="{n}"]').check()
    p.locator('#flawBtn').click();snap('flaw_'+branch,{'flaw':True})
    for key in ['script','filter','invite','pull']:p.locator('.studio-card[onclick*="'+key+'"]').click()
    p.locator('[onclick="revealDrawer()"]').click()
    if negative:
     for value in ['','14']:
      p.locator('#drawerPwd').fill(value);p.locator('[onclick="unlockDrawer()"]').click();snap('drawer_negative_'+value,{'drawer':False})
     p.locator('#drawerPwd').fill('15');snap('drawer_unsubmitted',{'drawer':False})
    p.locator('#drawerPwd').fill('15');p.locator('[onclick="unlockDrawer()"]').click();snap('drawer_'+branch,{'drawer':True});p.locator('#br'+branch).click();p.locator('#finishBtn').click();snap('branch_'+branch,{'ending-'+branch:True});p.screenshot(path=str(A/('branch-'+branch+'.png')))
   try:
    p.goto('http://127.0.0.1:'+PORT+'/');snap('fresh',{k:False for k in j.cfg['hooks']});p.locator('#caseCard').click();p.locator('[onclick="closeApply()"]').click();snap('cancel_apply');p.locator('#caseCard').click();p.locator('[onclick="confirmApply()"]').click();p.locator('[onclick="enterInvest()"]').click();hit('#sceneWrap',3,3);snap('mark_miss',{'mark':False})
    coords=[(49.7,30.9),(20.5,43.1),(75.1,39.6),(56.6,62.7),(38.4,62.7)]
    for x,y in coords:hit('#sceneWrap',x,y)
    snap('mark_positive',{'mark':True});p.locator('[onclick="resetMarks()"]').click();snap('mark_reset',{'mark':False})
    for x,y in coords:hit('#sceneWrap',x,y)
    p.locator('#act1Next').click();p.locator('#quizStep .opt[data-ans="0"]').click();snap('step_wrong',{'step':False});p.locator('#quizStep .opt[data-ans="1"]').click();snap('step_correct',{'step':True})
    for key in ['red','censer','water','slip']:
     p.locator('.ec[data-evi="'+key+'"]').click();p.locator('#eviAdd').click();p.locator('[onclick="closeEvi()"]').click()
    p.locator('#buttEvi').click();p.locator('#vhsPlayBtn').click();p.locator('#vhsStepBtn').wait_for(state='visible');p.wait_for_timeout(16000);p.locator('#vhsStepBtn').click();hit('#cuffWrap',90,10);snap('cuff_miss',{'cuff':False});hit('#cuffWrap',16,80);p.wait_for_timeout(1300);snap('cuff_hit',{'cuff':True});p.locator('#vhsBackBtn').click();p.locator('#act2Next').click();p.wait_for_timeout(11000);p.locator('#toAct2').click();p.wait_for_url('**/act2.html');act2('A',True)
    p.reload();snap('act2_reload_clears',{'flaw':False,'drawer':False,'ending-A':False,'ending-B':False});act2('B');p.locator('#toAct3').click();p.wait_for_url('**/act3.html')
    for i in range(5):p.locator('#fn'+str(i)).click()
    p.wait_for_timeout(700);snap('funds',{'funds':True});p.locator('[onclick="openFPModal()"]').click()
    for i in range(3):p.locator('.fp-tgt[data-idx="'+str(i)+'"]').click();p.wait_for_timeout(1500)
    p.locator('.fp-tgt[data-idx="0"]').click();snap('fingerprint_wrong',{'fingerprint':False});p.locator('.fp-tgt[data-idx="2"]').click();snap('fingerprint_correct',{'fingerprint':True});p.wait_for_timeout(3600)
    p.locator('.frag[data-k="juankuan"]').click();snap('timeline_wrong',{'timeline-1':False})
    for i,key in enumerate(['shaixuan','weiyi','konghe','butan','toudu','guizheng','juankuan']):
     bad='juankuan' if i<6 else 'shaixuan';hit('.frag[data-k="'+bad+'"]',50,50);snap('timeline_negative_'+str(i+1),{'timeline-'+str(i+1):False});p.locator('.frag[data-k="'+key+'"]').click();snap('timeline_'+str(i+1),{'timeline-'+str(i+1):True})
    p.locator('.cw-next').click();p.wait_for_url('**/act4.html');p.locator('#finaleBtn').click();snap('finale_locked',{'ending-final':False});p.locator('#fleePool [data-correct="false"]').first.click();snap('alias_wrong',{'alias':False});p.locator('#fleePool [data-correct="true"]').click();snap('alias_correct',{'alias':True});p.wait_for_timeout(11000)
    p.locator('.js-piece[data-idx="0"]').click();p.locator('.js-slot[data-slot="1"]').click();snap('network_wrong',{'network-1':False,'network-2':False})
    for i in range(5):
     p.locator('.js-piece[data-idx="'+str(i)+'"]').click();p.locator('.js-slot[data-slot="'+str((i+1)%5)+'"]').click();snap('network_negative_'+str(i+1),{'network-'+str(i+1):False});p.locator('.js-slot[data-slot="'+str(i)+'"]').click();snap('network_'+str(i+1),{'network-'+str(i+1):True})
    p.wait_for_timeout(1200);p.locator('#finaleBtn').click();snap('finale',{'ending-final':True});assert len(j.checkpoints)==3;p.screenshot(path=str(A/'finale.png'))
    p.locator('.fn-replay').click();snap('finale_replay',{'ending-final':True});p.locator('.fn-restart').click();p.wait_for_url('**/index.html');p.wait_for_timeout(1100);p.locator('.ncp-no').click();snap('new_case_dismissed');p.reload();j=Judge.load(J,'wuxing-xuming',R);snap('fresh_judge_after_return',{k:False for k in j.cfg['hooks']});assert not j.checkpoints
    # Browser Back + reload, only jigsaw: prove finale does not require alias or prior acts.
    p.go_back();p.reload();j=Judge.load(J,'wuxing-xuming',R)
    for i in range(5):p.locator('.js-piece[data-idx="'+str(i)+'"]').click();p.locator('.js-slot[data-slot="'+str(i)+'"]').click()
    p.wait_for_timeout(1200);p.locator('#finaleBtn').click();snap('finale_without_alias_or_prior_acts',{'ending-final':True,'alias':False});assert len(j.checkpoints)==0
    p.locator('.fn-restart').click();p.wait_for_url('**/index.html');p.wait_for_timeout(1100);p.locator('.ncp-yes').click();p.wait_for_timeout(2400);snap('new_case_accepted');assert p.evaluate("localStorage.getItem('lin_gang_act4_cleared')") is None
    # Fresh context resets all game state and independent judge.

    ctx.close();ctx=browser.new_context();p=ctx.new_page();p.goto('http://127.0.0.1:'+PORT+'/');j=Judge.load(J,'wuxing-xuming',R);snap('new_context_reset',{k:False for k in j.cfg['hooks']});browser.close();(A/'acceptance.json').write_text(json.dumps({'passed':True,'browser':browser.version,'stages':len(log),'checkpoints':3,'page_errors':errors,'scope':'four-act main case; both interim narrative branches; negative controls; local marker reset; reload and fresh context reset; full main-final route'},ensure_ascii=False,indent=2),encoding='utf8');print('PASS',len(log))
   except Exception:
    snap('ERROR');p.screenshot(path=str(A/'error.png'));raise
 finally:server.terminate();server.wait(timeout=10)
if __name__=='__main__':main()
