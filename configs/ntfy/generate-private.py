#!/usr/bin/env python3
"""Generate private ntfy and Uptime Kuma inputs without printing secrets."""

import argparse
import ipaddress
import os
from pathlib import Path
import secrets
import shutil
import string
import subprocess
from urllib.parse import urlsplit


PUBLISHER = 'kuma-publisher'
SUBSCRIBER = 'mobile-subscriber'
DEFAULT_IMAGE = (
    'binwiederhier/ntfy:v2.28.0@sha256:'
    '6ef4b819f722fccdc036af611c4774cfdc2de821ab74fdd48bbf4c9d6f8973da'
)


def validate_base_url(value):
    parsed = urlsplit(value)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username
            or parsed.password or parsed.query or parsed.fragment
            or parsed.path not in {'', '/'}):
        raise ValueError('base URL must be an HTTPS origin without a path')
    return value.rstrip('/')


def validate_bind_ip(value):
    address = ipaddress.ip_address(value)
    if not address.is_private or address.is_loopback or address.is_unspecified:
        raise ValueError('bind IP must be a private, non-loopback address')
    return str(address)


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


def write_private(path, content):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, 'w') as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        raise


def generate(output_dir, base_url, bind_ip, uid=1000, gid=1000,
             timezone='America/New_York', image=DEFAULT_IMAGE,
             password_hasher=hash_password):
    base_url = validate_base_url(base_url)
    bind_ip = validate_bind_ip(bind_ip)
    output_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(output_dir, 0o700)

    topic = 'kuma-' + secrets.token_hex(12)
    publisher_password = secrets.token_urlsafe(24)
    subscriber_password = secrets.token_urlsafe(24)
    alphabet = string.ascii_lowercase + string.digits
    publisher_token = 'tk_' + ''.join(secrets.choice(alphabet) for _ in range(29))
    publisher_hash = password_hasher(publisher_password, PUBLISHER)
    subscriber_hash = password_hasher(subscriber_password, SUBSCRIBER)

    auth_users = (
        f'{PUBLISHER}:{publisher_hash}:user,'
        f'{SUBSCRIBER}:{subscriber_hash}:user')
    auth_access = f'{PUBLISHER}:{topic}:wo,{SUBSCRIBER}:{topic}:ro'
    auth_tokens = f'{PUBLISHER}:{publisher_token}:kuma'

    compose_env = f"""NTFY_IMAGE={image}
NTFY_BASE_URL={base_url}
NTFY_BIND_IP={bind_ip}
NTFY_HTTP_PORT=2586
NTFY_UID={uid}
NTFY_GID={gid}
TZ={timezone}
NTFY_CACHE_DURATION=72h
NTFY_UPSTREAM_BASE_URL=https://ntfy.sh
NTFY_AUTH_USERS='{auth_users}'
NTFY_AUTH_ACCESS='{auth_access}'
NTFY_AUTH_TOKENS='{auth_tokens}'
"""
    mobile = f"""Server: {base_url}
Topic: {topic}
Username: {SUBSCRIBER}
Password: {subscriber_password}
"""
    kuma = f"""UPTIME_KUMA_NTFY_SERVER_URL={base_url}
UPTIME_KUMA_NTFY_TOPIC={topic}
UPTIME_KUMA_NTFY_ACCESS_TOKEN={publisher_token}
"""

    paths = {
        'compose_env': output_dir / '.env',
        'mobile': output_dir / 'mobile-subscription.txt',
        'kuma': output_dir / 'kuma-ntfy.env',
    }
    for path in paths.values():
        if path.exists():
            raise FileExistsError(f'refusing to overwrite {path}')
    write_private(paths['compose_env'], compose_env)
    write_private(paths['mobile'], mobile)
    write_private(paths['kuma'], kuma)
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--bind-ip', required=True)
    parser.add_argument('--uid', type=int, default=1000)
    parser.add_argument('--gid', type=int, default=1000)
    parser.add_argument('--timezone', default='America/New_York')
    parser.add_argument('--image', default=DEFAULT_IMAGE)
    args = parser.parse_args()
    if args.uid < 0 or args.gid < 0:
        parser.error('UID and GID must be non-negative')
    old_umask = os.umask(0o077)
    try:
        paths = generate(
            args.output_dir, args.base_url, args.bind_ip, args.uid, args.gid,
            args.timezone, args.image)
    finally:
        os.umask(old_umask)
    print('generated=' + ','.join(path.name for path in paths.values()))
    print('permissions=0600')


if __name__ == '__main__':
    try:
        main()
    except (FileExistsError, OSError, RuntimeError, ValueError) as error:
        raise SystemExit(f'error: {error}')
