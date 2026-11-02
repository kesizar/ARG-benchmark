from pathlib import Path
import json,hashlib,shutil
R=Path(__file__).resolve().parents[1];T='zhengming-renlei';J=R/'judge'/T;P=R/'tasks'/T
J.mkdir(exist_ok=True);(J/'source').mkdir(exist_ok=True);(P/'mirror').mkdir(parents=True,exist_ok=True)
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
for old,name in [(R/f'configs/{T}.json','legacy-config.json'),(J/'judge.json','legacy-judge.json')]:
 if old.exists() and not (J/'source'/name).exists():shutil.copyfile(old,J/'source'/name)
src=R/'ARG-packs/verify-416/bodies/658.html';sha=hashlib.sha256(src.read_bytes()).hexdigest();assert sha=='02e378f71da78338d5b22bfbc05993bf9f283e6954d2c66c86b957db65984494';shutil.copyfile(src,P/'mirror/index.html')
c=json.loads((R/'configs/baoya.json').read_text(encoding='utf-8'));c.update(id=T,judge_path=f'judge/{T}/judge.json',model_visible={'title':'证明你不是人类','intro':'完成本地网页安全验证，只依据页面观察操作。'})
c['local_serve']['command'][3]=f'tasks/{T}/mirror';c['limits'].update(max_steps=160,max_seconds=1800);c['notes_for_report']=['零推理点的交互演出，完成不代表推理能力。'];write(R/f'configs/{T}.json',c)
def hk(e):return {'type':'js_truthy','expr':e}
h={'complete':hk("document.querySelector('#log')?.textContent === '结论：非人类' && document.querySelector('#wrap .sub')?.textContent.includes('验证完成')"),'mask':hk("document.querySelector('#log')?.textContent === '伪装协议：已启动' && document.querySelector('#wrap .sub')?.textContent.includes('欢迎回来')")}
for key,feedback in [('real_A','错了。但没关系。'),('real_B','对。但你确定吗？'),('not_human','我也是这么想的。'),('behind','你没有回头。很好。')]:h[key]=hk('document.querySelector("#wrap .sub")?.textContent === '+json.dumps(feedback,ensure_ascii=False))
write(J/'judge.json',{'hooks':h,'checkpoints':[],'events':{k:{'hook':k,'op':'truthy'} for k in h if k!='complete'},'routes':[{'id':'complete','gates':[],'ending':{'hook':'complete','op':'truthy'}}]})
write(P/'provenance.json',{'record_id':'base664:0658','source_url':'https://qwert987df.github.io/kkkk/','source_snapshot':'ARG-packs/verify-416/bodies/658.html','source_sha256':sha,'modifications':[],'dependencies':'inline Canvas/data URI SVG and synthesized WebAudio only','live_parity':'not verified','account_requirement':'none'})
write(J/'flow.json',{'stages':[{'index':i,'id':n} for i,n in enumerate(['checkbox','traffic','crosswalk','watched','word','real','soul','questions','reveal'])],'endings':[{'id':'complete','type':'formal_completion','rank':None},{'id':'mask','type':'post_completion_continuation','rank':None}],'terminal_failure_or_death':[],'question_branches':{'identity':['是','不是','我不确定','问题本身就是答案'],'fear':['屏幕','身后','记忆','它'],'all':'16 combinations converge; four pairings used for UI option coverage'},'randomness':'drawing, phrase and humanity increments; no outcome change','reset':'reload/fresh context resets all state, no localStorage'})
write(J/'checkpoint-spec.json',{'critical_reasoning_points':[],'optional_reasoning_points':[],'reason':'Traffic answers array used for rendering only; all grids ignore selected. Word never reads value. Image A explicitly wrong and B both proceed. All question options pass. Old three optional points converted to events.','latching':'Update after each UI action; completion stays locked after mask replaces its text.'})
(P/'README.md').write_text('''# 证明你不是人类（冻结原样快照）

Python3.11+、requirements.txt中依赖、Playwright Chromium或已安装Edge/Chrome需另行安装。无外部游戏资源和账号。

运行：`python scripts/run_one.py --config configs/zhengming-renlei.json --policy script`（两步冒烟）；模型评测用`--policy llm`，API密钥仅由环境变量提供。

手动：`python scripts/serve_static.py --root tasks/zhengming-renlei/mirror --port 8811`，访问http://127.0.0.1:8811/index.html；Ctrl+C停止。重新开始reload或新context完全重置。仅托管mirror，严禁托管含私有裁判的包根目录。

私有验收：`python judge/zhengming-renlei/verify_sample.py --port 8812`。四遍覆盖空/错词、空选/全选/部分网格、真假图A/B、全部8问答选项及后记/重启。没有推理判题，零计分点，不适合作推理跑分；正式完成后继续伪装只是后记，标准runner在首个完成停止。
''',encoding='utf-8')
(J/'review.md').write_text('''# 内容复核

9阶段交互恐怖演出。traffic定义answers只用于绘图，selected未校验；其余网格也不判断选择；词语输入未读取value；真假图A标错与B同样继续；两问16组合仅反馈不同。故旧3个optional评分改成事件，零有效推理点。最终完成不评好坏，继续伪装是完成后记，无失败/死亡/隐藏结局。

HTML保持字节不变。随机绘图/短语/人性值不改变路径，不能保证像素复现。四次UI回放覆盖8问答选项，非16组合穷举。未验实时原站、跨OS或模型能力，无付费API。
''',encoding='utf-8')
print('prepared unchanged',T)
