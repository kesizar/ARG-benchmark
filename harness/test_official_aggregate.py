import json
import tempfile
import unittest
from pathlib import Path
from harness.summary import aggregate

class OfficialAggregateTests(unittest.TestCase):
    def test_only_valid_official_runs_are_counted_and_exclusions_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = {'task_id':'game', 'category':'arg', 'runtime_layer':'L1', 'obs_mode':'B',
                    'model':{'provider':'openai','name':'model'}, 'run_kind':'official',
                    'judge_error':None, 'ended_reason':'ending', 'ending_reached':True, 'progress':1}
            cases = {'valid':{}, 'failure':{'ended_reason':'failure','ending_reached':False,'failure_reached':True},
                     'test':{'run_kind':'test'}, 'error':{'ended_reason':'error'},
                     'judge':{'judge_error':'missing'}, 'old':{'run_kind':None},
                     'script':{'model':{'provider':'script'}}, 'unknown':{'ended_reason':'mystery'}}
            for name, change in cases.items():
                folder = root / 'game' / 'B' / name
                folder.mkdir(parents=True)
                (folder / 'summary.json').write_text(json.dumps(base | change), encoding='utf-8')
            (root / 'game' / 'B' / 'incomplete').mkdir()
            folder = root / 'game' / 'B' / 'broken'
            folder.mkdir()
            (folder / 'summary.json').write_text('{', encoding='utf-8')
            excluded = []
            rows = aggregate(root, official_only=True, exclusions=excluded)
            self.assertEqual(rows[0]['runs'], 2)
            self.assertEqual(rows[0]['endings_rate'], 0.5)
            self.assertEqual({x['reason'] for x in excluded}, {'test_run','runtime_error','judge_error',
                'unclassified_run','invalid_model','unknown_end_reason','missing_summary','unreadable_summary'})

if __name__ == '__main__':
    unittest.main()
