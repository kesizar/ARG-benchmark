import asyncio,json,os,pathlib,sys
root=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from harness.env import load_env
load_env(root)
key=os.environ.get('AGENT_API_KEY')
if not key:raise SystemExit('配对的 DeepSeek 凭据缺失')
os.environ['OPENAI_API_KEY']=key
os.environ['OPENAI_BASE_URL']='https://api.deepseek.com'
os.environ['OPENAI_MODEL']='deepseek-flash'
os.environ['LLM_PROVIDER']='deepseek'
os.environ['AGENT_HTTP_TRUST_ENV']='false'
os.environ['LLM_MAX_OUTPUT_TOKENS']='4096'
os.environ['LLM_TEMPERATURE']='1'
os.environ.pop('LLM_REASONING_EFFORT',None)
os.environ.pop('ENABLE_THINKING',None)
os.environ.pop('PRESERVE_REASONING',None)
from harness.loop import run
try:
 summary=asyncio.run(run(root/'data/pilot/deepseek-20261028/config.json',policy='llm',obs_mode='B',repo_root=root,run_kind='test'))
 print('PILOT_SUMMARY '+json.dumps({k:summary.get(k) for k in ['task_id','ended_reason','steps','seconds','scoring_protocol','target_success','progress','checkpoints_reached','checkpoints_total','tokens','model','judge_error']},ensure_ascii=False))
except Exception as e:
 print('PILOT_ERROR '+json.dumps({'type':type(e).__name__,'message':str(e)[:240]},ensure_ascii=False));raise
