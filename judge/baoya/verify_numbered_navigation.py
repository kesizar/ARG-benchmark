"""Targeted integration regression: use observed element numbers, not coordinates."""
import argparse,asyncio,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8813);args=p.parse_args();sys.path.insert(0,str(ROOT))
from harness.config import load_config
from harness.browser_harness import BrowserHarness
from harness.serve_local import LocalServer

async def main():
    out=ROOT/'judge/baoya/verification';out.mkdir(parents=True,exist_ok=True)
    c=load_config(ROOT/'configs/baoya.json');c['entry_url']=f'http://127.0.0.1:{args.port}/index.html';c['allow_hosts']=[f'127.0.0.1:{args.port}'];c['local_serve'].update(port=args.port,ready_url=c['entry_url']);c['local_serve']['command'][-1]=str(args.port)
    s=LocalServer();h=BrowserHarness(c,out);report={'deployment_root':str(ROOT),'runtime_source':str(Path(sys.modules['harness.browser_harness'].__file__)),'steps':[]}
    try:
        s.start(c,ROOT,out/'numbered-server.log');await h.start();await h.reset()
        first=await h.observe('numbered-index.png');start=next(e for e in first['elements'] if '开始调查' in e['label'])
        a={'op':'click','n':start['n']};assert await h.act(a)=='ok';await h.page.wait_for_url('**/email.html');report['steps'].append({'action':a,'url':h.page.url})
        raw=await h.observe('numbered-email.png');target=next(e for e in raw['elements'] if '官网' in e['label'])
        geometry=await h.page.locator('a[href="baoyahealth.html"]').evaluate('''e=>{const r=e.getBoundingClientRect();const hit=document.elementFromPoint((r.left+r.right)/2,(r.top+r.bottom)/2);return {client_rect_count:e.getClientRects().length,old_bbox_center_hits:!!hit&&(hit===e||e.contains(hit))}}''')
        assert geometry['client_rect_count']>=2,geometry
        assert not geometry['old_bbox_center_hits'],geometry
        a={'op':'click','n':target['n']};assert await h.act(a)=='ok';await h.page.wait_for_url('**/baoyahealth.html');await h.observe('numbered-company.png')
        assert await h.page.locator('#username').is_visible()
        report['steps'].append({'action':a,'label':target['label'],'url':h.page.url});report['wrapped_link_geometry']=geometry
        report['coordinate_override_used']=False;report['pass']=True
    finally:
        (out/'numbered-navigation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();s.stop()
    print('BAOYA NUMBERED NAVIGATION PASS',flush=True)

if __name__=='__main__':asyncio.run(main())
