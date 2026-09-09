#!/usr/bin/env python3
"""Cloudflare IP rules with exact lookups, verified results, and recorded ownership."""
import configparser
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from integration import address, protected, settings
from ownership import Ownership


class ApiError(RuntimeError):
    pass


class Cloudflare:
    def __init__(self, config, ownership=None):
        self.config = config
        self.ownership = ownership or Ownership(config['ownership_file'])
        credentials = configparser.ConfigParser(interpolation=None)
        if not credentials.read(config['credentials']):
            raise ApiError('Credential configuration cannot be read')
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
                raise ApiError('Cloudflare request failed: ' + str(
                    getattr(exc, 'code', 'network-error'))) from None
        raise ApiError('Cloudflare read attempts exhausted')

    def rules(self, ip=None, mode=None):
        query = {'page': 1, 'per_page': 500, 'match': 'all'}
        if ip is not None:
            ip = str(address(ip))
            query.update({'configuration.target': 'ip' if address(ip).version == 4 else 'ip6',
                          'configuration.value': ip})
        if mode:
            query['mode'] = mode
        result, seen = [], set()
        while query['page'] <= 200:
            data = self.request('GET', self.path, query=query)
            page = data['result']
            if not isinstance(page, list):
                raise ApiError('Invalid Cloudflare rule list')
            if page and all(r['id'] in seen for r in page):
                raise ApiError('Cloudflare pagination repeated a page')
            for rule in page:
                if rule['id'] in seen:
                    continue
                seen.add(rule['id'])
                conf = rule.get('configuration', {})
                if ip is None or (conf.get('target') in ('ip', 'ip6') and
                                  address(conf['value']) == address(ip)):
                    result.append(rule)
            info = data.get('result_info', {})
            per_page = max(1, int(info.get('per_page', query['per_page'])))
            total_pages = info.get('total_pages')
            if total_pages is None and info.get('total_count') is not None:
                total_pages = (int(info['total_count']) + per_page - 1) // per_page
            if not page or (total_pages is not None and query['page'] >= int(total_pages)):
                return result
            if total_pages is None and len(page) < per_page:
                return result
            query['page'] += 1
        raise ApiError('Cloudflare pagination exceeded its bound')

    def recover_ownership(self, rules):
        owned, intents = self.ownership.read()
        for rule in rules:
            ip = str(address(rule['configuration']['value']))
            if (rule['mode'] == 'block' and rule['id'] not in owned and
                    intents.get(rule.get('notes')) == ip):
                item = {'event': 'created', 'id': rule['id'], 'ip': ip, 'notes': rule['notes']}
                self.ownership.append(item)
                owned[rule['id']] = item
        return owned

    def ban(self, ip):
        ip = str(address(ip))
        if protected(ip, self.config):
            return {'status': 'protected', 'ip': ip}
        existing = self.rules(ip)
        self.recover_ownership(existing)
        if any(r['mode'] == 'whitelist' for r in existing):
            return {'status': 'allowlisted', 'ip': ip}
        if any(r['mode'] == 'block' for r in existing):
            return {'status': 'already-blocked', 'ip': ip}
        notes = self.config['notes'] + ' [' + self.config['owner_id'] + ':' + uuid.uuid4().hex + ']'
        self.ownership.append({'event': 'intent', 'ip': ip, 'notes': notes})
        body = {'mode': 'block', 'configuration': {
            'target': 'ip' if address(ip).version == 4 else 'ip6', 'value': ip}, 'notes': notes}
        error = None
        try:
            self.request('POST', self.path, body=body)
        except ApiError as exc:
            error = exc
        current = self.rules(ip)
        owned = self.recover_ownership(current)
        if any(r['id'] in owned and r.get('notes') == notes for r in current):
            return {'status': 'blocked', 'ip': ip}
        if error:
            raise error
        raise ApiError('Cloudflare did not retain the requested block')

    def unban(self, ip):
        ip = str(address(ip))
        current = self.rules(ip, 'block')
        owned = self.recover_ownership(current)
        selected = [r for r in current if r['mode'] == 'block' and
                    r['id'] in owned and owned[r['id']]['ip'] == ip and
                    owned[r['id']]['notes'] == r.get('notes')]
        errors = []
        for rule in selected:
            if not re.fullmatch(r'[a-fA-F0-9]{32}', rule['id']):
                raise ApiError('Invalid rule identifier')
            try:
                self.request('DELETE', self.path + '/' + rule['id'])
            except ApiError as exc:
                errors.append(exc)
        remaining_ids = {r['id'] for r in self.rules(ip, 'block')}
        for rule in selected:
            if rule['id'] not in remaining_ids:
                self.ownership.append({'event': 'released', 'id': rule['id'], 'ip': ip})
        if any(r['id'] in remaining_ids for r in selected):
            raise errors[0] if errors else ApiError('An owned Cloudflare block remains')
        return {'status': 'unbanned', 'ip': ip, 'rules': len(selected)}


def main():
    config = settings()
    with Ownership(config['ownership_file']).locked():
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
        print('cloudflare-firewall: ' + (str(exc) if isinstance(exc, ApiError)
                                        else type(exc).__name__), file=sys.stderr)
        sys.exit(1)
