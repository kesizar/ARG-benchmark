"""Normal UI acceptance; evaluator observes storage, never alters game state."""
from pathlib import Path
import sys,json,asyncio,os,traceback,re
from playwright.async_api import async_playwright
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from harness.judge import Judge
O=R/'runs/guangying-she';O.mkdir(parents=True,exist_ok=True); URL=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8812/index.html';LABEL=sys.argv[2] if len(sys.argv)>2 else 'acceptance'
ORDER=['点灯之前','千灯齐明','人潮初起','灯谜长廊','河灯缓缓','鱼龙灯舞','压轴烟花','熄灯之后']
class Adapter:
 def __init__(self,p):self.p=p
 async def page_expr(self,e):return await self.p.evaluate(e)
async def main():
 events=[];errors=[];requests=[];result={'url':URL,'label':LABEL,'events':events,'errors':errors,'external_requests':requests,'paid_api_calls':0}
 def save(): (O/(LABEL+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
 try:
  async with async_playwright() as pw:
   b=await pw.chromium.launch(channel='msedge',headless=True);c=await b.new_context(viewport={'width':1366,'height':900});p=await c.new_page();p.on('pageerror',lambda e:errors.append(str(e)));p.on('dialog',lambda d:asyncio.create_task(d.accept()));p.on('request',lambda r:requests.append(r.url) if not r.url.startswith(URL.split('/index')[0]) else None)
   j=Judge.load(R/'judge/guangying-she/judge.json','guangying-she',R)
   async def record(label,shot=False):
    await p.wait_for_timeout(90);await j.read(Adapter(p));j.update(len(events)+1);state=await p.evaluate('JSON.parse(localStorage.getItem("lhs2008save-v1"))');events.append({'label':label,'url':p.url,'state':state,'score':j.score(),'text':(await p.locator('body').inner_text())[-10000:]});save()
    if shot:await p.screenshot(path=str(O/(LABEL+'-'+label+'.png')),full_page=True)
    return state
   async def btn(name,exact=True):await p.get_by_role('button',name=name,exact=exact).first.click();await p.wait_for_timeout(60)
   async def nav(name):await p.get_by_role('button',name=re.compile('^'+name+'[●]?$')).first.click();await p.wait_for_timeout(60)
   async def arrange(titles):
    for i,title in enumerate(titles):
     await p.locator('button.tray-card').filter(has_text='《'+title+'》').click();await p.locator('button.wall-slot').nth(i).click()
   await p.goto(URL);await btn('全自助观展',False);await record('fresh')
   if LABEL=='acceptance':
    # Full normal site pages and the three albums; no source-derived route is needed.
    for name in ['社团简介','公告栏','影展列表','迁移说明']:
     await nav(name);await record(name)
    await nav('公告栏');await p.get_by_role('button',name='钉入线索夹',exact=True).first.click();await record('pin')
    await nav('相册浏览')
    for expo in [1,2,3]:
     await btn('第'+str(expo)+'届',False)
     cards=p.locator('article.tray-card button');count=await cards.count()
     for i in range(count):
      await cards.nth(i).click();await record(f'album{expo}-photo{i+1}');await p.keyboard.press('Escape')
    await nav('文件名索引');inp=p.get_by_placeholder('输入关键词',exact=False)
    for query in ['不存在的附件','attach_009','烟花','']:
     await inp.fill(query);await record('file-query-'+str(len(query)))
    await nav('暗房园地');await p.get_by_placeholder('输入四个大字口令').fill('错误口令');await btn('开门');s=await record('wrong-password');assert not s['darkroom']
    await p.get_by_placeholder('输入四个大字口令').fill('灯河纪事');await btn('开门');s=await record('memo',True);assert s['darkroom']
    await p.get_by_role('button',name='钉入线索夹',exact=True).click();await record('memo-pinned')
    await nav('影友留言簿');await btn('贴上留言板');s=await record('empty-guestbook');assert not s['gbUser']
    await p.get_by_placeholder('例如：路过的影友').fill('验收影友');await p.locator('textarea').fill('灯会复原测试留言');await btn('贴上留言板');s=await record('guestbook');assert len(s['gbUser'])==1
   else:
    await nav('暗房园地');await p.get_by_placeholder('输入四个大字口令').fill('灯河纪事');await btn('开门');await record('memo-delta-precondition')
   await nav('展览墙排序');assert await p.get_by_role('button',name='核对顺序',exact=True).is_disabled();s=await record('incomplete-wall');assert not s['solved'] and s['checkedCount']==0
   wrong=ORDER[1:]+ORDER[:1];await arrange(wrong);await btn('核对顺序');s=await record('wrong-wall',True);assert not s['solved'] and s['checkedCount']==1 and not j.score()['ending_reached']
   await btn('全部摘回');s=await record('wall-clear');assert not any(s['slots'])
   await arrange(ORDER);await record('correct-unsubmitted');assert not j.score()['ending_reached']
   await btn('核对顺序');s=await record('solved-wall',True);assert s['solved'];assert not j.score()['ending_reached']
   await btn('前往开幕之夜');await record('ending',True);assert j.score()['ending_reached']
   await p.get_by_placeholder('写下你的名字').fill('复原者');await btn('落款');s=await record('certificate');assert s['badgeName']=='复原者'
   await btn('打印观展证');await record('print-button')
   await p.reload();s=await record('reload-persisted');assert s['solved'] and s['badgeName']=='复原者'
   await btn('再排一次展墙');s=await record('replay');assert not s['solved'] and not any(s['slots']) and s['darkroom']
   await btn('重置本站进度');await record('reset-dialog')
   # Native confirm accepted above; registration must return.
   await btn('全自助观展',False);j=Judge.load(R/'judge/guangying-she/judge.json','guangying-she',R);s=await record('full-reset',True);assert not s['darkroom'] and not s['pinned'] and not s['gbUser'] and not s['solved'] and not j.score()['ending_reached']
   # Normal wall-only route proves optional login and no false prerequisite.
   await nav('展览墙排序');await arrange(ORDER);await btn('核对顺序');await btn('前往开幕之夜');s=await record('without-darkroom-ending');assert not s['darkroom'] and j.score()['ending_reached']
   await c.close();c=await b.new_context();p=await c.new_page();p.on('dialog',lambda d:asyncio.create_task(d.accept()));await p.goto(URL+'#/opening');await btn('全自助观展',False);j=Judge.load(R/'judge/guangying-she/judge.json','guangying-she',R);s=await record('fresh-opening-locked');assert not s['solved'] and not j.score()['ending_reached']
   # Guide route is author-supported but excluded from benchmark scoring.
   await btn('重置本站进度');await btn('巡展向导同行',False);await p.get_by_role('button',name='打开巡展向导提示').click();await record('guide-mode');assert (await p.evaluate('JSON.parse(localStorage.getItem("lhs2008save-v1")).hintMode'))=='on';assert not j.score()['ending_reached']
   result['passed']=True;result['browser_version']=b.version;save();print(json.dumps({'passed':True,'events':len(events),'errors':errors,'external_requests':requests}),flush=True);os._exit(0)
 except Exception:
  result['failure']=traceback.format_exc();save();print(result['failure'],flush=True);os._exit(1)
asyncio.run(main())
