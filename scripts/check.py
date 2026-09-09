#!/usr/bin/env python3
"""Validate repository templates offline; never build images or start containers."""
import ast
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from prepare import ROOT, prepare


def run(args, **kwargs):
    result = subprocess.run(args, text=True, capture_output=True, **kwargs)
    if result.returncode:
        # Compose config may contain private input. Only show stderr from our isolated fixtures.
        raise RuntimeError(f'{args[0]} failed: {result.stderr.strip()}')
    return result.stdout


def main():
    manifest = json.loads((ROOT / 'deployments.json').read_text())
    projects = {p.parent.name for p in (ROOT / 'docker-compose').glob('*/docker-compose.yml')}
    assert projects == set(manifest), 'Compose projects and deployments.json differ'
    docker = shutil.which('docker')
    if not docker:
        raise RuntimeError('Docker Compose CLI is required; a running daemon is not needed')
    with tempfile.TemporaryDirectory(prefix='homelab-check-') as tmp:
        for name in sorted(projects):
            target = prepare(name, Path(tmp) / name)
            values = {}
            for line in (target / '.env.example').read_text().splitlines():
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    values[key] = value or 'validation-only'
            # Stub paths are used only for Compose's static configuration parser.
            source = Path(tmp) / 'source'
            source.mkdir(exist_ok=True)
            (source / 'Dockerfile').write_text('FROM scratch\n')
            auth = Path(tmp) / 'auth.json'
            auth.write_text('{}\n')
            values.update(FBN_SOURCE_DIR=str(source), FBN_AUTH_FILE=str(auth),
                          HOMEBRIDGE_DATA_DIR=str(source))
            content = ''.join(f'{key}={value}\n' for key, value in values.items())
            (target / '.env').write_text(content)
            if (target / 'docker-compose.env.example').exists():
                shutil.copy2(target / 'docker-compose.env.example', target / 'docker-compose.env')
            # Do not inherit a user's Compose substitutions or their private env files.
            clean_env = {k: os.environ[k] for k in ('PATH', 'HOME', 'DOCKER_CONFIG') if k in os.environ}
            run([docker, 'compose', '--project-directory', str(target), '--env-file',
                 str(target / '.env'), '-f', str(target / 'docker-compose.yml'),
                 'config', '--quiet'], env=clean_env)
            print(f'Compose: {name}')
    tracked = run(['git', 'ls-files', '-c', '-o', '--exclude-standard'], cwd=ROOT).splitlines()
    for relative in sorted(set(tracked)):
        path = ROOT / relative
        if not path.is_file():
            continue
        if path.suffix == '.sh':
            run(['bash', '-n', str(path)])
        elif path.suffix == '.py':
            ast.parse(path.read_text(), filename=relative)
        elif path.suffix == '.json' or path.name.endswith('.json.example'):
            json.loads(path.read_text())
        if path.suffix in {'.yaml', '.yml'} or path.name.endswith('.yml.example') or path.name.endswith('.yaml.example'):
            run(['ruby', '-rpsych', '-e', 'Psych.parse_stream(File.read(ARGV[0]))', str(path)])
        if path.suffix == '.md':
            for link in re.findall(r'\]\(([^)]+)\)', path.read_text()):
                if '://' in link or link.startswith('#'):
                    continue
                dest = link.split('#')[0]
                assert (path.parent / dest).exists(), f'Broken link: {relative} -> {link}'
    print('Shell syntax, Python syntax, JSON, YAML, and Markdown links: passed')


if __name__ == '__main__':
    main()
