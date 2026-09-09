"""No network, Docker daemon, or host firewall access in these tests."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'configs/fail2ban/data/scripts'))
import prepare
import integration
import source_firewall


class PreparationTests(unittest.TestCase):
    def test_existing_directory_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            existing = Path(tmp) / 'npm'
            existing.mkdir()
            state = existing / '.env'
            state.write_text('PRIVATE=value\n')
            with self.assertRaises(FileExistsError):
                prepare.prepare('npm', existing)
            self.assertEqual(state.read_text(), 'PRIVATE=value\n')

    def test_nginx_includes_are_assembled(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = prepare.prepare('npm', Path(tmp) / 'nginx')
            self.assertTrue((out / 'nginx.conf').exists())
            self.assertTrue((out / 'data/nginx/custom/cloudflare-trusted.conf').exists())
            self.assertFalse((out / '.env').exists())

    def test_unknown_project_creates_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                prepare.prepare('../escape', Path(tmp) / 'new')
            self.assertEqual(list(Path(tmp).iterdir()), [])


class FirewallTests(unittest.TestCase):
    def test_private_and_owner_addresses_are_protected(self):
        config = {'protected_networks': ['8.8.8.0/24']}
        for ip in ['127.0.0.1', '10.1.2.3', '::1', 'fd00::1', '8.8.8.8']:
            self.assertTrue(integration.protected(ip, config))
        self.assertFalse(integration.protected('1.1.1.1', config))

    def test_protected_ban_never_calls_firewall(self):
        with patch.object(source_firewall, 'settings', return_value={'protected_networks': []}), \
             patch.object(source_firewall, 'run') as run, \
             patch.object(sys, 'argv', ['source_firewall.py', 'ban', '10.0.0.1']):
            source_firewall.main()
            run.assert_not_called()

    def test_unban_uses_exact_ip_and_family(self):
        config = {'protected_networks': [], 'set_prefix': 'test-', 'ports': '80,443'}
        with patch.object(source_firewall, 'settings', return_value=config), \
             patch.object(source_firewall, 'ensure'), \
             patch.object(source_firewall, 'run') as run, \
             patch.object(sys, 'argv', ['source_firewall.py', 'unban', '2606:4700:4700::1111']):
            source_firewall.main()
            run.assert_called_once_with(['ipset', 'del', 'test-6', '2606:4700:4700::1111', '-exist'])


class UpdateTests(unittest.TestCase):
    def test_default_preview_never_executes_docker(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / 'project with spaces'
            project.mkdir()
            (project / 'docker-compose.yml').write_text('services: {}\n')
            result = subprocess.run(['bash', str(ROOT / 'docker-compose/update-all.sh'), str(project)],
                                    text=True, capture_output=True, env={'PATH': '/usr/bin:/bin'})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('docker compose config --quiet', result.stdout)
            self.assertNotIn('prune', result.stdout)

    def test_no_implicit_project_selection(self):
        result = subprocess.run(['bash', str(ROOT / 'docker-compose/update-all.sh')], capture_output=True)
        self.assertEqual(result.returncode, 2)

class FilterTests(unittest.TestCase):
    def test_sensitive_probes_match_but_normal_errors_do_not(self):
        import configparser
        import re
        config = configparser.ConfigParser()
        config.read(ROOT / 'configs/fail2ban/data/filter.d/npm-docker.conf')
        patterns = [re.compile(line.replace('<HOST>', r'\S+')) for line in
                    config['Definition']['failregex'].splitlines() if line]
        def matches(path, status):
            log = f'1.1.1.1 - - [09/Sep/2026:12:00:00 +0000] "GET {path} HTTP/1.1" {status} 123 "-" "Browser"'
            return any(p.search(log) for p in patterns)
        for path in ['/.env', '/.git/config', '/actuator/env', '/foo/.env.production']:
            self.assertTrue(matches(path, 404), path)
        for path, status in [('/', 301), ('/login', 401), ('/favicon.ico', 404),
                             ('/api/items', 403), ('/.env', 200)]:
            self.assertFalse(matches(path, status), path)


class CloudflareTests(unittest.TestCase):
    def api(self):
        import cloudflare_firewall
        api = object.__new__(cloudflare_firewall.Cloudflare)
        api.config = {'notes': 'test-owner', 'protected_networks': []}
        api.path = '/rules'
        return api

    def test_unban_preserves_other_owners(self):
        api = self.api()
        mine = {'mode': 'block', 'notes': 'test-owner', 'id': 'a' * 32}
        other = {'mode': 'block', 'notes': 'manual', 'id': 'b' * 32}
        with patch.object(api, 'rules', side_effect=[[mine, other], [other]]), \
             patch.object(api, 'request') as request:
            result = api.unban('1.1.1.1')
        request.assert_called_once_with('DELETE', '/rules/' + 'a' * 32)
        self.assertEqual(result['rules'], 1)

    def test_lost_write_response_is_verified_before_retry(self):
        import cloudflare_firewall
        api = self.api()
        with patch.object(api, 'rules', side_effect=[[], [{'mode': 'block'}]]), \
             patch.object(api, 'request', side_effect=cloudflare_firewall.ApiError('timeout')) as request:
            result = api.ban('1.1.1.1')
        self.assertEqual(result['status'], 'verified-blocked')
        self.assertEqual(request.call_count, 1)

    def test_allowlisted_ip_is_never_written(self):
        api = self.api()
        with patch.object(api, 'rules', return_value=[{'mode': 'whitelist'}]), \
             patch.object(api, 'request') as request:
            self.assertEqual(api.ban('1.1.1.1')['status'], 'allowlisted')
            request.assert_not_called()


if __name__ == '__main__':
    unittest.main()
