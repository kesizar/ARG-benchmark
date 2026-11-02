"""Acquire the current public revision; resource staging is not readiness."""
from pathlib import Path
import hashlib
import json
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
ORIGIN='https://cbe13e960c974eb28565ada57114771e.app.workbuddy.link/'


def main():
    dest=ROOT/'tasks/shisanlou-xia/mirror';dest.mkdir(parents=True,exist_ok=True)
    names=['index.html','style.css','data.js','game.js','scare-normal.png','scare-burned.png']
    files=[]
    for name in names:
        path=dest/name
        done=subprocess.run(['curl.exe','--fail','--location','--silent','--show-error','--connect-timeout','10','--max-time','30','--output',str(path),ORIGIN+('' if name=='index.html' else name)],capture_output=True,text=True)
        transport='curl'
        if done.returncode:
            import httpx
            response=httpx.get(ORIGIN+('' if name=='index.html' else name),timeout=20,follow_redirects=True)
            response.raise_for_status()
            path.write_bytes(response.content)
            transport='httpx_after_curl_failure'
        data=path.read_bytes()
        if name.endswith('.png'):assert data.startswith(b'\x89PNG'),name
        elif name=='index.html':assert '十三楼之下' in data.decode('utf-8')
        else:assert '<!DOCTYPE' not in data.decode('utf-8')[:100],f'HTML fallback returned for {name}'
        files.append({'file':name,'source_url':ORIGIN+('' if name=='index.html' else name),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'transport':transport})
    (ROOT/'tasks/shisanlou-xia/provenance.json').write_text(json.dumps({'record_id':'base664:0554','source_url':ORIGIN,'revision':'fresh acquisition 2026-10-26','changes':[],'files':files,'status':'resources_staged_not_full_flow_verified'},ensure_ascii=False,indent=2),encoding='utf-8')
    print('staged_files',len(files),'bytes',sum(x['bytes'] for x in files))


if __name__=='__main__':main()
