from pathlib import Path
import json,hashlib,shutil,re,ast
R=Path(__file__).resolve().parents[1];T='laopengyou';J=R/'judge'/T;P=R/'tasks'/T
(J/'source').mkdir(parents=True,exist_ok=True);(P/'mirror').mkdir(parents=True,exist_ok=True)
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
for f,n in [(R/f'configs/{T}.json','legacy-config.json'),(J/'judge.json','legacy-judge.json')]:
 if f.exists() and not (J/'source'/n).exists():shutil.copyfile(f,J/'source'/n)
src=R/'ARG-packs/verify-84/bodies/83.html';sha=hashlib.sha256(src.read_bytes()).hexdigest();assert sha=='247ef750c1eacbbad77777dec7ca3d6a5d2000c80e3789c0d1dd13f84e44fc8a';s=src.read_text(encoding='utf-8');shutil.copyfile(src,P/'mirror/index.html')
q=[]
for line in s[s.index('const QUIZ ='):s.index('function $(id)')].splitlines():
 if 'correct:' in line:
  item=line.strip().rstrip(',');item=re.sub(r'([{,])\s*(\w+)\s*:',r'\1"\2":',item);q.append(ast.literal_eval(item))
assert len(q)==8;write(J/'private-quiz.json',q)
c=json.loads((R/'configs/baoya.json').read_text(encoding='utf-8'));c.update(id=T,judge_path=f'judge/{T}/judge.json',model_visible={'title':'老朋友之死','intro':'你在本地虚构手机中寻找线索，还原故事并提交结论。站内账号均为游戏谜题，无需真实账号。'})
c['local_serve']['command'][3]=f'tasks/{T}/mirror';c['limits'].update(max_steps=600,max_seconds=3600,max_answer_submits=40);c['notes_for_report']=['所有账号均虚构、无需真实网络账号。','两条复活选择均为正式通关，不擅自评高低。'];write(R/f'configs/{T}.json',c)
def hk(e):return {'type':'js_truthy','expr':e}
h={'system':hk("document.querySelector('.view.active')?.id.startsWith('view-sub-')"),'wish':hk("document.querySelector('#modal-revive-yes-result')?.classList.contains('show')"),'accept':hk("document.querySelector('#modal-revive-no-result')?.classList.contains('show')"),'quiz_pass':hk("document.querySelector('#modal-revive')?.classList.contains('show')"),'wrong_quiz':hk("document.querySelector('#modal-quiz-wrong')?.classList.contains('show')"),'hint':hk("document.querySelector('#modal-forum-hint')?.classList.contains('show')")}
for key,storage in [('wechat','wechatLogin'),('qq','qqLogin'),('diary','subDiaryLogin'),('subqq','subQqLogin')]:h[key]=hk(f"localStorage.getItem('{storage}') === '1'")
submitted="['modal-quiz-wrong','modal-revive','modal-revive-yes-result','modal-revive-no-result'].some(id=>document.getElementById(id)?.classList.contains('show'))"
for i,item in enumerate(q):
 prefix=f"#sub-submit-body .quiz-question[data-quiz-index=\"{i}\"]"
 if item.get('type')=='pair':
  checks=[]
  for li,ri in item['correct'].items():
   selector=prefix+' .pair-name[data-left='+json.dumps(str(li))+']'
   expected='（'+item['rightOptions'][ri]+'）'
   checks.append('document.querySelector('+json.dumps(selector)+')?.textContent.endsWith('+json.dumps(expected,ensure_ascii=False)+')')
  expr=' && '.join(checks)
 else:
  correct=item['correct'] if item.get('type')=='multi' else [item['correct']]
  expr=f"JSON.stringify(Array.from(document.querySelectorAll({json.dumps(prefix+' .quiz-option.selected')}),e=>Number(e.dataset.oi)).sort((a,b)=>a-b)) === '{json.dumps(correct,separators=(',',':'))}'"
 h[f'quiz_{i+1}']=hk('('+submitted+') && ('+expr+')')
critical=['system']+[f'quiz_{i+1}' for i in range(8)]
write(J/'judge.json',{'hooks':h,'checkpoints':[{'id':k,'hook':k,'op':'truthy','role':'critical'} for k in critical]+[{'id':k,'hook':k,'op':'truthy','role':'optional'} for k in ['wechat','qq','diary','subqq']],'events':{k:{'hook':k,'op':'truthy'} for k in ['wrong_quiz','quiz_pass','hint']},'routes':[{'id':k,'gates':critical,'ending':{'hook':k,'op':'truthy'}} for k in ['wish','accept']]})
views=re.findall(r'<div[^>]*id="(view-[^"]+)"',s);search=re.findall(r"'([^']+)': 'result-[^']+'",s[s.index('const SEARCH_MAP'):s.index('const MEMO_ITEMS')]);write(J/'flow.json',{'record_id':'added84:0083','views':views,'search_keys':search,'mandatory':['unlock and death notice (story setup, unscored)','settings advanced system credentials','final quiz8 questions then revival yes/no'],'optional_gates':['wechat pinyin identity','QQ Hamiltonian account and two-rail birthday password','diary departure date','subQQ private account/password'],'narrative_material':['all main/sub memo entries','wechat chats and moments','main/sub QQ chats including xiang view','11 simulated search articles and forum home/me/secret posts','diary expandable entries'],'endings':[{'id':'wish','type':'formal_completion','rank':None,'choice':'revive yes'},{'id':'accept','type':'formal_completion','rank':None,'choice':'revive no'}],'non_endings':['opening death modal is premise, not player failure','3 system errors show retry hint','wrong quiz can retry','both endings agree merge to creator credits; not another ending'],'reset':'No in-game full reset; new browser context clears localStorage and closure quiz/login state. Reload preserves localStorage tokens/searchHistory, resets quiz closure.','legacy_judge_risk':'Old dom_regex can match hidden result texts at initial page load. New hooks explicitly require modal show class.'})
write(J/'checkpoint-spec.json',{'critical':[{'id':'system','mechanism':'decode forum secret posts to system name/password; accepted credentials enter sub home'}]+[{'id':f'quiz_{i+1}','question':a['q'],'mechanism':a.get('type','single'),'grading':'judge sees selected DOM only while completed quiz submission result modal is visible; correct answer latched even if other submitted questions wrong; no grading mere unsubmitted selection'} for i,a in enumerate(q)],'optional':['wechat','qq','diary','subqq'],'why_optional':'mechanically no mandatory read/login prerequisite if solver knows final facts; keep evidence acquisition gates distinct from route requirements','pair_scoring':'one checkpoint per complete matching question; not per person','negative_requirements':'hidden static endings, incomplete quiz, wrong credentials, wrong/missing/extra answers must not falsely score the corresponding point'})
write(P/'provenance.json',{'record_id':'added84:0083','source_url':'https://mobilephone1.pages.dev/','source_snapshot':'ARG-packs/verify-84/bodies/83.html','source_sha256':sha,'modifications':[],'account_requirement':'none (fictional local credentials)','dependencies':'single inline HTML/CSS/JS, no external resources','live_origin_parity':'not checked'})
(P/'README.md').write_text('''# 老朋友之死（原样冻结快照）

Python3.11+、requirements.txt固定依赖与Playwright Chromium（或Edge/Chrome）需另行准备。所有账号均为游戏内虚构输入，无真实账号、网络服务或支付依赖。

标准：`python scripts/run_one.py --config configs/laopengyou.json --policy script`（两步冒烟），模型用`--policy llm`，API凭据由环境提供，不随包保存。

手动：`python scripts/serve_static.py --root tasks/laopengyou/mirror --port 8811`，访问http://127.0.0.1:8811/index.html；Ctrl+C停止。仅托管mirror，禁止托管含裁判的包根目录。完整重置使用全新浏览器context；刷新仍保留登录和搜索历史，但问卷会清空。

私有验收：`python judge/laopengyou/verify_sample.py --port 8812`。源答案仅供工程回放，不提供模型。两结局暂不评价好坏，错误输入可重试。登录门与问卷分开，逐题只在提交完整问卷结果时采分，防止无提交切换选项赚分。
''',encoding='utf-8')
(J/'review.md').write_text('''# 私有内容与公平性审核

资源不改字节，原作署名/使用声明保留，包仅本地评测使用。手机各app和搜索全为模拟。旧裁判搜整页文本有隐藏弹框误报风险，新的完成判定要求对应模态框show。开场死亡是故事前提，不是失败结局；两种复活选择均正式完成，不擅定善恶。作者框为片尾。

五个账号/系统门里，只有次系统门在两条机械路径中必经，微信/QQ/日记/次QQ供获取线索，可凭已有事实绕过，均记optional。QQ九位数题按九九表邻接约束完整回溯得到唯一728163549，非多解猜测。最终8题含两组完整配对和一组精确多选，每题单独采分但必须在一次完整提交的结果模态框出现时才检查DOM，避免循环选择未提交答案刷分。错题反馈不逐题指出答案，私有裁判不进入模型观察。

尚需逐题叙事证据充分性、医疗/解离概念与故事表达复核，不把作品叙事视为现实医学事实。未核实时原站版本、跨OS或模型能力。无付费API测试。
''',encoding='utf-8')
print('prepared',T,'quiz',len(q),'views',len(views))
