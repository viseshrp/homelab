#!/usr/bin/env python3
"""Audit, apply, or restore the reversible Radarr/Sonarr safety policy."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import urllib.request
import xml.etree.ElementTree as ET


PROJECT_ROOT = Path('/opt/media-automation')
BACKUP_ROOT = PROJECT_ROOT / 'backups'
POLICY_PATH = PROJECT_ROOT / 'safety-policy.json'
APPS = {
    'radarr': {
        'port': 7878,
        'config': PROJECT_ROOT / 'radarr/config/config.xml',
    },
    'sonarr': {
        'port': 8989,
        'config': PROJECT_ROOT / 'sonarr/config/config.xml',
    },
}
SECTIONS = ('downloadclient', 'mediamanagement', 'naming')
COUNT_ENDPOINTS = {
    'downloadClients': 'downloadclient',
    'indexers': 'indexer',
    'rootFolders': 'rootfolder',
}


def read_json(path):
    with path.open(encoding='utf-8') as handle:
        return json.load(handle)


def write_json_new(path, value):
    data = (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, 'wb') as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        raise
    return hashlib.sha256(data).hexdigest()


def api_key(app):
    value = ET.parse(APPS[app]['config']).getroot().findtext('ApiKey')
    if not value:
        raise RuntimeError(f'{app}: API key is absent')
    return value


def request(app, endpoint, method='GET', payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    headers = {'X-Api-Key': api_key(app)}
    if data is not None:
        headers['Content-Type'] = 'application/json'
    call = urllib.request.Request(
        f"http://127.0.0.1:{APPS[app]['port']}/api/v3/{endpoint}",
        data=data,
        headers=headers,
        method=method,
    )
    with urllib.request.urlopen(call, timeout=10) as response:
        body = response.read()
    return json.loads(body) if body else None


def desired_for(policy, app):
    desired = {name: dict(values) for name, values in policy['common'].items()}
    for name, values in policy['applications'][app].items():
        desired.setdefault(name, {}).update(values)
    return desired


def capture(policy):
    captured = {}
    for app in APPS:
        counts = {}
        for name, endpoint in COUNT_ENDPOINTS.items():
            value = request(app, endpoint)
            if not isinstance(value, list):
                raise RuntimeError(f'{app}: unexpected {endpoint} response')
            counts[name] = len(value)
        resources = {
            section: request(app, f'config/{section}') for section in SECTIONS
        }
        desired = desired_for(policy, app)
        for section, values in desired.items():
            missing = sorted(set(values) - set(resources[section]))
            if missing:
                raise RuntimeError(
                    f"{app}: settings absent from {section}: {', '.join(missing)}")
        status = request(app, 'system/status')
        captured[app] = {
            'counts': counts,
            'resources': resources,
            'version': status.get('version'),
        }
    return captured


def require_empty(policy, captured):
    problems = []
    for app, state in captured.items():
        for name, expected in policy['requirements'].items():
            actual = state['counts'][name]
            if actual != expected:
                problems.append(f'{app}.{name}={actual}, expected {expected}')
    if problems:
        raise RuntimeError('refusing safety change: ' + '; '.join(problems))


def controlled_values(policy, app, resources):
    return {
        section: {name: resources[section][name] for name in values}
        for section, values in desired_for(policy, app).items()
    }


def snapshot(policy, captured):
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    directory = BACKUP_ROOT / f'settings-before-media-safety-{timestamp}'
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    manifest = {
        'createdAt': datetime.now(timezone.utc).isoformat(),
        'purpose': 'Exact pre-change values for reversible media-safety settings',
        'applications': {},
    }
    hashes = {}
    for app, state in captured.items():
        resource_file = directory / f'{app}-resources.json'
        hashes[resource_file.name] = write_json_new(resource_file, state['resources'])
        manifest['applications'][app] = {
            'before': controlled_values(policy, app, state['resources']),
            'counts': state['counts'],
            'target': desired_for(policy, app),
            'version': state['version'],
        }
    manifest['resourceSha256'] = hashes
    manifest_path = directory / 'manifest.json'
    write_json_new(manifest_path, manifest)
    verified = read_json(manifest_path)
    if verified != manifest:
        raise RuntimeError('rollback manifest verification failed')
    for filename, expected in hashes.items():
        actual = hashlib.sha256((directory / filename).read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError(f'rollback resource verification failed: {filename}')
    return directory, manifest


def update_section(app, section, replacements):
    current = request(app, f'config/{section}')
    changed = {name: value for name, value in replacements.items()
               if current[name] != value}
    if not changed:
        return False
    updated = dict(current)
    updated.update(changed)
    request(app, f"config/{section}/{current['id']}", 'PUT', updated)
    verified = request(app, f'config/{section}')
    wrong = {name: {'expected': value, 'actual': verified.get(name)}
             for name, value in replacements.items() if verified.get(name) != value}
    if wrong:
        raise RuntimeError(f'{app}.{section}: verification failed: {wrong}')
    return True


def restore_manifest(directory, manifest):
    changed = []
    for app, state in manifest['applications'].items():
        for section, values in state['before'].items():
            if update_section(app, section, values):
                changed.append(f'{app}.{section}')
    return changed


def audit(policy):
    captured = capture(policy)
    result = {}
    for app, state in captured.items():
        result[app] = {
            'counts': state['counts'],
            'controlled': controlled_values(policy, app, state['resources']),
            'version': state['version'],
        }
    print(json.dumps(result, indent=2, sort_keys=True))


def apply(policy):
    captured = capture(policy)
    require_empty(policy, captured)
    directory, manifest = snapshot(policy, captured)
    print(f'rollback_snapshot={directory}')
    print('rollback_snapshot_verified=true')
    changed = []
    try:
        for app in APPS:
            for section, values in desired_for(policy, app).items():
                if update_section(app, section, values):
                    changed.append(f'{app}.{section}')
    except Exception:
        restore_manifest(directory, manifest)
        print('apply_failed_automatic_restore=true', file=sys.stderr)
        raise
    print('changed=' + (','.join(changed) if changed else 'none'))
    print('safety_policy_verified=true')


def restore(policy, supplied):
    directory = supplied.resolve()
    backup_root = BACKUP_ROOT.resolve()
    if directory.parent != backup_root or not directory.name.startswith(
            'settings-before-media-safety-'):
        raise RuntimeError(f'refusing snapshot outside {backup_root}')
    manifest = read_json(directory / 'manifest.json')
    captured = capture(policy)
    require_empty(policy, captured)
    changed = restore_manifest(directory, manifest)
    print('restored=' + (','.join(changed) if changed else 'none'))
    print('original_values_verified=true')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('audit', 'apply', 'restore'))
    parser.add_argument('snapshot', nargs='?', type=Path)
    args = parser.parse_args()
    if args.action == 'restore' and args.snapshot is None:
        parser.error('restore requires an explicit snapshot directory')
    if args.action != 'restore' and args.snapshot is not None:
        parser.error('a snapshot directory is accepted only with restore')
    policy = read_json(POLICY_PATH)
    if args.action == 'audit':
        audit(policy)
    elif args.action == 'apply':
        apply(policy)
    else:
        restore(policy, args.snapshot)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'error: {exc}', file=sys.stderr)
        raise SystemExit(1)
