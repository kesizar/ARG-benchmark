import json,pathlib
p=pathlib.Path
cfg=json.loads(p('configs/wuluo-cun.json').read_text(encoding='utf-8'))
cfg.update(id='huisheng-weizhi',account_requirement='none',model_visible={'title':'回声未止','intro':'调查林沐失踪事件，使用作品内的电脑与网站搜集线索并作出选择。'},entry_url='http://127.0.0.1:8821/index.html',judge_path='judge/huisheng-weizhi/judge.json',notes_for_report=['本地镜像为公开作品现行版本，虚构游戏账号为作品内交互，无需真实账号。'])
cfg['local_serve'].update(command=['python','scripts/serve_static.py','--root','tasks/huisheng-weizhi/mirror','--port','8821'],ready_url=cfg['entry_url'],port=8821)
cfg['allow_hosts']=['127.0.0.1:8821'];cfg['limits']={'max_steps':400,'max_seconds':3600,'max_answer_submits':5}
p('configs/huisheng-weizhi.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
hooks={
 'student':"location.pathname.endsWith('/jiangdudaxue.html') && !!document.querySelector('#studentResult.active')",
 'nickname':"location.pathname.endsWith('/huisheng.html') && document.querySelector('#loginStep2')?.style.display === 'block'",
 'account':"location.pathname.endsWith('/huisheng.html') && !!document.querySelector('#loggedInApp.show')",
 'retained':"location.pathname.endsWith('/huisheng.html') && document.querySelector('#retainedRecovered')?.style.display === 'block'",
 'null_search':"localStorage.getItem('null_searched') === '1'",
 'memo':"location.pathname.endsWith('/game.html') && !!document.querySelector('#memoOpenOverlay.show')",
 'confession':"localStorage.getItem('null_confession_read') === '1'",
 'privacy':"location.pathname.endsWith('/game.html') && !!document.querySelector('.evidence-list')",
 'handback':"localStorage.getItem('evidence_handed_back') === '1'"
}
ends={'handback':'theonlyend1.html','truth':'end2.html','self':'end3.html','cut':'end4.html','forget':'end5.html'}
for name,file in ends.items(): hooks['end_'+name]=f"location.pathname.endsWith('/{file}') && !!document.querySelector('#endingStage.show')"
judge={'hooks':{k:{'type':'js_truthy','expr':v} for k,v in hooks.items()},'checkpoints':[{'id':k,'hook':k,'op':'truthy'} for k in ('student','nickname','account','retained','null_search','memo','confession','privacy','handback')], 'events':{},'routes':[{'id':name,'tier':'normal','gates':(['null_search','confession','handback'] if name=='handback' else ['privacy']),'ending':{'hook':'end_'+name,'op':'truthy'}} for name in ends],'terminal_failures':[],'ending':None,'answer_sha256':[],'answer_hash_file':None,'request_milestones':[],'submit_conclusion':{'enabled':False,'schema':None},'rubric_path':None}
p('judge/huisheng-weizhi/judge.json').write_text(json.dumps(judge,ensure_ascii=False,indent=2),encoding='utf-8')
