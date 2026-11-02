import asyncio,json,sys,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R));from harness.browser_harness import BrowserHarness
from harness.judge import Judge
E=R/'judge/qingmiao-zhongxue/verification';T='qingmiao-zhongxue'
async def main():
 c=json.loads((R/'configs'/f'{T}.json').read_text(encoding='utf8'));c['entry_url']=c['entry_url'].replace('8811','8812');c['allow_hosts']=['127.0.0.1:8812'];h=BrowserHarness(c,E);rows=[];log=(E/'bypass-server.log').open('w');proc=subprocess.Popen([sys.executable,str(R/'scripts/serve_static.py'),'--root',str(R/'tasks'/T/'mirror'),'--port','8812'],stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 try:
  await asyncio.sleep(1);await h.start()
  for phrase,ident,element in [('期待我们下次见面','gentle','typewriterEndTypedText'),('食人族如何补充膳食纤维？','harsh','animationEndTypedText')]:
   await h.reset();await h.page.locator('.start-game-btn').click();await asyncio.sleep(.5);h.page=h.context.pages[-1];await h.page.bring_to_front();await h.page.wait_for_load_state();await h.page.locator('#closeEmailBtn').click();await h.page.wait_for_timeout(1800);j=Judge.load(R/c['judge_path'],T,R);await h.page.locator('#messageInput').fill(phrase);await h.page.locator('#sendButton').click();await h.page.wait_for_function('(id)=>document.getElementById(id)?.textContent==="END"',arg=element,timeout=120000);await j.read(h);j.update(1);s=j.score();assert s['ending_reached'] and s['route_id']==ident and not s['diagnostic'] and s['ending_tier']=='normal' and not s['good_ending'];await h.page.screenshot(path=str(E/(ident+'-fresh-bypass.png')));rows.append({'phrase':phrase,'score':s,'history':await h.page.evaluate('conversationHistory')})
  await h.reset();j=Judge.load(R/c['judge_path'],T,R);await j.read(h);j.update(0);assert not j.score()['diagnostic'] and not j.score()['ending_reached'];rows.append({'label':'final-reset','score':j.score()})
  out={'pass':True,'rows':rows,'conclusion':'Both authored END animations reachable from fresh start without any accepted puzzle response; both conservatively normal with good_ending=false; final fresh reset is empty.'}
 except Exception as ex:
  import traceback;out={'pass':False,'error':repr(ex),'traceback':traceback.format_exc(),'rows':rows}
 finally:await h.close();proc.terminate();proc.wait();log.close()
 (E/'both-ending-bypass.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in out.items() if k!='rows'},ensure_ascii=False))
asyncio.run(main())
