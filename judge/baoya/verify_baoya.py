"""Private engineering replay using only player UI actions via BrowserHarness."""
import argparse,asyncio,ast,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--port',type=int,default=8811);args=p.parse_args();ROOT=args.root.resolve();sys.path.insert(0,str(ROOT))
from harness.browser_harness import BrowserHarness
from harness.config import load_config
from harness.judge import Judge
from harness.serve_local import LocalServer
OUT=ROOT/'judge/baoya/verification'

def source(name):return (ROOT/'tasks/baoya/mirror'/name).read_text(encoding='utf-8')
def val(name,key):return re.search(r'const '+key+r'\s*=\s*[\"\']([^\"\']+)',source(name))[1]

class Replay:
    def __init__(self,h):self.h=h;self.j=Judge.load(ROOT/'judge/baoya/judge.json','baoya',ROOT);self.trace=[];self.negative=0;self.pages=set()
    async def record(self,action):
        await self.j.read(self.h);fresh=self.j.update(len(self.trace)+1)
        self.pages.add(self.h.page.url.rsplit('/',1)[-1]);self.trace.append({'action':action,'new':fresh,'score':self.j.score()});self.h.consume_step()
    async def click(self,selector,negative=False):
        before=set(self.j.checkpoints)|set(self.j.side)
        loc=self.h.page.locator(selector).first;await loc.wait_for(state='visible',timeout=10000);await loc.scroll_into_view_if_needed();await loc.click(trial=True)
        b=await loc.evaluate('(e)=>{const r=e.getClientRects()[0];return {x:r.x,y:r.y,width:r.width,height:r.height}}');assert b
        r=await self.h.act({'op':'click','x':b['x']+b['width']/2,'y':b['y']+b['height']/2});assert r=='ok',r
        if self.h.pending:await self.h.act({'op':'dialog','accept':True})
        await self.h.page.wait_for_timeout(180)
        await self.record({'op':'click','selector':selector})
        if negative:assert before==set(self.j.checkpoints)|set(self.j.side);assert not self.j.ending_reached;self.negative+=1
    async def type(self,selector,text):
        loc=self.h.page.locator(selector).first;await loc.scroll_into_view_if_needed();b=await loc.bounding_box();assert b
        self.h.elements=[{'n':0,'x':b['x']+b['width']/2,'y':b['y']+b['height']/2}]
        r=await self.h.act({'op':'type','n':0,'text':text,'clear':True});assert r=='ok';await self.record({'op':'type','selector':selector,'text':'[private test input]'})
    async def wait(self,ms):await self.h.act({'op':'wait','ms':ms});await self.record({'op':'wait','ms':ms})
    async def act(self,a):assert await self.h.act(a)=='ok';await self.record(a)
    async def employee(self,id,pw,negative=False):
        if '员工' not in await self.h.page.locator('#login-title').inner_text():await self.click('#switch')
        await self.type('#username',id);await self.type('#password','invalid' if negative else pw);await self.click('button[onclick="login()"]',negative=negative)
    async def run(self,full,timed=False):
        await self.record({'op':'reset'});assert not self.j.checkpoints and not self.j.side
        await self.click('.start-btn')
        if full:
            await self.click('a[href="baoyahealth.html"]')
            m=re.search(r'user === "([^"]+)" && pass === "([^"]+)"',source('baoyahealth.html'))
            await self.type('#username',m[1]);await self.type('#password','invalid');await self.click('button[onclick="login()"]',negative=True)
            await self.type('#password',m[2]);await self.click('button[onclick="login()"]')
            await self.click('[data-target="page2"]');await self.click('button[onclick="openReal()"]');await self.click('button[onclick="fakeOption()"]',negative=True)
            await self.act({'op':'back'})
            employees=re.findall(r'"(\d+)": \{ password: "([^"]+)", page: "([^"]+)"',source('baoyahealth.html'))
            for id,pw,page in employees:
                await self.employee(id,pw,negative=True);await self.employee(id,pw)
                await self.h.page.screenshot(path=str(OUT/('full-'+page+'.png')))
                if page=='stafftian.html':
                    await self.click('[data-target="page2"]');await self.click('a[href="cv.html"]');await self.click('a[href="blog.html"]')
                    await self.act({'op':'close_tab','i':len(self.h.context.pages)-1});await self.act({'op':'close_tab','i':len(self.h.context.pages)-1})
                elif page=='staffyu.html':
                    await self.click('[data-target="page2"]',negative=True);await self.click('a[href="staffyujiamiyouxiang.html"]')
                    await self.type('#email-password','invalid');await self.click('#password-submit',negative=True)
                    await self.type('#email-password',val('staffyujiamiyouxiang.html','correctPassword'));await self.click('#password-submit')
                    for i in range(5):await self.click(f'.email-item[data-index="{i}"]');await self.click('#back-btn')
                    await self.act({'op':'back'})
                else:await self.click('[data-target="page2"]')
                await self.act({'op':'back'})
            await self.act({'op':'back'})
        await self.click('a[href="emailbox.html"]')
        await self.type('#email',val('emailbox.html','validEmail'));await self.type('#password','invalid');await self.click('button[type="submit"]',negative=True)
        await self.type('#password',val('emailbox.html','validPassword'));await self.click('button[type="submit"]')
        await self.click('a[href="wushan.html"]');await self.click('#openLogin');await self.click('#submitLogin',negative=True);await self.click('#stealthTrigger')
        await self.h.page.wait_for_load_state('domcontentloaded')
        await self.click('#btnCheck',negative=True)
        codes=ast.literal_eval(re.search(r'const correctSequence = (\[[^;]+\])',source('game1.js'))[1])
        if full:
            for code in reversed(codes):await self.click('.code:text-is('+json.dumps(code,ensure_ascii=False)+')')
            await self.click('#btnCheck',negative=True);await self.click('#btnReset')
        for code in codes:await self.click('.code:text-is('+json.dumps(code,ensure_ascii=False)+')')
        await self.click('#btnCheck');assert 'code_sequence' in self.j.checkpoints
        await self.wait(2300);await self.wait(5200)
        if full or timed:
            if timed:await self.wait(14500)
            else:await self.act({'op':'key','key':'Z'})
            await self.type('#keyInput','invalid');await self.click('#keySubmit',negative=True)
            secret=re.search(r"const correctPassword = '([^']+)'",source('script.js'))[1]
            await self.type('#keyInput',secret);await self.click('#keySubmit');assert 'caesar_key' in self.j.side
        else:
            sequence=re.search(r"const qteSequence = '([^']+)'",source('script.js'))[1]
            await self.h.act({'op':'type','text':sequence});await self.record({'op':'type','target':'QTE','text':'[private test input]'})
        await self.wait(1800);assert self.h.page.url.endswith('/choice.html')
        await self.click('button[onclick*="choice'+('2' if full else '1')+'.html"]')
        await self.wait(700);assert self.j.ending_reached
        assert len(self.j.checkpoints)==2
        assert len(self.j.side)==(6 if full else 1 if timed else 0),self.j.score()
        assert bool(self.j.events)==(not full and not timed)
        await self.h.page.screenshot(path=str(OUT/(('ending-dawn' if full else 'ending-sacrifice')+'.png')))
        return {'path':'all_optional_wrong_key_caesar_dawn' if full else 'minimal_timeout_caesar_sacrifice' if timed else 'minimal_qte_sacrifice','visited_pages':sorted(self.pages),'negative_checks':self.negative,'score':self.j.score(),'trace':self.trace}

async def main():
    OUT.mkdir(parents=True,exist_ok=True);c=load_config(ROOT/'configs/baoya.json');c['entry_url']=f'http://127.0.0.1:{args.port}/index.html';c['allow_hosts']=[f'127.0.0.1:{args.port}'];c['local_serve'].update(port=args.port,ready_url=c['entry_url']);c['local_serve']['command'][-1]=str(args.port)
    s=LocalServer();h=BrowserHarness(c,OUT);report={'deployment_root':str(ROOT),'kind':'engineering_acceptance_not_model_score','branches':[],'page_errors':[],'http_errors':[]}
    try:
        s.start(c,ROOT,OUT/'server.log');await h.start()
        for full,timed in [(True,False),(False,False),(False,True)]:
            await h.reset();h.context.on('page',lambda page:page.on('pageerror',lambda e:report['page_errors'].append(str(e))));h.page.on('pageerror',lambda e:report['page_errors'].append(str(e)));h.context.on('response',lambda r:report['http_errors'].append({'url':r.url,'status':r.status}) if r.status>=400 else None)
            report['branches'].append(await Replay(h).run(full,timed))
        assert not report['page_errors'],report['page_errors'];assert not report['http_errors'],report['http_errors'];assert not h.blocked,h.blocked
        assert report['branches'][0]['score']['route_progress']==1.0 and report['branches'][1]['score']['route_progress']==1.0
        assert len(set(p for b in report['branches'] for p in b['visited_pages']))==18
        report['pass']=True
    except Exception as e:
        report['failure']=str(e)
        if h.page:await h.page.screenshot(path=str(OUT/'failure.png'))
        raise
    finally:
        (OUT/'acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();s.stop()
    print('BAOYA ACCEPTANCE PASS',flush=True)

if __name__=='__main__':asyncio.run(main())
