#!/usr/bin/env python3
"""Assemble one project locally without overwriting an existing directory."""
import argparse
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def prepare(project, destination):
    projects = json.loads((ROOT / 'deployments.json').read_text())
    if project not in projects:
        raise ValueError(f'Unknown project: {project}')
    destination = Path(destination).absolute()
    # mkdir is deliberately exclusive; existing configuration and state are never replaced.
    destination.mkdir(parents=True, exist_ok=False)
    source = ROOT / 'docker-compose' / project
    for item in source.iterdir():
        if item.is_file() and (item.name.endswith('.example') or item.name in {
            'docker-compose.yml', 'Dockerfile', 'default.conf', 'settings.json', 'settings3.json'
        }):
            shutil.copy2(item, destination / item.name)
    for source_name, target_name in projects[project]['assets'].items():
        source_path = ROOT / source_name
        target = destination / target_name
        target.parent.mkdir(parents=True, exist_ok=True)
        if source_path.is_dir():
            # Copy only files tracked by this repository's asset tree, excluding private inputs.
            for item in source_path.rglob('*'):
                if item.is_file() and (item.suffix in {'.conf', '.local', '.py'} or item.name.endswith('.example')):
                    relative = item.relative_to(source_path)
                    (target / relative).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target / relative)
        else:
            shutil.copy2(source_path, target)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project')
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    try:
        result = prepare(args.project, args.destination)
    except (ValueError, FileExistsError) as exc:
        parser.exit(1, f'{exc}\n')
    print(result)


if __name__ == '__main__':
    main()
