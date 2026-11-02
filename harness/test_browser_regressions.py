"""Player-action regressions found during real-game preparation. No APIs."""
import asyncio
import tempfile
import unittest
from pathlib import Path

from harness.browser_harness import BrowserHarness
from harness.config import apply_defaults, apply_obs_mode


class BrowserRegressionTests(unittest.TestCase):
    def test_judge_init_runs_in_new_context_and_child_frame(self):
        asyncio.run(self._judge_init())

    async def _judge_init(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg=apply_obs_mode(apply_defaults({'category':'web_puzzle','runtime_layer':'L1','settle_ms':10}))
            h=BrowserHarness(cfg,Path(tmp))
            h.judge_init_script='window.__judge_test = 7'
            try:
                await h.start();await h.reset()
                await h.page.set_content('<iframe srcdoc="<p>child</p>"></iframe>')
                await h.page.wait_for_timeout(100)
                self.assertTrue(await h.page_expr('window.__judge_test === 7'))
                self.assertEqual(await h.page.frames[1].evaluate('window.__judge_test'),7)
                await h.page.evaluate('window.__judge_test = 99')
                await h.reset()
                self.assertEqual(await h.page.evaluate('window.__judge_test'),7)
            finally:await h.close()

    def test_numbered_click_hits_wrapped_inline_text(self):
        asyncio.run(self._wrapped())

    async def _wrapped(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg=apply_obs_mode(apply_defaults({'category':'web_puzzle','runtime_layer':'L1','obs_mode':'B','settle_ms':10}))
            h=BrowserHarness(cfg,Path(tmp))
            try:
                await h.start();await h.reset()
                await h.page.set_content('''<style>body{font:20px monospace}div{width:150px;line-height:30px}</style>
                    <div>AAAAAAA <a id="link" href="#clicked">wrapped inline link with many words</a></div>''')
                fragments=await h.page.locator('#link').evaluate('(n)=>Array.from(n.getClientRects()).map(r=>({x:r.x,y:r.y,w:r.width,h:r.height}))')
                self.assertGreater(len(fragments),1)
                obs=await h.observe()
                link=next(e for e in obs['elements'] if 'wrapped inline link' in e['label'])
                result=await h.act({'op':'click','n':link['n']})
                self.assertEqual(result,'ok');self.assertTrue(h.page.url.endswith('#clicked'))
            finally:await h.close()

    def test_selected_tab_survives_next_action_and_closed_tab_falls_back(self):
        asyncio.run(self._tabs())

    async def _tabs(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg=apply_obs_mode(apply_defaults({'category':'web_puzzle','runtime_layer':'L1','settle_ms':10}))
            h=BrowserHarness(cfg,Path(tmp))
            try:
                await h.start();await h.reset()
                first=h.page
                await first.set_content('<input id="value"><button onclick="document.body.dataset.clicked=1">OK</button>')
                second=await h.context.new_page()
                await second.set_content('<p>second tab</p>')
                await h.act({'op':'switch_tab','i':0})
                await first.locator('#value').focus()
                await h.act({'op':'type','text':'retained tab'})
                self.assertIs(h.page,first)
                self.assertEqual(await first.locator('#value').input_value(),'retained tab')
                obs=await h.observe()
                button=next(e for e in obs['elements'] if e['label']=='OK')
                await h.act({'op':'click','n':button['n']})
                self.assertEqual(await first.get_attribute('body','data-clicked'),'1')
                self.assertIs(h.page,first)
                await first.close();await h._drop_blocked_pages()
                self.assertIs(h.page,second)
            finally:await h.close()


class NativeDialogTests(unittest.TestCase):
    def test_prompt_yields_and_keeps_observation_and_judge_responsive(self):
        asyncio.run(self._prompt())

    async def _prompt(self):
        from harness.judge import Judge
        with tempfile.TemporaryDirectory() as tmp:
            cfg=apply_obs_mode(apply_defaults({'category':'web_puzzle','runtime_layer':'L1','settle_ms':10}))
            h=BrowserHarness(cfg,Path(tmp))
            try:
                await h.start();await h.reset()
                await h.page.set_content("""<p>before</p><button onclick="document.body.dataset.result=prompt('code')">Ask</button>""")
                before=await h.observe()
                j=Judge({'hooks':{'screen':{'type':'dom_regex','pattern':'before'},
                    'result':{'type':'js_truthy','expr':"document.body.dataset.result === 'answer'"}},
                    'checkpoints':[{'id':'result','hook':'result'}]},'sample')
                await j.read(h);j.update(0)
                button=next(e for e in before['elements'] if e['label']=='Ask')
                result=await asyncio.wait_for(h.act({'op':'click','n':button['n']}),5)
                self.assertEqual(result,'ok');self.assertIsNotNone(h.pending)
                pending=await asyncio.wait_for(h.observe(),3)
                self.assertEqual(pending['pending_dialog']['type'],'prompt')
                self.assertEqual(pending['elements'],[])
                self.assertEqual(pending['screenshot'],before['screenshot'])
                await asyncio.wait_for(j.read(h),3);j.update(1)
                self.assertTrue(j.values['screen']);self.assertEqual(j.score()['checkpoints_reached'],0)
                self.assertEqual(await asyncio.wait_for(h.act({'op':'click','x':1,'y':1}),3),
                                 '请先用 dialog 动作处理待回应的对话框')
                self.assertEqual(await asyncio.wait_for(h.act({'op':'dialog','accept':True,'text':'answer'}),5),'ok')
                await j.read(h);j.update(2)
                self.assertEqual(j.score()['checkpoints_reached'],1)
                self.assertIsNone((await h.observe())['pending_dialog'])
                self.assertEqual(len(h.step_dialogs),1)
            finally:await h.close()

    def test_confirm_cancel_nested_prompt_alert_and_reset(self):
        asyncio.run(self._other_dialogs())

    async def _other_dialogs(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg=apply_obs_mode(apply_defaults({'category':'web_puzzle','runtime_layer':'L1','settle_ms':10}))
            h=BrowserHarness(cfg,Path(tmp))
            try:
                await h.start();await h.reset()
                await h.page.set_content("""<button onclick="document.body.dataset.result=String(confirm('sure'))">Confirm</button>""")
                b=await h.page.locator('button').bounding_box()
                click={'op':'click','x':b['x']+b['width']/2,'y':b['y']+b['height']/2}
                await asyncio.wait_for(h.act(click),5)
                await asyncio.wait_for(h.act({'op':'dialog','accept':False}),5)
                self.assertEqual(await h.page.get_attribute('body','data-result'),'false')
                await h.page.set_content("""<button onclick="prompt('first');prompt('second');document.body.dataset.done=1">Two</button>""")
                await asyncio.wait_for(h.act(click),5)
                self.assertEqual(h.pending.message,'first')
                await asyncio.wait_for(h.act({'op':'dialog','accept':True,'text':'one'}),5)
                self.assertEqual(h.pending.message,'second')
                await asyncio.wait_for(h.act({'op':'dialog','accept':False}),5)
                self.assertEqual(await h.page.get_attribute('body','data-done'),'1')
                await h.page.set_content("""<button onclick="alert('notice');document.body.dataset.done=1">Alert</button>""")
                await asyncio.wait_for(h.act(click),5)
                self.assertIsNone(h.pending)
                self.assertEqual(await h.page.get_attribute('body','data-done'),'1')
                await h.page.set_content("""<button onclick="prompt('pending reset')">Reset</button>""")
                await asyncio.wait_for(h.act(click),5)
                await asyncio.wait_for(h.reset(),5)
                self.assertIsNone(h.pending)
                self.assertFalse(h._action_tasks)
            finally:await h.close()
