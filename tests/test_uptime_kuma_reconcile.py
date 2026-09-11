"""Offline tests for the declarative Uptime Kuma monitor workflow."""

import copy
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / 'configs/uptime-kuma/reconcile.py'
SPEC = importlib.util.spec_from_file_location('uptime_kuma_reconcile', MODULE_PATH)
reconcile = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reconcile)


class UptimeKumaReconcileTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads(
            (ROOT / 'configs/uptime-kuma/monitors.json').read_text())
        self.environment = reconcile.read_env(
            ROOT / 'docker-compose/uptime-kuma/.env.example')

    def test_policy_resolves_sanitized_targets_from_private_inputs(self):
        resolved = reconcile.resolve_policy(
            self.policy, self.environment, allow_placeholders=True)
        monitors = {item['name']: item for item in resolved['monitors']}
        self.assertEqual(monitors['Anki']['url'],
                         'https://anki.example.com/health')
        self.assertEqual(monitors['ArchiveBox']['hostname'], '192.0.2.14')
        self.assertEqual(monitors['ArchiveBox']['port'], 8002)
        self.assertEqual(monitors['Pi-hole Blocking']['resolver'], '192.0.2.13')
        self.assertEqual(monitors['Pi-hole Blocking']['record_type'], 'CNAME')
        self.assertTrue(monitors['Pi-hole Blocking']['expected_failure'])

    def test_apply_resolution_refuses_documentation_placeholders(self):
        with self.assertRaisesRegex(ValueError, 'placeholder'):
            reconcile.resolve_policy(self.policy, self.environment)

    def test_status_page_contains_every_monitor_once(self):
        reconcile.validate_policy(self.policy)
        expected = {item['name'] for item in self.policy['monitors']}
        grouped = [name for group in self.policy['status_page']['groups']
                   for name in group['monitors']]
        self.assertEqual(set(grouped), expected)
        self.assertEqual(len(grouped), len(expected))

    def test_duplicate_previous_name_is_rejected(self):
        broken = copy.deepcopy(self.policy)
        broken['previous_names']['Anki'].append('pass')
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            reconcile.validate_policy(broken)

    def test_reconcile_assets_are_in_the_deployment_payload(self):
        manifest = json.loads((ROOT / 'deployments.json').read_text())
        self.assertEqual(manifest['uptime-kuma']['assets'], {
            'configs/uptime-kuma/monitors.json': 'monitors.json',
            'configs/uptime-kuma/reconcile.py': 'reconcile.py',
        })


if __name__ == '__main__':
    unittest.main()
