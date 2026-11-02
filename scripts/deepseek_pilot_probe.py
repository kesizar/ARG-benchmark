import json,os,pathlib,sys,httpx
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from harness.env import load_env
load_env(pathlib.Path.cwd())
key=os.environ.get('AGENT_API_KEY')
if not key:raise SystemExit('AGENT_API_KEY 未设置')
try:
 r=httpx.post('https://api.deepseek.com/chat/completions',headers={'Authorization':'Bearer '+key},json={'model':'deepseek-flash','messages':[{'role':'user','content':'只输出 OK'}],'max_tokens':256},timeout=60,trust_env=False)
 try: body=r.json()
 except ValueError: body={}
 if r.status_code==200:
  x=(body.get('choices') or [{}])[0];print(json.dumps({'status':r.status_code,'model':body.get('model'),'finish_reason':x.get('finish_reason'),'has_text':bool((x.get('message') or {}).get('content')),'usage':body.get('usage')},ensure_ascii=False))
 else:
  e=body.get('error') or {}; print(json.dumps({'status':r.status_code,'error_code':e.get('code')},ensure_ascii=False))
except Exception as e:print(json.dumps({'error_type':type(e).__name__},ensure_ascii=False))
