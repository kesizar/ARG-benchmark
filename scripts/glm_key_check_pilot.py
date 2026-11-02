import getpass, json, httpx
key=getpass.getpass('请输入测试密钥：').strip()
if not key: raise SystemExit('未收到密钥')
headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'}
payload={'model':'glm-5.3-flash','messages':[{'role':'user','content':'请只回答：OK'}],'max_tokens':256}
try:
 r=httpx.post('https://open.bigmodel.cn/api/paas/v4/chat/completions',headers=headers,json=payload,timeout=90,trust_env=False)
 try: body=r.json()
 except Exception: body={}
 if r.status_code==200:
  print(json.dumps({'ok':True,'status':r.status_code,'model':body.get('model'),'usage':body.get('usage'),'finish_reason':(body.get('choices') or [{}])[0].get('finish_reason'),'has_text':bool(((body.get('choices') or [{}])[0].get('message') or {}).get('content'))},ensure_ascii=False))
 else:
  err=body.get('error') or {}; print(json.dumps({'ok':False,'status':r.status_code,'error_code':err.get('code'),'message':str(err.get('message') or '')[:200]},ensure_ascii=False))
except Exception as e:
 print(json.dumps({'ok':False,'error_type':type(e).__name__},ensure_ascii=False))
