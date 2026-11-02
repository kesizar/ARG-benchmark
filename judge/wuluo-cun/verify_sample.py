"""Auditor-only UI replay. Never import this into a model policy or serve it.

Reads source-derived solutions, but advances only with real mouse clicks via
BrowserHarness.act. No state injection, function calls, or direct scene jumps.
The output is engineering acceptance evidence, never a model benchmark score.
"""
from __future__ import annotations
import asyncio
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description="裁判侧完整 UI 验收")
parser.add_argument("--root", type=Path, default=ROOT)
parser.add_argument("--port", type=int, default=8788)
args = parser.parse_args()
ROOT = args.root.resolve()
sys.path.insert(0, str(ROOT))
from harness.browser_harness import BrowserHarness
from harness.config import load_config
from harness.judge import Judge
from harness.serve_local import LocalServer

OUT = ROOT / "judge/wuluo-cun/verification"


class Replay:
    def __init__(self, h, judge, negatives):
        self.h, self.judge, self.negatives = h, judge, negatives
        self.steps = []; self.visited = []; self.negative_checks = []

    async def record(self, action):
        await self.judge.read(self.h)
        fresh = self.judge.update(len(self.steps) + 1)
        self.steps.append({"action": action, "new": fresh, "score": self.judge.score()})
        self.h.consume_step()

    async def click(self, selector, negative=False):
        before = set(self.judge.checkpoints)
        loc = self.h.page.locator(selector).first
        await loc.wait_for(state="visible", timeout=12000)
        await loc.scroll_into_view_if_needed()
        await loc.click(trial=True, timeout=12000)
        box = await loc.bounding_box()
        assert box, selector
        result = await self.h.act({"op": "click", "x": box["x"] + box["width"]/2, "y": box["y"] + box["height"]/2})
        assert result == "ok", (selector, result)
        await self.record({"op":"click", "selector":selector})
        if negative:
            assert before == set(self.judge.checkpoints), f"Wrong action earned progress: {selector}"
            assert not self.judge.ending_reached
            self.negative_checks.append(selector)

    async def wait(self, ms=1600):
        await self.h.act({"op":"wait", "ms":ms})
        await self.record({"op":"wait", "ms":ms})

    async def modal_close(self):
        await self.click('#itemModal .item-modal-actions button')

    async def puzzle(self, scene):
        n = self.negatives
        if scene == 'act1_2':
            if n:
                for item in ['photo','basket','thimble','box','calendar','window','door','drawer','lamp','shelf','mirror']:
                    await self.click(f'[onclick="examineItem(\'{item}\')"]', negative=True)
                    await self.modal_close()
            await self.click('[onclick="examineItem(\'papercut\')"]'); await self.modal_close()
            await self.click('[onclick="examineItem(\'basket\')"]'); await self.modal_close()
            if n:
                await self.click('#dirCCW'); await self.click('#twistBtn',negative=True)
            await self.click('#dirCW')
            for _ in range(3): await self.click('#twistBtn')
            await self.wait(950); await self.modal_close()
        elif scene == 'act2_1d':
            if n:
                for item in ['counter','shelf1','shelf2','shelf3','backroom','wall','crack']:
                    await self.click(f'[onclick="shopSearch(\'{item}\')"]',negative=True); await self.modal_close()
            await self.click('[onclick="shopSearch(\'floor\')"]'); await self.modal_close()
            await self.wait(2500)
        elif scene == 'act2_2':
            if n: await self.click('[onclick="combineStep1(\'back\')"]',negative=True)
            await self.click('[onclick="combineStep1(\'front\')"]')
            if n: await self.click('[onclick="combineStep2(\'left\')"]',negative=True)
            await self.click('[onclick="combineStep2(\'right\')"]')
            await self.click('[onclick="combineStep3()"]')
        elif scene == 'act2_4':
            if n:
                for item in ['mill','tree']: await self.click(f'[onclick="trackFoot(\'{item}\')"]',negative=True)
            for item in ['well','mill','tree']: await self.click(f'[onclick="trackFoot(\'{item}\')"]')
        elif scene == 'act3_2':
            if n:
                for _ in range(8): await self.click('[onclick="codeInput(0)"]',negative=True)
                await self.wait(500); await self.click('[onclick="codeClear()"]')
            # Read the archived program only on the auditor side.
            src=(ROOT/'tasks/wuluo-cun/mirror/index.html').read_text(encoding='utf-8')
            answer=re.search(r"if\(code === '([0-9]+)'\)",src)[1]
            for digit in answer: await self.click(f'[onclick="codeInput({digit})"]')
        elif scene == 'act3_2b':
            if n:
                for i in range(1,6):
                    await self.click(f'#d{i}'); await self.click(f'#slot{(i%5)+1}',negative=True)
            for i in range(1,6):
                await self.click(f'#d{i}'); await self.click(f'#slot{i}')
            await self.wait(3800)
        elif scene == 'act4_2':
            if n:
                await self.click('.stone[data-num="1"]',negative=True); await self.wait(1400)
            src=(ROOT/'tasks/wuluo-cun/mirror/index.html').read_text(encoding='utf-8')
            order=json.loads('['+re.search(r'window.stoneCorrect = \[([^]]+)\]',src)[1]+']')
            for i in order: await self.click(f'.stone[data-num="{i}"]')
        elif scene == 'act4_4':
            if n:
                for d in ['left','right']: await self.click(f'[onclick="navigate(\'{d}\')"]',negative=True)
            for _ in range(3): await self.click('[onclick="navigate(\'center\')"]')
        elif scene == 'act5_2':
            if n:
                for item in ['gun','name']:
                    await self.click(f'#cv-{item}',negative=True); await self.wait(1400)
            for item in ['needle','gun','name']: await self.click(f'#cv-{item}')
        elif scene == 'act5_2b':
            for q, right in enumerate([1,2,3]):
                if n:
                    for wrong in range(4):
                        if wrong!=right: await self.click(f'[onclick="spiritAnswer({wrong})"]',negative=True)
                await self.click(f'[onclick="spiritAnswer({right})"]')
                await self.wait(2800 if q<2 else 5600)
        elif scene == 'act6_1c':
            # Cover all 20 wrong pairings before filling the five correct pairs.
            if n:
                for i in range(1,6):
                    for j in range(1,6):
                        if i!=j:
                            await self.click(f'#c{i}'); await self.click(f'#m{j}',negative=True)
            for i in range(1,6): await self.click(f'#c{i}'); await self.click(f'#m{i}')
            await self.wait(3800)
        else:
            raise AssertionError('Uncovered puzzle scene: '+scene)
        await self.h.page.locator('#puzzle-next button').wait_for(state='visible',timeout=12000)
        await self.record({'op':'checkpoint_before_navigation'})
        await self.click('#puzzle-next button')

    async def run(self, ending):
        await self.record({'op':'reset'})
        assert not self.judge.checkpoints and not self.judge.ending_reached
        while True:
            await self.wait(900)
            scene=await self.h.page.evaluate('gameState.currentScene')
            kind=await self.h.page.evaluate('id => scenes[id].type',scene)
            if scene not in self.visited:
                self.visited.append(scene)
                print(ending,scene,'points',len(self.judge.checkpoints),flush=True)
                if kind in ['cover','puzzle','ending','choice']:
                    await self.h.page.screenshot(path=str(OUT/f'{ending}-{scene}.png'),animations='disabled')
            if kind=='ending':
                await self.record({'op':'ending_observation'})
                assert scene=='ending_'+ending
                assert len(self.judge.checkpoints)==21
                assert self.judge.ending_reached
                break
            if kind=='puzzle': await self.puzzle(scene)
            elif kind=='choice': await self.click(f'[onclick="renderScene(\'ending_{ending}\')"]')
            elif kind=='cover': await self.click('.cover-btn')
            else: await self.click(f'#scene-{scene} .btn-row button')
        return {'ending':ending,'visited':self.visited,'recorded_steps':len(self.steps),'ui_actions':sum(s['action']['op']=='click' for s in self.steps),'negative_checks':len(self.negative_checks),'score':self.judge.score(),'steps':self.steps,'negative_selectors':self.negative_checks}


async def main():
    OUT.mkdir(parents=True,exist_ok=True)
    cfg=load_config(ROOT/'configs/wuluo-cun.json')
    cfg['entry_url']=f'http://127.0.0.1:{args.port}/index.html'
    cfg['allow_hosts']=[f'127.0.0.1:{args.port}']
    cfg['local_serve'].update({'port':args.port,'ready_url':cfg['entry_url']})
    command=cfg['local_serve']['command']
    command[command.index('--port')+1]=str(args.port)
    cfg['settle_ms']=350
    server=LocalServer(); h=BrowserHarness(cfg,OUT)
    report={'kind':'engineering_acceptance_not_model_score','deployment_root':str(ROOT),'entry_url':cfg['entry_url'],'branches':[],'errors':[],'http_errors':[]}
    try:
        server.start(cfg,ROOT,OUT/'server.log'); await h.start()
        for ending in ['a','b']:
            await h.reset()
            h.context.on('response',lambda r: report['http_errors'].append({'url':r.url,'status':r.status}) if r.status>=400 else None)
            h.page.on('pageerror',lambda e: report['errors'].append(str(e)))
            graph=await h.page.evaluate("Object.entries(scenes).map(([id,s])=>({id,type:s.type,title:s.title||'封面',next:s.next||null,choices:(s.choices||[]).map(c=>({text:c.text,next:c.next})),image:s.img||null}))")
            (ROOT/'judge/wuluo-cun/flow.json').write_text(json.dumps({'scenes':graph},ensure_ascii=False,indent=2),encoding='utf-8')
            judge=Judge.load(ROOT/cfg['judge_path'],'wuluo-cun',ROOT)
            replay=Replay(h,judge,ending=='a')
            report['branches'].append(await replay.run(ending))
        report['scene_count']=len(graph)
        report['covered_scene_count']=len(set(x for b in report['branches'] for x in b['visited']))
        assert report['covered_scene_count']==report['scene_count']
        assert not report['http_errors'] and not report['errors']
        report['pass']=True
    except Exception as exc:
        report['failure']=str(exc)
        if h.page:
            await h.page.screenshot(path=str(OUT/'failure.png'))
        raise
    finally:
        (OUT/'acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        await h.close(); server.stop()
    print('ACCEPTANCE PASS',report['scene_count'],'scenes',flush=True)


if __name__=='__main__': asyncio.run(main())
