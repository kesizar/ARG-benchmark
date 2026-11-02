"""Extra source-level BBS branch check via real local UI, no real message sending."""
import asyncio,json
import verify_sample as v
async def main():
 v.OUT.mkdir(parents=True,exist_ok=True);c=v.cfg_for('day');s=v.LocalServer();h=v.BrowserHarness(c,v.OUT);report={'deployment_root':str(v.R),'kind':'local_simulated_bbs_branch_audit','state_injection':False,'results':[]}
 try:
  s.start(c,v.R,v.OUT/'bbs-server.log');await h.start();await h.reset();b=v.Audit(h);await h.page.wait_for_timeout(1800);await b.cmd('www');await b.click('#webBody a[onclick="webGo(\'bbs\')"]')
  for text,expected in [('???','只能輸入'),('否','太晚了'),('是','你現在是K7-007'),('maybe','你現在是K7-007')]:
   await b.type('#bbsReply',text);await b.click('#webBody [onclick="bbsSubmit()"]');await h.page.wait_for_timeout(450);dialogs=b.last_dialogs or h.dialogs_step();assert dialogs and dialogs[-1]['type']=='alert'
   message=dialogs[-1]['message'];normalized=''.join(message.split());assert expected in normalized,(text,message)
   await b.record({'op':'auto_accepted_alert','input':text});assert not b.j.ending_reached and not b.j.checkpoints and not b.j.side
   report['results'].append({'input':text,'message':message,'ending':False})
  assert not h.blocked;report['pass']=True
 finally:
  (v.OUT/'bbs-acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();s.stop()
 print('K7 BBS BRANCHES PASS',flush=True)
if __name__=='__main__':asyncio.run(main())
