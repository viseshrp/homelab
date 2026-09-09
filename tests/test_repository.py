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
import check
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


class DeploymentManifestTests(unittest.TestCase):
    def test_single_and_replicated_hosts_are_valid(self):
        manifest = {
            'single': {'host': 'rpimon'},
            'replicated': {'hosts': ['rpiblog', 'rpihole']},
        }
        check.validate_manifest(manifest, set(manifest))

    def test_host_and_hosts_are_mutually_exclusive(self):
        manifest = {'broken': {'host': 'rpimon', 'hosts': ['rpimon']}}
        with self.assertRaises(AssertionError):
            check.validate_manifest(manifest, set(manifest))

    def test_replicated_hosts_must_be_unique(self):
        manifest = {'broken': {'hosts': ['rpimon', 'rpimon']}}
        with self.assertRaises(AssertionError):
            check.validate_manifest(manifest, set(manifest))


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
        fallback = '[09/Sep/2026:12:00:00 +0000] 404 - GET https example.com "/.env" [Client 1.1.1.1] [Length 123] "-" "Browser"'
        self.assertTrue(any(p.search(fallback) for p in patterns))
        for path, status in [('/', 301), ('/login', 401), ('/favicon.ico', 404),
                             ('/api/items', 403), ('/.env', 200)]:
            self.assertFalse(matches(path, status), path)


class CloudflareTests(unittest.TestCase):
    def setUp(self):
        import cloudflare_firewall
        from ownership import Ownership
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.api = object.__new__(cloudflare_firewall.Cloudflare)
        self.api.config = {'notes': 'test-owner', 'owner_id': 'test-instance', 'protected_networks': []}
        self.api.ownership = Ownership(Path(self.temp.name) / 'ownership.jsonl')
        self.api.path = '/rules'

    def rule(self, id='a', notes='manual', mode='block'):
        return {'id': id * 32, 'mode': mode, 'notes': notes,
                'configuration': {'target': 'ip', 'value': '1.1.1.1'}}

    def test_unban_preserves_other_owners_even_with_matching_notes(self):
        mine = self.rule(notes='test-owner')
        other = self.rule(id='b', notes='test-owner')
        self.api.ownership.append({'event': 'created', 'id': mine['id'],
                                   'ip': '1.1.1.1', 'notes': mine['notes']})
        with patch.object(self.api, 'rules', side_effect=[[mine, other], [other]]), \
             patch.object(self.api, 'request') as request:
            result = self.api.unban('1.1.1.1')
        request.assert_called_once_with('DELETE', '/rules/' + 'a' * 32)
        self.assertEqual(result['rules'], 1)
        self.assertEqual(self.api.ownership.read()[0], {})

    def test_lost_write_response_recovers_recorded_intent(self):
        import cloudflare_firewall
        records = []
        def write(method, path, body):
            self.assertEqual(method, 'POST')
            records.append(self.rule(notes=body['notes']))
            raise cloudflare_firewall.ApiError('lost response')
        with patch.object(self.api, 'rules', side_effect=lambda *args: list(records)), \
             patch.object(self.api, 'request', side_effect=write) as request:
            result = self.api.ban('1.1.1.1')
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(request.call_count, 1)
        self.assertIn('a' * 32, self.api.ownership.read()[0])

    def test_allowlisted_ip_is_never_written(self):
        with patch.object(self.api, 'rules', return_value=[self.rule(mode='whitelist')]), \
             patch.object(self.api, 'request') as request:
            self.assertEqual(self.api.ban('1.1.1.1')['status'], 'allowlisted')
            request.assert_not_called()

    def test_repeated_pagination_page_fails(self):
        import cloudflare_firewall
        with patch.object(self.api, 'request', return_value={
            'result': [self.rule()], 'result_info': {'total_pages': 2}
        }):
            with self.assertRaises(cloudflare_firewall.ApiError):
                self.api.rules('1.1.1.1')


class RestoreTests(unittest.TestCase):
    def test_restore_excludes_expired_other_jail_and_private_bans(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as tmp:
            database = Path(tmp) / 'fail2ban.sqlite3'
            with sqlite3.connect(database) as connection:
                connection.execute('CREATE TABLE bips (ip TEXT, jail TEXT, bantime INTEGER, timeofban REAL)')
                connection.executemany('INSERT INTO bips VALUES (?, ?, ?, ?)', [
                    ('1.1.1.1', 'npm-docker', -1, 0),
                    ('8.8.8.8', 'npm-docker', 100, 950),
                    ('8.8.4.4', 'npm-docker', 10, 0),
                    ('9.9.9.9', 'another-jail', -1, 0),
                    ('10.0.0.1', 'npm-docker', -1, 0),
                ])
            before = database.read_bytes()
            config = {'database': str(database), 'jail': 'npm-docker',
                      'protected_networks': [], 'set_prefix': 'test-'}
            with patch.object(source_firewall, 'ensure'), \
                 patch.object(source_firewall.time, 'time', return_value=1000), \
                 patch.object(source_firewall, 'run') as run:
                self.assertEqual(source_firewall.restore(config), 2)
            run.assert_called_once_with(['ipset', 'restore', '-exist'],
                                        data='add test-4 1.1.1.1\nadd test-4 8.8.8.8\n')
            self.assertEqual(database.read_bytes(), before)


class PersistentActionTests(unittest.TestCase):
    def test_shutdown_preserves_bans_and_explicit_flush_unbans(self):
        import importlib.util
        import types
        class CommandAction:
            def __init__(self, jail, name):
                self._jail = jail
            def flush(self):
                return 'shutdown-noop'
            def reload(self):
                return True
        fake = types.ModuleType('fail2ban.server.action')
        fake.CommandAction = CommandAction
        spec = importlib.util.spec_from_file_location(
            'persistent_fixture', ROOT / 'configs/fail2ban/data/action.d/persistent.py')
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'fail2ban.server.action': fake}):
            spec.loader.exec_module(module)
        jail = types.SimpleNamespace(actions=types.SimpleNamespace(active=True))
        action = module.Action(jail, 'fixture', 'python3 helper.py', skip_restored='true', startup='restore')
        self.assertFalse(action.flush())
        self.assertIn('<restored>', action.actionban)
        self.assertFalse(action.actionstart_on_demand)
        self.assertEqual(action.actionstart, 'python3 helper.py restore')
        jail.actions.active = False
        self.assertEqual(action.flush(), 'shutdown-noop')
        self.assertEqual(action.actionflush, 'true')


if __name__ == '__main__':
    unittest.main()
