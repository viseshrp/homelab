#!/usr/bin/env python3
"""Idempotent, exact-IP Cloudflare action. Credentials never enter argv/logs."""
import configparser
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from integration import address, protected, settings


class ApiError(RuntimeError):
    pass


class Cloudflare:
    def __init__(self, config):
        self.config = config
        credentials = configparser.ConfigParser(interpolation=None)
        credentials.read(config['credentials'])
        self.headers = {'X-Auth-Email': credentials['Init']['cfuser'],
                        'X-Auth-Key': credentials['Init']['cftoken'],
                        'Content-Type': 'application/json'}
        self.base = 'https://api.cloudflare.com/client/v4'
        self.path = '/user/firewall/access_rules/rules'

    def request(self, method, path, query=None, body=None):
        url = self.base + path
        if query:
            url += '?' + urllib.parse.urlencode(query)
        data = None if body is None else json.dumps(body).encode()
        # Do not retry writes blindly after an uncertain network response.
        attempts = 3 if method == 'GET' else 1
        for attempt in range(attempts):
            try:
                req = urllib.request.Request(url, data=data, headers=self.headers, method=method)
                with urllib.request.urlopen(req, timeout=15) as response:
                    result = json.load(response)
                if result.get('success') is not True:
                    codes = [e.get('code') for e in result.get('errors', [])]
                    raise ApiError('Cloudflare rejected request; codes=' + str(codes))
                return result
            except (urllib.error.URLError, TimeoutError) as exc:
                if method == 'GET' and attempt + 1 < attempts:
                    time.sleep(attempt + 1)
                    continue
                status = getattr(exc, 'code', 'network-error')
                raise ApiError('Cloudflare request failed: ' + str(status)) from None
        raise ApiError('Cloudflare read attempts exhausted')

    def rules(self, ip=None, mode=None):
        query = {'page': 1, 'per_page': 500, 'match': 'all'}
        if ip is not None:
            query['configuration.target'] = 'ip' if address(ip).version == 4 else 'ip6'
            query['configuration.value'] = str(address(ip))
        if mode:
            query['mode'] = mode
        result = []
        while True:
            data = self.request('GET', self.path, query=query)
            for rule in data['result']:
                conf = rule.get('configuration', {})
                if ip is None or (conf.get('target') in ('ip', 'ip6') and
                                  address(conf['value']) == address(ip)):
                    result.append(rule)
            info = data.get('result_info', {})
            if query['page'] >= info.get('total_pages', query['page']):
                break
            query['page'] += 1
        return result

    def ban(self, ip):
        ip = str(address(ip))
        if protected(ip, self.config):
            return {'status': 'protected', 'ip': ip}
        existing = self.rules(ip)
        if any(r['mode'] == 'whitelist' for r in existing):
            return {'status': 'allowlisted', 'ip': ip}
        if any(r['mode'] == 'block' for r in existing):
            return {'status': 'already-blocked', 'ip': ip}
        body = {'mode': 'block', 'configuration': {
            'target': 'ip' if address(ip).version == 4 else 'ip6', 'value': ip},
            'notes': self.config['notes']}
        try:
            self.request('POST', self.path, body=body)
        except ApiError:
            # A lost response or duplicate race must be resolved by a fresh read.
            if any(r['mode'] == 'block' for r in self.rules(ip)):
                return {'status': 'verified-blocked', 'ip': ip}
            raise
        if not any(r['mode'] == 'block' for r in self.rules(ip)):
            raise ApiError('Cloudflare did not retain the new block')
        return {'status': 'blocked', 'ip': ip}

    def unban(self, ip):
        ip = str(address(ip))
        # Never remove a manually-created rule, Allow rule, or another jail's rule.
        owned = [r for r in self.rules(ip, 'block')
                 if r['mode'] == 'block' and r.get('notes') == self.config['notes']]
        for rule in owned:
            rule_id = rule['id']
            if not re.fullmatch(r'[a-fA-F0-9]{32}', rule_id):
                raise ApiError('Invalid rule identifier')
            self.request('DELETE', self.path + '/' + rule_id)
        remaining = [r for r in self.rules(ip, 'block')
                     if r['mode'] == 'block' and r.get('notes') == self.config['notes']]
        if remaining:
            raise ApiError('An owned Cloudflare block remains')
        return {'status': 'unbanned', 'ip': ip, 'rules': len(owned)}


def main():
    config = settings()
    api = Cloudflare(config)
    command = sys.argv[1]
    if command == 'check':
        result = api.request('GET', api.path, query={'per_page': 1})
        print(json.dumps({'status': 'authenticated', 'success': result['success']}))
    elif command in ('ban', 'unban') and len(sys.argv) == 3:
        print(json.dumps(getattr(api, command)(sys.argv[2])))
    else:
        raise ValueError('Usage: cloudflare_firewall.py check|ban IP|unban IP')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        # Report no request headers, credentials, or raw remote response.
        print('cloudflare-firewall: ' + (str(exc) if isinstance(exc, ApiError)
                                        else type(exc).__name__), file=sys.stderr)
        sys.exit(1)
