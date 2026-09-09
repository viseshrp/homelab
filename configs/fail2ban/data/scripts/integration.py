#!/usr/bin/env python3
"""Shared settings and IP validation for the NPM fail2ban actions."""
import ipaddress
import json
from pathlib import Path

CONFIG = Path('/data/f2b-integration.json')


def settings():
    return json.loads(CONFIG.read_text())


def address(value):
    return ipaddress.ip_address(value)


def protected(value, config):
    ip = address(value)
    return (not ip.is_global or any(ip in ipaddress.ip_network(n)
            for n in config['protected_networks']))

