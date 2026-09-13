"""Offline tests for distributed DIUN monitoring and private ntfy publishers."""

import importlib.util
import json
from pathlib import Path
import stat
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


publisher = load_module(
    'ntfy_add_diun', ROOT / 'configs/ntfy/add-diun-publishers.py')
prepare = load_module('homelab_prepare', ROOT / 'scripts/prepare.py')


class DiunTests(unittest.TestCase):
    conventional_hosts = (
        'optiplex', 'rpiblog', 'rpihole', 'rpimon', 'rpinfs', 'rpiproxy',
        'vpn-edge',
    )
    publisher_hosts = conventional_hosts + ('rpihass',)

    @staticmethod
    def fixture(path):
        path.write_text(
            'NTFY_BIND_IP=192.0.2.14\n'
            'NTFY_HTTP_PORT=2586\n'
            'TZ=America/New_York\n'
            "NTFY_AUTH_USERS='kuma-publisher:$2y$12$kuma:user,"
            "mobile-subscriber:$2y$12$mobile:user,"
            "scrutiny-publisher:$2y$12$scrutiny:user'\n"
            "NTFY_AUTH_ACCESS='kuma-publisher:private-topic:wo,"
            "mobile-subscriber:private-topic:ro,"
            "scrutiny-publisher:private-topic:wo'\n"
            "NTFY_AUTH_TOKENS='kuma-publisher:tk_existing:kuma,"
            "scrutiny-publisher:tk_existing2:scrutiny'\n")
        path.chmod(0o600)

    def read_host_rules(self, host):
        path = ROOT / f'docker-compose/diun-agent/rules/{host}.yml'
        return json.loads(path.read_text())

    def test_compose_combines_local_docker_and_local_file_providers(self):
        compose = (ROOT / 'docker-compose/diun-agent/docker-compose.yml').read_text()
        example = (ROOT / 'docker-compose/diun-agent/.env.example').read_text()
        self.assertIn('DIUN_DEFAULTS_NOTIFYON: "update"', compose)
        self.assertIn('DIUN_PROVIDERS_DOCKER_WATCHBYDEFAULT: "true"', compose)
        self.assertIn('DIUN_PROVIDERS_DOCKER_WATCHSTOPPED:', compose)
        self.assertIn('DIUN_PROVIDERS_FILE_FILENAME:', compose)
        self.assertIn('/var/run/docker.sock:/var/run/docker.sock:ro', compose)
        self.assertIn('./custom-images.yml:/etc/diun/custom-images.yml:ro', compose)
        self.assertIn('./ntfy-token:/run/secrets/ntfy-token:ro', compose)
        self.assertIn('DIUN_NOTIF_NTFY_TOKENFILE:', compose)
        self.assertIn('read_only: true', compose)
        self.assertIn('no-new-privileges:true', compose)
        self.assertIn('cap_drop:', compose)
        self.assertNotIn('\n    ports:', compose)
        self.assertNotIn('release-watch', compose)
        self.assertNotIn('profiles:', compose)
        self.assertNotIn('docker compose pull', compose)
        self.assertNotIn('docker compose up', compose)
        self.assertIn('crazymax/diun:4.33.0@sha256:e324b793', example)
        self.assertIn('DIUN_WATCH_SCHEDULE: "${DIUN_WATCH_SCHEDULE:-0 */6 * * *}"',
                      compose)
        self.assertIn('DIUN_WATCH_SCHEDULE=0 */6 * * *', example)
        self.assertFalse(
            (ROOT / 'docker-compose/diun-agent/release-watch.yml').exists())
        self.assertFalse(
            (ROOT / 'docker-compose/diun-agent/.env.release-watch.example').exists())

    def test_each_conventional_host_has_its_own_bounded_rules(self):
        expected_direct = {
            'optiplex': {
                'docker.io/crazymax/diun:latest',
                'docker.io/amir20/dozzle:latest',
                'lscr.io/linuxserver/bazarr:latest',
                'lscr.io/linuxserver/sonarr:latest',
                'lscr.io/linuxserver/radarr:latest',
                'ghcr.io/seerr-team/seerr:latest',
                'ghcr.io/analogj/scrutiny:latest-collector',
            },
            'rpiblog': {
                'docker.io/crazymax/diun:latest',
                'docker.io/amir20/dozzle:latest',
                'ghcr.io/plankanban/planka:latest',
                'ghcr.io/ajnart/homarr:latest',
                'docker.io/library/nginx:latest',
                'docker.io/library/ubuntu:24.04',
            },
            'rpihole': {
                'docker.io/crazymax/diun:latest',
                'docker.io/amir20/dozzle:latest',
            },
            'rpimon': {
                'docker.io/crazymax/diun:latest',
                'docker.io/amir20/dozzle:latest',
                'docker.io/archivebox/archivebox:dev',
                'docker.io/webrecorder/pywb:latest',
                'ghcr.io/analogj/scrutiny:latest-web',
                'docker.io/library/influxdb:2',
            },
            'rpinfs': {
                'docker.io/crazymax/diun:latest',
                'docker.io/amir20/dozzle:latest',
            },
            'rpiproxy': {
                'docker.io/crazymax/diun:latest',
                'docker.io/amir20/dozzle:latest',
                'docker.io/cloudflare/cloudflared:latest',
            },
            'vpn-edge': {
                'docker.io/crazymax/diun:latest',
                'docker.io/amir20/dozzle:latest',
            },
        }
        expected_repo = {
            'optiplex': set(),
            'rpiblog': {'docker.io/library/postgres:14-alpine'},
            'rpihole': set(),
            'rpimon': {
                'docker.io/louislam/uptime-kuma:2',
                'docker.io/library/influxdb:2',
            },
            'rpinfs': set(),
            'rpiproxy': set(),
            'vpn-edge': {
                'ghcr.io/wg-easy/wg-easy:15',
                'docker.io/library/postgres:15',
            },
        }

        for host in self.conventional_hosts:
            with self.subTest(host=host):
                rules = self.read_host_rules(host)
                direct = {rule['name'] for rule in rules
                          if not rule.get('watch_repo')}
                repositories = {rule['name'] for rule in rules
                                if rule.get('watch_repo')}
                self.assertEqual(direct, expected_direct[host])
                self.assertEqual(repositories, expected_repo[host])
                self.assertEqual(len(rules), len({
                    (rule['name'], rule.get('watch_repo', False))
                    for rule in rules
                }))
                for rule in rules:
                    self.assertEqual(rule['notify_on'],
                                     ['new'] if rule.get('watch_repo') else ['update'])
                    if rule.get('watch_repo'):
                        self.assertEqual(len(rule['include_tags']), 1)
                        self.assertTrue(rule['include_tags'][0].startswith('^'))
                        self.assertTrue(rule['include_tags'][0].endswith('$'))
                names = {rule['name'] for rule in rules}
                self.assertNotIn('docker.io/homebridge/homebridge:latest', names)
                self.assertNotIn('lscr.io/linuxserver/pairdrop:latest', names)

    def test_manifest_and_prepare_select_one_local_rule_file(self):
        manifest = json.loads((ROOT / 'deployments.json').read_text())
        deployment = manifest['diun-agent']
        self.assertEqual(deployment['hosts'], list(self.conventional_hosts))
        self.assertEqual(deployment['directory'], '/opt/diun-agent')
        self.assertEqual(deployment['assets'], {})
        self.assertEqual(set(deployment['host_assets']),
                         set(self.conventional_hosts))

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            missing_host = root / 'missing-host'
            with self.assertRaisesRegex(ValueError, 'requires --host'):
                prepare.prepare('diun-agent', missing_host)
            self.assertFalse(missing_host.exists())

            invalid_host = root / 'invalid-host'
            with self.assertRaisesRegex(ValueError, 'not a deployment target'):
                prepare.prepare('diun-agent', invalid_host, host='rpihass')
            self.assertFalse(invalid_host.exists())

            for host in self.conventional_hosts:
                target = prepare.prepare('diun-agent', root / host, host=host)
                self.assertEqual(
                    (target / 'custom-images.yml').read_bytes(),
                    (ROOT / f'docker-compose/diun-agent/rules/{host}.yml').read_bytes())
                self.assertFalse((target / 'rules').exists())

    def test_generator_adds_unique_write_only_publishers(self):
        with tempfile.TemporaryDirectory() as directory:
            env_path = Path(directory) / '.env'
            output_dir = Path(directory) / 'diun-private'
            self.fixture(env_path)
            result = publisher.extend(
                env_path, output_dir, self.publisher_hosts,
                password_hasher=lambda _password, host: '$2y$12$' + host,
                token_factory=lambda host: 'tk_' +
                (host.replace('-', '') + ('x' * 29))[:29])

            self.assertEqual(result['topic'], 'private-topic')
            updated = env_path.read_text()
            for host in self.publisher_hosts:
                identity = f'diun-{host}'
                self.assertIn(f'{identity}:private-topic:wo', updated)
                self.assertIn(f'{identity}:tk_', updated)
                host_dir = output_dir / host
                env_content = (host_dir / '.env').read_text()
                token = (host_dir / 'ntfy-token').read_text()
                self.assertIn(f'DIUN_HOSTNAME={host}', env_content)
                self.assertIn('DIUN_NTFY_ENDPOINT=http://192.0.2.14:2586',
                              env_content)
                self.assertIn('DIUN_NTFY_TOPIC=private-topic', env_content)
                self.assertIn('DIUN_WATCH_SCHEDULE=0 */6 * * *', env_content)
                self.assertNotIn('COMPOSE_PROFILES=', env_content)
                self.assertNotIn('DIUN_RELEASE_WATCH_', env_content)
                self.assertNotIn(token, env_content)
                self.assertFalse(
                    (host_dir / 'ntfy-token').read_bytes().endswith(b'\n'))
                self.assertEqual(stat.S_IMODE(host_dir.stat().st_mode), 0o700)
                for private_file in (host_dir / '.env', host_dir / 'ntfy-token'):
                    self.assertEqual(
                        stat.S_IMODE(private_file.stat().st_mode), 0o600)

    def test_generator_refuses_existing_identity_without_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            env_path = Path(directory) / '.env'
            output_dir = Path(directory) / 'diun-private'
            self.fixture(env_path)
            original = env_path.read_text()
            env_path.write_text(original.replace(
                "scrutiny-publisher:$2y$12$scrutiny:user'",
                "scrutiny-publisher:$2y$12$scrutiny:user,"
                "diun-rpimon:$2y$12$existing:user'"))
            before = env_path.read_text()
            with self.assertRaisesRegex(ValueError, 'already exist'):
                publisher.extend(env_path, output_dir, ('rpimon',))
            self.assertEqual(env_path.read_text(), before)
            self.assertFalse(output_dir.exists())

    def test_haos_app_watches_only_homebridge_and_pairdrop(self):
        config = (ROOT / 'home-assistant-diun-agent/config.yaml').read_text()
        dockerfile = (ROOT / 'home-assistant-diun-agent/Dockerfile').read_text()
        runner = (ROOT / 'home-assistant-diun-agent/run.sh').read_text()
        rules = json.loads(
            (ROOT / 'home-assistant-diun-agent/custom-images.yml').read_text())
        self.assertIn('version: "4.33.0-5"', config)
        self.assertIn('schedule: "0 */6 * * *"', config)
        self.assertIn('docker_api: false', config)
        self.assertIn('backup: cold', config)
        self.assertIn('ntfy_token: password', config)
        self.assertIn('notification_test_on_start: bool', config)
        self.assertNotIn('watch_stopped:', config)
        self.assertNotIn('\nports:', config)
        self.assertIn('crazymax/diun:4.33.0@sha256:e324b793', dockerfile)
        self.assertIn('COPY custom-images.yml /etc/diun/custom-images.yml',
                      dockerfile)
        self.assertIn("printf '%s' \"$ntfy_token\"", runner)
        self.assertIn('DIUN_PROVIDERS_FILE_FILENAME=', runner)
        self.assertNotIn('DIUN_PROVIDERS_DOCKER', runner)
        self.assertNotIn('watch_stopped', runner)
        self.assertIn('/usr/local/bin/diun notif test', runner)
        self.assertIn('kill -TERM "$diun_pid"', runner)
        self.assertNotIn('docker pull', runner)
        self.assertEqual(rules, [
            {
                'name': 'docker.io/homebridge/homebridge:latest',
                'notify_on': ['update'],
            },
            {
                'name': 'lscr.io/linuxserver/pairdrop:latest',
                'notify_on': ['update'],
            },
        ])

        inventory = json.loads(
            (ROOT / 'configs/homeassistant/apps.json').read_text())
        monitored = {app['release_channel'] for app in inventory['apps']
                     if app.get('diun_release_monitoring')}
        self.assertEqual(monitored, {rule['name'] for rule in rules})


if __name__ == '__main__':
    unittest.main()
