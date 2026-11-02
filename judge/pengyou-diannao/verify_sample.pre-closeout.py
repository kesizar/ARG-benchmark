"""Private source-assisted UI replay. No state injection, clock changes or APIs."""
from pathlib import Path
import asyncio,argparse,json,sys,time
from urllib.parse import unquote
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R));T='pengyou-diannao';OUT=R/f'judge/{T}/verification'
from harness.config import load_config
from harness.browser_harness import BrowserHarness
from harness.judge import Judge
from harness.serve_local import LocalServer
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8821);p.add_argument('--aux-only',action='store_true');p.add_argument('--system-only',action='store_true');p.add_argument('--minimum-only',action='store_true');a=p.parse_args()
if a.aux_only:OUT=OUT/'auxiliary'
if a.system_only:OUT=OUT/'system'
if a.minimum_only:OUT=OUT/'minimum'
async def main():
 OUT.mkdir(parents=True,exist_ok=True);c=load_config(R/f'configs/{T}.json');c['entry_url']=f'http://127.0.0.1:{a.port}/index.html';c['allow_hosts']=[f'127.0.0.1:{a.port}'];c['local_serve'].update(port=a.port,ready_url=c['entry_url']);c['local_serve']['command'][-1]=str(a.port);c['settle_ms']=220
 h=BrowserHarness(c,OUT);server=LocalServer();j=None;steps=[];report={'kind':'engineering_ui_audit_not_model_score','page_errors':[],'http_errors':[],'negative_checks':0,'completed_routes':[],'read_views':[]}
 async def rec(label):
  await j.read(h);j.update(len(steps)+1);steps.append({'action':label,'score':j.score()});h.consume_step()
  if len(steps)%30==0:
   print('PC UI',len(steps),label,flush=True);(OUT/'progress.json').write_text(json.dumps({'steps':len(steps),'last':label},ensure_ascii=False),encoding='utf-8')
 async def act(x,label=None):
  result=await h.act(x);assert result=='ok',(x,result);await rec(label or str(x))
 async def click(target):
  await target.wait_for(state='visible');await target.scroll_into_view_if_needed();await target.click(trial=True);b=await target.bounding_box();assert b;await act({'op':'click','x':b['x']+b['width']/2,'y':b['y']+b['height']/2},'click '+str(target))
 async def fill(target,text):
  await click(target);old=await target.input_value();await act({'op':'key','key':'End'})
  for _ in old:await act({'op':'key','key':'Backspace'})
  await act({'op':'type','text':text});assert await target.input_value()==text
 async def wait(ms):await act({'op':'wait','ms':ms})
 def frame(name):return next(f for f in h.page.frames if unquote(f.url).endswith('/'+name))
 async def boot():
  await h.reset();nonlocal j;j=Judge.load(R/c['judge_path'],T,R);h.context.on('response',lambda r:report['http_errors'].append(r.url) if r.status>=400 and not r.url.endswith('/favicon.ico') else None);h.page.on('pageerror',lambda e:report['page_errors'].append(str(e)));await h.observe();await click(h.page.locator('#startGameBtn'));await wait(1100);await click(h.page.locator('.modal-mask .close-panel'))
 async def openapp(app,file):
  await click(h.page.locator('.icon[data-app="'+app+'"]'));await h.page.wait_for_timeout(600);f=frame(file);await f.wait_for_load_state();return f
 async def closeapp(app):await click(h.page.locator('.app-window[data-app="'+app+'"] .window-close').first)
 async def search(f,word,input='#searchInput',btn='#searchBtn'):
  await fill(f.locator(input),word);await click(f.locator(btn))
 async def snap(name):await h.observe(name+'.png')
 async def endingwait(kind):
  # All original narrative timers and dialogs remain intact.
  if kind=='true':await click(h.page.locator('#diaryLink'))
  for n in range(100):
   if h.pending:raise AssertionError('unexpected native dialog in ending')
   if await h.page.locator('.xp-dialog').count():break
   if kind=='surface' and await h.page.locator('#exitBtn:visible').count():await click(h.page.locator('#exitBtn'));continue
   buttons=h.page.locator('.center-popup .ok-btn:visible, #diaryOk:visible')
   if await buttons.count():await click(buttons.first)
   else:await wait(1000)
  else:raise AssertionError('ending final dialog not reached '+kind)
  await rec('final authored '+kind);assert j.score()['route_id']==kind and j.score()['ending_reached'],j.score();report['completed_routes'].append({'id':kind,'score':j.score()});await snap(kind+'-ending')
 async def puzzles(name):
  f=await openapp('browser','browser_main.html');await wait(800);g=frame('首页.html')
  await search(g,'wrong');assert 'necklace_code' not in j.checkpoints;report['negative_checks']+=1
  await search(g,'tbwfnf');await wait(8500);assert await h.page.evaluate('localStorage.getItem("has_secret_code")==="true"')
  await click(g.locator('[data-page="vip"]'));await click(g.locator('#vipPayButton'));await fill(g.locator('#payCode'),'wrong');await click(g.locator('#payConfirm'));assert not await h.page.evaluate('localStorage.getItem("vip_unlocked")==="true"');report['negative_checks']+=1
  await fill(g.locator('#payCode'),'吞噬，献出我自己');await click(g.locator('#payConfirm'));await click(g.locator('#closeEditorMsg'));report['vip_text']=await g.locator('#vipContentArea').inner_text();await click(g.locator('[data-page="home"]'));await click(g.locator('#lightOffBtn'));assert 'Raven_Anchor' in await g.locator('body').inner_text();await snap('password-night');await closeapp('browser')
  f=await openapp('mail','mail.html');await click(f.locator('#switchAccountBtn'));await click(f.locator('.account-item').last);await fill(f.locator('#loginEmail'),'zhubian@xinqing.com');await fill(f.locator('#loginPwd'),'wrong');await click(f.locator('#loginConfirm'));assert 'editor_login' not in j.checkpoints;report['negative_checks']+=1
  await fill(f.locator('#loginPwd'),'Raven_Anchor');await click(f.locator('#loginConfirm'))
  if not h.pending:assert 'editor_login' in j.checkpoints
  # Native prompt is triggered by original cross-frame storage event/10s timer.
  for _ in range(20):
   if h.pending:break
   await wait(1000)
  assert h.pending and h.pending.type=='prompt';ob=await h.observe();assert ob['pending_dialog'];await act({'op':'dialog','accept':False});report['prompt_cancel_verified']=True;assert 'editor_login' in j.checkpoints
  for _ in range(20):
   if h.pending:break
   await wait(1000)
  assert h.pending;await act({'op':'dialog','accept':True,'text':name});await endingwait('true' if name=='陈晓晴' else 'hidden')
 async def minimum_flow():
  await boot();f=await openapp('work','review.html');articles=await f.evaluate('articles');indices=[i for i,x in enumerate(articles) if not x['shouldReject']][:15]
  for i in indices:await click(f.locator(f'.submission-card[data-idx="{i}"] .btn-adopt'))
  assert await h.page.evaluate('JSON.parse(localStorage.getItem("review_adopted")).length')==15;await closeapp('work')
  f=await openapp('wetalk','wetalk.html');await search(f,'奥拉西坦');await click(f.locator('#submitQuiz'));assert not await h.page.evaluate('localStorage.getItem("surface_outcome")=="true"');await click(f.locator('input[name="q6"][value="D"]'));await click(f.locator('#submitQuiz'));await endingwait('surface');assert len(j.checkpoints)==15 and not j.side;assert j.score()['route_progress']==1;report['exactly_15_of_16_adopts_with_no_rejects_or_main_puzzles_verified']=True;report['wetalk_questionnaire_D_branch_verified']=True
 async def system_flow():
  await boot()
  async def menu():
   await click(h.page.locator('#startBtn'))
   if not await h.page.locator('#startMenu').is_visible():await click(h.page.locator('#startBtn'))
  await menu();await click(h.page.locator('#settingsBtn'));assert '文件已损坏' in await h.page.locator('.corrupt-msg').inner_text();await click(h.page.locator('.modal-mask .window-close'));report['settings_corrupt_verified']=True
  await menu();await click(h.page.locator('#loadGameBtn'));await click(h.page.locator('.slot-btn[data-slot="2"]'));assert not await h.page.evaluate('localStorage.getItem("save_slot_2")')
  await menu();await click(h.page.locator('#saveGameBtn'));await fill(h.page.locator('#saveNote'),'audit-before-raven');await click(h.page.locator('.slot-btn[data-slot="1"]'));assert await h.page.evaluate('JSON.parse(localStorage.getItem("save_slot_1"))._note')=='audit-before-raven'
  f=await openapp('wetalk','wetalk.html');await search(f,'渡鸦005');await closeapp('wetalk');assert await h.page.evaluate('localStorage.getItem("duyao_added")=="true"')
  await menu();await click(h.page.locator('#loadGameBtn'));await click(h.page.locator('.slot-btn[data-slot="1"]'));assert await h.page.evaluate('localStorage.getItem("duyao_added")=="true"');report['load_missing_keys_not_removed_defect_verified']=True
  await menu();await click(h.page.locator('#saveGameBtn'));await fill(h.page.locator('#saveNote'),'audit-after-raven');await click(h.page.locator('.slot-btn[data-slot="2"]'));assert await h.page.evaluate('JSON.parse(localStorage.getItem("save_slot_2")).duyao_added')=='true';report['two_save_slots_verified']=True
  await menu();await click(h.page.locator('#exitGameBtn'));assert h.pending and h.pending.type=='confirm';await act({'op':'dialog','accept':False});assert not h.page.is_closed();report['exit_cancel_verified']=True
  await menu();await click(h.page.locator('#restartGameBtn'));await wait(4000);assert not await h.page.evaluate('localStorage.length');report['restart_clears_slots_and_state']=True
 async def exploration():
  await boot()
  # Calendar corruption remains a five-second atmosphere effect, not a puzzle.
  await click(h.page.locator('#clock'));await wait(600);f=frame('calendar.html');await click(f.locator('#prevMonthBtn'));assert await f.locator('#resetBtn').count();await wait(5300);assert not await f.locator('#resetBtn').count()
  for _ in range(4):await click(f.locator('#nextMonthBtn'))
  assert await f.locator('#resetBtn').count();await click(f.locator('#resetBtn'));await closeapp('calendar');report['calendar_lower_upper_bounds_timer_reset_verified']=True
  # Four diary search gates and invalid/repeat input, all actual rendered entries.
  f=await openapp('diary','diary.html')
  for word in ['INVALID','火灾','高考','东华第二小学','张丽','火灾']:await search(f,word,'#searchDiaryInput','#searchDiaryBtn')
  report['diary_rendered_text']=await f.locator('#diaryList').inner_text();await closeapp('diary')
  f=await openapp('wetalk','wetalk.html')
  for word in ['INVALID','INVALID','INVALID','0377-6821435','渡鸦005','高考','秋秋','东华第二小学','张丽','火灾']:
   await search(f,word)
  ids=await f.locator('.contact-item').evaluate_all('(els)=>els.map(e=>e.dataset.id)');report['contact_texts']={}
  for cid in ids:
   await click(f.locator('.contact-item[data-id="'+cid+'"]'));report['contact_texts'][cid]=await f.locator('#messagesContainer').inner_text()
  await click(f.locator('.contact-item[data-id="linxiao"]'));await click(f.locator('#unlockWeirdDiaryBtn'));await search(f,'奥拉西坦');await click(f.locator('#cancelQuiz'));await search(f,'奥拉西坦');assert not await f.locator('#submitQuiz').count();report['wetalk_cancel_consumes_quiz_verified']=True;await closeapp('wetalk')
  f=await openapp('album','album_final.html');db=await f.evaluate('searchPhotoDatabase');report['album_keywords']=list(db);report['album_photo_cards']={}
  for word in ['INVALID']+list(db)+['主编','陈晞晴']:
   await search(f,word,'#searchAlbumInput','#searchAlbumBtn')
   if word=='奥拉西坦':await click(f.locator('input[name="q6"][value="A"]'));await click(f.locator('#submitQuiz'));assert not await h.page.evaluate('localStorage.getItem("surface_outcome")==="true"')
   if word in ['主编','陈晞晴']:await wait(6300)
   count=await f.locator('.photo-card').count();report['album_photo_cards'][word]=count
   for i in range(count):
    await click(f.locator('.photo-card').nth(i));await click(f.locator('.close-modal'))
  assert not await h.page.evaluate('localStorage.getItem("album_searched_olaxitan")==="true"');report['original_postit_missing_flag_confirmed']=True;await closeapp('album')
  f=await openapp('huihui','huihui.html');await click(f.locator('.goods-item[data-id="necklace"]'));await click(f.locator('#contactSellerBtnFromDetail'));await click(f.locator('.chat-image'));await snap('necklace-full');await click(f.locator('.close-modal'));report['necklace_image_read']=True;await closeapp('huihui')
  f=await openapp('account','account.html');report['account_text']=await f.locator('body').inner_text();await closeapp('account')
  # Traverse all generated forum/info/story entries with real modal open/close.
  f=await openapp('browser','browser_main.html');await wait(600);g=frame('首页.html');report['web_data_counts']=await g.evaluate('({forum:forumPosts.length,weird:weirdStories.length,info:infoData.length,vip:vipPosts.length,award:awardArticles.length})');report['web_modal_reads']={}
  for page,selector in [('forum','.forum-item'),('weird','.weird-card'),('info','.info-item')]:
   await click(g.locator('[data-page="'+page+'"]'));n=await g.locator(selector).count();report['web_modal_reads'][page]=[]
   for i in range(n):
    await click(g.locator(selector).nth(i));report['web_modal_reads'][page].append(await g.locator('.post-modal').inner_text());await click(g.locator('.post-modal button').last)
  for tab in ['news','medical']:
   await click(f.locator('[data-tab="'+tab+'"]'));await wait(800);page=frame(tab+'.html');report['read_views'].append({'page':tab,'text':await page.locator('body').inner_text(),'images':await page.locator('img').evaluate_all('(es)=>es.map(e=>({src:e.getAttribute("src"),ok:e.complete&&e.naturalWidth>0}))')});await snap(tab)
  await closeapp('browser')
  # Native account login uses only fictional credentials from the game.
  f=await openapp('mail','mail.html')
  for i in range(await f.locator('.email-item').count()):await click(f.locator('.email-item').nth(i));report['read_views'].append({'mail':await f.locator('#detailContent').inner_text()});await click(f.locator('#backToListBtn'))
  await click(f.locator('#switchAccountBtn'));await click(f.locator('.account-item').last);await fill(f.locator('#loginEmail'),'zhubian@xinqing.com');await fill(f.locator('#loginPwd'),'Raven_Anchor');await click(f.locator('#loginConfirm'));await click(f.locator('#switchAccountBtn'));await click(f.locator('.account-item').last)
  mainpage=h.page
  await click(f.locator('.email-item').nth(0));await wait(800);chars=h.page.locator('.covered-char');report['covered_email_chars']=await chars.count()
  # Clicks move the ordinary pointer over each letter, invoking original mouseenter.
  h.settle_ms=0
  for i in range(await chars.count()):await click(chars.nth(i))
  h.settle_ms=220
  assert await h.page.locator('#unlockHint.show').count();report['covered_email_revealed']=True;await snap('email-revealed');await act({'op':'close_tab','i':h.context.pages.index(h.page)});h.page=mainpage
  await click(f.locator('.email-item').nth(1));await wait(3600);report['garbled_email_text']=await h.page.locator('body').inner_text();await snap('email-garbled-revealed');await act({'op':'close_tab','i':h.context.pages.index(h.page)});h.page=mainpage;await closeapp('mail')
  report['auxiliary_exploration_complete']=True
 try:
  server.start(c,R,OUT/'server.log');assert server.owned;report['server_owned']=True;await h.start()
  if a.minimum_only:
   await minimum_flow();report['blocked_requests']=h.blocked;assert not report['page_errors'] and not report['http_errors'] and not h.blocked;report['pass']=True;return
  if a.system_only:
   await system_flow();report['blocked_requests']=h.blocked;assert not report['page_errors'] and not report['http_errors'] and not h.blocked;report['pass']=True;return
  if a.aux_only:
   await exploration();report['blocked_requests']=h.blocked;assert not report['page_errors'] and not report['http_errors'] and not h.blocked;report['pass']=True;return
  await boot();f=await openapp('work','review.html');articles=await f.evaluate('articles');report['articles']=articles
  for i,article in enumerate(articles):
   card=f.locator(f'.submission-card[data-idx="{i}"]');wrong='.btn-adopt' if article['shouldReject'] else '.btn-reject';right='.btn-reject' if article['shouldReject'] else '.btn-adopt';before=set(j.checkpoints)|set(j.side);await click(card.locator(wrong));assert before==set(j.checkpoints)|set(j.side);report['negative_checks']+=1;await click(f.locator('#closeToastBtn'));await click(card.locator(right));assert f'article_{i:02d}' in set(j.checkpoints)|set(j.side)
  assert await h.page.evaluate('JSON.parse(localStorage.getItem("review_adopted")).length')==16;report['classification_all_30_correct_and_wrong_verified']=True;await closeapp('work')
  f=await openapp('browser','browser_main.html');await wait(3200);g=frame('首页.html');report['award_articles']=[]
  for i in range(await g.locator('.award-item').count()):
   await click(g.locator('.award-item').nth(i));report['award_articles'].append(await g.locator('.post-modal').inner_text());await click(g.locator('.post-modal button').last)
  assert report['award_articles'];await closeapp('browser')
  f=await openapp('album','album_final.html');await search(f,'奥拉西坦','#searchAlbumInput','#searchAlbumBtn');await click(f.locator('#submitQuiz'));assert not await h.page.evaluate('localStorage.getItem("surface_outcome")==="true"');report['negative_checks']+=1;await click(f.locator('input[name="q6"][value="C"]'));await click(f.locator('#submitQuiz'));await endingwait('surface');await click(h.page.locator('#xpLaterBtn'));await click(h.page.locator('#exitBtn'));await click(h.page.locator('#xpRestartBtn'));await wait(4000);assert h.page.url.endswith('/index.html');assert not await h.page.evaluate('localStorage.length');report['in_game_restart_reset_verified']=True
  await boot();await puzzles('陈晓晴');await boot();await puzzles('无名测试');report['fresh_context_reset_verified']=True
  report['blocked_requests']=h.blocked;report['steps']=steps;assert not report['page_errors'] and not report['http_errors'] and not h.blocked;report['pass']=True
 except Exception as e:
  report['failure']=repr(e)
  if h.page and not h.pending:await h.page.screenshot(path=str(OUT/'failure.png'))
  raise
 finally:
  report['steps']=steps;(OUT/('minimum-acceptance.json' if a.minimum_only else 'system-acceptance.json' if a.system_only else 'auxiliary-acceptance.json' if a.aux_only else 'acceptance.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();server.stop()
 print('PC FULL UI PASS',flush=True)
if __name__=='__main__':asyncio.run(main())
