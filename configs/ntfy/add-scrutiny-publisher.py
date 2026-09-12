#!/usr/bin/env python3
"""Add a token-only Scrutiny publisher to an existing private ntfy environment."""

import argparse
import os
from pathlib import Path
import secrets
import shutil
import string
import subprocess
from urllib.parse import urlsplit


PUBLISHER = 'scrutiny-publisher'
TOKEN_LABEL = 'scrutiny'


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
        raise RuntimeError('htpasswd is required to generate a bcrypt hash')
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
    known = {'kuma-publisher', 'mobile-subscriber'}
    topics = {
        entry.split(':', 2)[1]
        for entry in access_entries
        if entry.split(':', 2)[0] in known
    }
    if len(topics) != 1:
        raise ValueError('existing Kuma and mobile ACLs must share exactly one topic')
    return topics.pop()


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
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def extend(env_path, output_path, password_hasher=hash_password, token=None):
    if output_path.exists():
        raise FileExistsError(f'refusing to overwrite {output_path}')
    lines, values = read_env(env_path)
    required = {'NTFY_BASE_URL', 'NTFY_AUTH_USERS', 'NTFY_AUTH_ACCESS',
                'NTFY_AUTH_TOKENS'}
    missing = sorted(key for key in required if not values.get(key))
    if missing:
        raise ValueError('required ntfy inputs absent: ' + ', '.join(missing))

    users = split_entries(values['NTFY_AUTH_USERS'], 'NTFY_AUTH_USERS')
    access = split_entries(values['NTFY_AUTH_ACCESS'], 'NTFY_AUTH_ACCESS')
    tokens = split_entries(values['NTFY_AUTH_TOKENS'], 'NTFY_AUTH_TOKENS')
    if any(entry.split(':', 1)[0] == PUBLISHER for entry in users + access + tokens):
        raise ValueError(f'{PUBLISHER} already exists')

    parsed = urlsplit(values['NTFY_BASE_URL'])
    if parsed.scheme != 'https' or not parsed.netloc or parsed.path not in {'', '/'}:
        raise ValueError('NTFY_BASE_URL must be an HTTPS origin')
    topic = find_topic(access)
    alphabet = string.ascii_lowercase + string.digits
    access_token = token or 'tk_' + ''.join(
        secrets.choice(alphabet) for _ in range(29))
    if not access_token.startswith('tk_'):
        raise ValueError('Scrutiny token must use the ntfy tk_ format')
    password_hash = password_hasher(secrets.token_urlsafe(24), PUBLISHER)

    replacements = {
        'NTFY_AUTH_USERS': values['NTFY_AUTH_USERS'] +
            f',{PUBLISHER}:{password_hash}:user',
        'NTFY_AUTH_ACCESS': values['NTFY_AUTH_ACCESS'] +
            f',{PUBLISHER}:{topic}:wo',
        'NTFY_AUTH_TOKENS': values['NTFY_AUTH_TOKENS'] +
            f',{PUBLISHER}:{access_token}:{TOKEN_LABEL}',
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

    source_stat = env_path.stat()
    output_content = (
        f'SCRUTINY_NTFY_URL=ntfy://:{access_token}@{parsed.netloc}/{topic}\n')
    write_atomic(output_path, output_content, source_stat)
    try:
        write_atomic(env_path, '\n'.join(updated) + '\n', source_stat)
    except Exception:
        output_path.unlink(missing_ok=True)
        raise
    return {'publisher': PUBLISHER, 'topic': topic, 'output': output_path}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = extend(args.env_file, args.output)
    print(f"publisher={result['publisher']}")
    print(f"output={result['output']}")
    print('permissions=0600')


if __name__ == '__main__':
    try:
        main()
    except (FileExistsError, OSError, RuntimeError, ValueError) as error:
        raise SystemExit(f'error: {error}')
