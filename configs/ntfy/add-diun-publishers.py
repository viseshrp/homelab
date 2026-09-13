#!/usr/bin/env python3
"""Add per-host token-only DIUN publishers to an existing ntfy environment."""

import argparse
import os
from pathlib import Path
import secrets
import shutil
import string
import subprocess


DEFAULT_HOSTS = (
    'optiplex',
    'rpiblog',
    'rpihole',
    'rpimon',
    'rpinfs',
    'rpiproxy',
    'vpn-edge',
    'rpihass',
)
DIUN_IMAGE = (
    'crazymax/diun:4.33.0@'
    'sha256:e324b793eb32dfb7f74d3a39421ebf090141caaadee69b8f78da63112408ee25'
)


def read_env(path):
    values = {}
    lines = path.read_text().splitlines()
    for number, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            raise ValueError(f'{path}:{number}: expected KEY=VALUE')
        key, value = line.split('=', 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        values[key.strip()] = value
    return lines, values


def hash_password(password, username, executable=None):
    binary = executable or shutil.which('htpasswd')
    if not binary:
        raise RuntimeError('htpasswd is required to generate bcrypt hashes')
    result = subprocess.run(
        [binary, '-niBC', '12', username], input=password + '\n', text=True,
        capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError('htpasswd could not generate a bcrypt hash')
    prefix = username + ':'
    if not result.stdout.startswith(prefix):
        raise RuntimeError('htpasswd returned an unexpected result')
    value = result.stdout[len(prefix):].strip()
    if not value.startswith(('$2a$12$', '$2b$12$', '$2y$12$')):
        raise RuntimeError('htpasswd did not return a bcrypt cost-12 hash')
    return value


def split_entries(value, field):
    entries = [entry for entry in value.split(',') if entry]
    if any(len(entry.split(':', 2)) != 3 for entry in entries):
        raise ValueError(f'{field} contains an invalid entry')
    return entries


def find_topic(access_entries):
    known = {'kuma-publisher', 'mobile-subscriber', 'scrutiny-publisher'}
    topics = {
        entry.split(':', 2)[1]
        for entry in access_entries
        if entry.split(':', 2)[0] in known
    }
    if len(topics) != 1:
        raise ValueError('existing publisher and mobile ACLs must share one topic')
    return topics.pop()


def validate_host(host):
    if not host or any(char not in string.ascii_lowercase + string.digits + '-'
                       for char in host):
        raise ValueError(f'invalid host alias: {host!r}')


def write_private(path, content, uid, gid, *, newline=True):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, 'w') as handle:
            handle.write(content)
            if newline:
                handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.chown(path, uid, gid)
        os.chmod(path, 0o600)
    except Exception:
        path.unlink(missing_ok=True)
        raise


def write_atomic(path, content, source_stat):
    temporary = path.with_name(f'.{path.name}.tmp-{secrets.token_hex(6)}')
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, 'w') as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chown(temporary, source_stat.st_uid, source_stat.st_gid)
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def extend(env_path, output_dir, hosts=DEFAULT_HOSTS,
           password_hasher=hash_password, token_factory=None):
    hosts = tuple(hosts)
    if len(hosts) != len(set(hosts)):
        raise ValueError('host aliases must be unique')
    for host in hosts:
        validate_host(host)
    if output_dir.exists():
        raise FileExistsError(f'refusing to overwrite {output_dir}')

    lines, values = read_env(env_path)
    required = {
        'NTFY_AUTH_USERS', 'NTFY_AUTH_ACCESS', 'NTFY_AUTH_TOKENS',
        'NTFY_BIND_IP', 'NTFY_HTTP_PORT', 'TZ',
    }
    missing = sorted(key for key in required if not values.get(key))
    if missing:
        raise ValueError('required ntfy inputs absent: ' + ', '.join(missing))

    users = split_entries(values['NTFY_AUTH_USERS'], 'NTFY_AUTH_USERS')
    access = split_entries(values['NTFY_AUTH_ACCESS'], 'NTFY_AUTH_ACCESS')
    tokens = split_entries(values['NTFY_AUTH_TOKENS'], 'NTFY_AUTH_TOKENS')
    existing = {entry.split(':', 1)[0] for entry in users + access + tokens}
    publishers = {host: f'diun-{host}' for host in hosts}
    collisions = sorted(set(publishers.values()) & existing)
    if collisions:
        raise ValueError('DIUN publishers already exist: ' + ', '.join(collisions))

    topic = find_topic(access)
    if any(char in topic for char in '\r\n'):
        raise ValueError('ntfy topic contains a newline')
    endpoint = f"http://{values['NTFY_BIND_IP']}:{values['NTFY_HTTP_PORT']}"
    source_stat = env_path.stat()
    token_factory = token_factory or (
        lambda _host: 'tk_' + ''.join(
            secrets.choice(string.ascii_lowercase + string.digits)
            for _ in range(29)))

    new_users = []
    new_access = []
    new_tokens = []
    private = {}
    try:
        output_dir.mkdir(mode=0o700)
        os.chown(output_dir, source_stat.st_uid, source_stat.st_gid)
        for host, publisher in publishers.items():
            token = token_factory(host)
            if (not token.startswith('tk_') or len(token) != 32 or
                    any(char not in string.ascii_letters + string.digits + '_'
                        for char in token)):
                raise ValueError(f'{host} token must use the 32-character ntfy tk_ format')
            password_hash = password_hasher(secrets.token_urlsafe(24), publisher)
            new_users.append(f'{publisher}:{password_hash}:user')
            new_access.append(f'{publisher}:{topic}:wo')
            new_tokens.append(f'{publisher}:{token}:diun-{host}')

            host_dir = output_dir / host
            host_dir.mkdir(mode=0o700)
            os.chown(host_dir, source_stat.st_uid, source_stat.st_gid)
            env_content = '\n'.join((
                f'DIUN_IMAGE={DIUN_IMAGE}',
                f'DIUN_HOSTNAME={host}',
                f'TZ={values["TZ"]}',
                'DIUN_WATCH_SCHEDULE=0 */6 * * *',
                'DIUN_WATCH_JITTER=45m',
                'DIUN_WATCH_WORKERS=10',
                'DIUN_WATCH_STOPPED=true',
                'DIUN_LOG_LEVEL=info',
                f'DIUN_NTFY_ENDPOINT={endpoint}',
                f'DIUN_NTFY_TOPIC={topic}',
                'DIUN_NTFY_PRIORITY=3',
                'DOCKER_LOG_MAX_SIZE=10m',
                'DOCKER_LOG_MAX_FILES=3',
            ))
            write_private(host_dir / '.env', env_content,
                          source_stat.st_uid, source_stat.st_gid)
            write_private(host_dir / 'ntfy-token', token,
                          source_stat.st_uid, source_stat.st_gid, newline=False)
            private[host] = host_dir

        replacements = {
            'NTFY_AUTH_USERS': values['NTFY_AUTH_USERS'] + ',' + ','.join(new_users),
            'NTFY_AUTH_ACCESS': values['NTFY_AUTH_ACCESS'] + ',' + ','.join(new_access),
            'NTFY_AUTH_TOKENS': values['NTFY_AUTH_TOKENS'] + ',' + ','.join(new_tokens),
        }
        updated = []
        seen = set()
        for raw in lines:
            key = raw.split('=', 1)[0].strip() if '=' in raw else ''
            if key in replacements:
                updated.append(f"{key}='{replacements[key]}'")
                seen.add(key)
            else:
                updated.append(raw)
        if seen != set(replacements):
            raise ValueError('could not locate every ntfy auth line')
        write_atomic(env_path, '\n'.join(updated) + '\n', source_stat)
    except Exception:
        shutil.rmtree(output_dir, ignore_errors=True)
        raise

    return {'publishers': publishers, 'topic': topic, 'output': output_dir,
            'private': private}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--host', action='append', dest='hosts')
    args = parser.parse_args()
    result = extend(args.env_file, args.output_dir,
                    tuple(args.hosts) if args.hosts else DEFAULT_HOSTS)
    print(f"publishers={len(result['publishers'])}")
    print(f"output={result['output']}")
    print('directory_permissions=0700')
    print('file_permissions=0600')


if __name__ == '__main__':
    try:
        main()
    except (FileExistsError, OSError, RuntimeError, ValueError) as error:
        raise SystemExit(f'error: {error}')
