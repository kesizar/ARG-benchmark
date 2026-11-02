"""Check existing player actions against a real canvas game; no game-state injection."""
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.browser_harness import BrowserHarness
from harness.actions import normalize

OUT = ROOT / 'data/discovery/english-community/canvas-deductopia-probe'
OUT.mkdir(parents=True, exist_ok=True)
cfg = {'id': 'canvas-probe', 'obs_mode': 'B', 'obs_text': True, 'obs_elements': True,
       'entry_url': 'https://html.itch.zone/html/12384341/Web/index.html',
       'viewport': {'width':1280,'height':900}, 'allow_hosts':['html.itch.zone'],
       'actions_enabled':['click','drag','key','wait'], 'settle_ms':500}

async def main():
    h = BrowserHarness(cfg, OUT)
    try:
        await h.start(); await h.reset()
        await h.page.wait_for_timeout(30000)
        await h.observe('before.png')
        action, err = normalize({'op':'click','x':835,'y':465}, cfg)
        if err: raise ValueError(err)
        result = await h.act(action)
        await h.page.wait_for_timeout(3000)
        await h.observe('after.png')
        drag, err = normalize({'op':'drag','x1':100,'y1':298,'x2':550,'y2':200}, cfg)
        if err: raise ValueError(err)
        drag_result = await h.act(drag)
        await h.observe('after-drag.png')
        reset, err = normalize({'op':'click','x':1175,'y':130}, cfg)
        if err: raise ValueError(err)
        reset_result = await h.act(reset)
        await h.observe('after-reset.png')
        (OUT / 'probe.json').write_text(json.dumps({'click':action,'click_result':result,'drag':drag,
            'drag_result':drag_result,'reset':reset,'reset_result':reset_result,'blocked':h.blocked},ensure_ascii=False,indent=2),encoding='utf8')
        print(json.dumps({'click_result':result,'drag_result':drag_result,'reset_result':reset_result,'blocked':h.blocked},ensure_ascii=False))
    finally:
        await h.close()

asyncio.run(main())
