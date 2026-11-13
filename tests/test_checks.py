"""Consumer-visible outcomes and evidence, including missing-hook false-pass guards."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReliabilityChecks(unittest.TestCase):
    def run_check(self, target):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'evidence.json'
            process = subprocess.run([sys.executable, str(ROOT / 'check'), str(target),
                                      '--output', str(output)], capture_output=True, text=True,
                                     timeout=20)
            self.assertTrue(output.exists(), process.stderr)
            return process.returncode, json.loads(output.read_text())

    def test_known_vulnerabilities_are_reproduced(self):
        code, report = self.run_check(ROOT / 'reference')
        self.assertEqual(code, 1)
        results = report['results']
        self.assertEqual([r['outcome'] for r in results], ['failure reproduced'] * 3)
        self.assertTrue(results[0]['evidence']['monitor_healthy'])
        self.assertEqual(results[1]['evidence']['total_cost_units'], 10)
        self.assertEqual(results[2]['evidence']['effects_after_replay'], ['order-1', 'order-1'])

    def test_independent_workflow_controls_hold_after_actual_restart(self):
        code, report = self.run_check(ROOT / 'sample')
        self.assertEqual(code, 0)
        results = report['results']
        self.assertEqual([r['outcome'] for r in results], ['check held under tested conditions'] * 3)
        self.assertTrue(results[0]['evidence']['process_alive'])
        self.assertFalse(results[0]['evidence']['monitor_healthy'])
        self.assertEqual(results[1]['evidence']['charges_by_run'], {'first': 2, 'second': 1})
        self.assertEqual(results[2]['evidence']['effects_after_replay'], ['order-1'])

    def model_config(self, directory):
        config = json.loads((ROOT / 'reference/adapter.json').read_text())
        config['sources'] = ['adapter.json', str(ROOT / 'model.py')]
        path = Path(directory) / 'adapter.json'
        return config, path

    def test_missing_stall_hook_is_inconclusive_not_healthy(self):
        with tempfile.TemporaryDirectory() as temp:
            config, path = self.model_config(temp)
            del config['steps']['stall']
            path.write_text(json.dumps(config))
            code, report = self.run_check(path)
        self.assertEqual(code, 2)
        self.assertEqual(report['results'][0]['outcome'], 'inconclusive')
        self.assertIn('capabilities', report['results'][0]['reason'])
        self.assertEqual(report['results'][2]['outcome'], 'failure reproduced')

    def test_unexercised_billing_is_not_a_held_check(self):
        with tempfile.TemporaryDirectory() as temp:
            config, path = self.model_config(temp)
            config['steps']['attempt'] = []
            path.write_text(json.dumps(config))
            code, report = self.run_check(path)
        self.assertEqual(code, 2)
        self.assertEqual(report['results'][1]['outcome'], 'inconclusive')
        self.assertIn('no billable attempts', report['results'][1]['reason'])

    def test_missing_effect_before_crash_is_not_a_held_check(self):
        with tempfile.TemporaryDirectory() as temp:
            config, path = self.model_config(temp)
            config['steps']['deliver'] = [{'action': 'checkpoint'}]
            path.write_text(json.dumps(config))
            code, report = self.run_check(path)
        self.assertEqual(code, 2)
        self.assertEqual(report['results'][2]['outcome'], 'inconclusive')
        self.assertIn('precondition', report['results'][2]['reason'])


if __name__ == '__main__':
    unittest.main()
