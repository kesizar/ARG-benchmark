"""Offline tests for using the shared harness with an extracted evaluator."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import run_external_bundle
from harness.loop import run


class ExternalBundleLauncherTests(unittest.TestCase):
    def test_extracted_root_config_and_manifest_are_passed_to_shared_harness(self):
        parent = Path(__file__).resolve().parents[1] / 'data' / 'preparation'
        with tempfile.TemporaryDirectory(dir=parent) as name:
            root = Path(name)
            config = root / 'configs' / 'task.json'
            config.parent.mkdir()
            config.write_text('{}', encoding='utf8')
            manifest = root / 'manifest.json'
            manifest.write_text(json.dumps({'id': 'sample'}), encoding='utf8')
            calls = []

            def fake_run(path, **kwargs):
                calls.append((path, kwargs))
                return object()

            with patch.object(run_external_bundle, 'run', fake_run), patch.object(run_external_bundle.asyncio, 'run', return_value={'ended_reason': 'give_up'}):
                status = run_external_bundle.main(['--bundle-root', str(root), '--config', 'configs/task.json',
                                                   '--policy', 'llm', '--run-kind', 'official', '--manifest', str(manifest),
                                                   '--repetition', '1'])
            self.assertEqual(status, 0)
            self.assertEqual(calls[0][0], config.resolve())
            self.assertEqual(calls[0][1]['repo_root'], root.resolve())
            self.assertEqual(calls[0][1]['manifest'], {'id': 'sample'})
            self.assertEqual(calls[0][1]['run_kind'], 'official')

    def test_official_script_run_rejected_before_io_or_network(self):
        coroutine = run('missing-config', policy='script', run_kind='official')
        try:
            with self.assertRaisesRegex(ValueError, '正式评测必须使用 llm'):
                coroutine.send(None)
        finally:
            coroutine.close()

    def test_config_cannot_escape_extracted_bundle(self):
        parent = Path(__file__).resolve().parents[1] / 'data' / 'preparation'
        with tempfile.TemporaryDirectory(dir=parent) as name:
            with self.assertRaises(SystemExit):
                run_external_bundle.main(['--bundle-root', name, '--config', '../progress.json'])


if __name__ == '__main__':
    unittest.main()
