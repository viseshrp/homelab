"""Offline tests for the private ntfy deployment and Kuma integration."""

import importlib.util
import json
from pathlib import Path
import re
import stat
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generator = load_module(
    'ntfy_generate_private', ROOT / 'configs/ntfy/generate-private.py')
notification = load_module(
    'kuma_reconcile_notification',
    ROOT / 'configs/uptime-kuma/reconcile-notification.py')


class NtfyTests(unittest.TestCase):
    def test_compose_uses_private_auth_and_the_latest_image_tag(self):
        compose = (ROOT / 'docker-compose/ntfy/docker-compose.yml').read_text()
        example = (ROOT / 'docker-compose/ntfy/.env.example').read_text()
        self.assertIn('NTFY_AUTH_DEFAULT_ACCESS: "deny-all"', compose)
        self.assertIn('NTFY_ENABLE_SIGNUP: "false"', compose)
        self.assertIn('NTFY_BEHIND_PROXY: "true"', compose)
        self.assertIn('NTFY_UPSTREAM_BASE_URL', compose)
        self.assertNotIn('NTFY_ATTACHMENT_CACHE_DIR', compose)
        self.assertIn('NTFY_IMAGE=binwiederhier/ntfy:latest', example)

    def test_generator_separates_server_and_mobile_secrets(self):
        fake_hash = '$2y$12$' + ('a' * 53)

        def hasher(_password, _username):
            return fake_hash

        with tempfile.TemporaryDirectory() as directory:
            paths = generator.generate(
                Path(directory) / 'private', 'https://ntfy.example.test',
                '10.0.0.4', password_hasher=hasher)
            compose_env = paths['compose_env'].read_text()
            mobile = paths['mobile'].read_text()
            kuma = paths['kuma'].read_text()
            password = next(line.split(': ', 1)[1] for line in mobile.splitlines()
                            if line.startswith('Password: '))
            topic = next(line.split(': ', 1)[1] for line in mobile.splitlines()
                         if line.startswith('Topic: '))
            token = next(line.split('=', 1)[1] for line in kuma.splitlines()
                         if line.startswith('UPTIME_KUMA_NTFY_ACCESS_TOKEN='))
            self.assertIn(
                'NTFY_IMAGE=binwiederhier/ntfy:latest', compose_env)
            self.assertNotIn(password, compose_env)
            self.assertIn(f'kuma-publisher:{topic}:wo', compose_env)
            self.assertIn(f'mobile-subscriber:{topic}:ro', compose_env)
            self.assertRegex(token, r'^tk_[a-z0-9]{29}$')
            for path in paths.values():
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_generator_refuses_non_https_and_public_bind_addresses(self):
        with self.assertRaisesRegex(ValueError, 'HTTPS'):
            generator.validate_base_url('http://ntfy.example.test')
        with self.assertRaisesRegex(ValueError, 'private'):
            generator.validate_bind_ip('8.8.8.8')

    def test_kuma_notification_policy_resolves_without_committed_secrets(self):
        policy = json.loads(
            (ROOT / 'configs/uptime-kuma/notification.json').read_text())
        environment = notification.read_env(
            ROOT / 'docker-compose/uptime-kuma/.env.example')
        resolved = notification.resolve_policy(
            policy, environment, allow_placeholders=True)
        self.assertEqual(resolved['type'], 'ntfy')
        self.assertEqual(resolved['ntfyAuthenticationMethod'], 'accessToken')
        self.assertTrue(re.fullmatch(
            r'tk_[a-z0-9]{29}', resolved['ntfyaccesstoken']))

    def test_deployment_assets_cover_private_generation_and_kuma_cutover(self):
        manifest = json.loads((ROOT / 'deployments.json').read_text())
        self.assertEqual(manifest['ntfy'], {
            'host': 'rpimon',
            'directory': '/opt/ntfy',
            'compose': 'docker-compose.yml',
            'assets': {
                'configs/ntfy/add-diun-publishers.py': 'add-diun-publishers.py',
                'configs/ntfy/add-scrutiny-publisher.py': 'add-scrutiny-publisher.py',
                'configs/ntfy/generate-private.py': 'generate-private.py',
            },
        })
        self.assertIn(
            'configs/uptime-kuma/reconcile-notification.py',
            manifest['uptime-kuma']['assets'])


if __name__ == '__main__':
    unittest.main()
