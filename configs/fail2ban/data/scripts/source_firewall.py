#!/usr/bin/env python3
"""Source-IP bans for both Docker forwarding and local HTTP(S), IPv4/IPv6."""
import json
import subprocess
import sys
from integration import address, protected, settings


def run(args, check=True, data=None):
    return subprocess.run(args, input=data, text=True, capture_output=True, check=check)


def ensure(config):
    for version, binary, family in [(4, 'iptables', 'inet'), (6, 'ip6tables', 'inet6')]:
        name = config['set_prefix'] + str(version)
        run(['ipset', 'create', name, 'hash:ip', 'family', family,
             'maxelem', '131072', '-exist'])
        for chain in ('INPUT', 'DOCKER-USER'):
            rule = ['-p', 'tcp', '-m', 'multiport', '--dports', config['ports'],
                    '-m', 'conntrack', '--ctdir', 'ORIGINAL',
                    '-m', 'set', '--match-set', name, 'src',
                    '-m', 'comment', '--comment', 'fail2ban npm source bans', '-j', 'DROP']
            if run([binary, '-w', '5', '-C', chain] + rule, check=False).returncode:
                run([binary, '-w', '5', '-I', chain, '1'] + rule)


def main():
    config = settings()
    command = sys.argv[1]
    if command == 'start':
        ensure(config)
        print('source-firewall: ready')
    elif command in ('ban', 'unban'):
        ip = str(address(sys.argv[2]))
        if protected(ip, config):
            print('source-firewall: protected ' + ip)
            return
        ensure(config)
        operation = 'add' if command == 'ban' else 'del'
        run(['ipset', operation, config['set_prefix'] + str(address(ip).version), ip, '-exist'])
        print('source-firewall: ' + command + ' ' + ip)
    elif command == 'sync':
        # Add missing members only. Never flush a set or remove old rules.
        ensure(config)
        ips = run(['fail2ban-client', 'get', config['jail'], 'banip']).stdout.split()
        commands = []
        skipped = []
        for value in ips:
            ip = str(address(value))
            if protected(ip, config):
                skipped.append(ip)
            else:
                commands.append('add ' + config['set_prefix'] + str(address(ip).version) + ' ' + ip)
        run(['ipset', 'restore', '-exist'], data='\n'.join(commands) + '\n')
        print(json.dumps({'added_or_existing': len(commands), 'protected_skipped': skipped}))
    else:
        raise ValueError('Usage: source_firewall.py start|sync|ban IP|unban IP')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('source-firewall: ' + type(exc).__name__, file=sys.stderr)
        sys.exit(1)
