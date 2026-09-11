#!/usr/bin/env python3
"""Audit or reconcile Uptime Kuma monitors from a sanitized policy file."""

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
from urllib.parse import urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG = ROOT / 'monitors.json'
DEFAULT_ENV = ROOT / '.env'
DEFAULT_DATA = ROOT / 'uptime-kuma-data'
DEFAULT_BACKUPS = ROOT / 'backups'
TEST_NETWORKS = tuple(ipaddress.ip_network(value) for value in (
    '192.0.2.0/24', '198.51.100.0/24', '203.0.113.0/24'))


NODE_PROGRAM = r'''const payload = JSON.parse(Buffer.from(
    "__PAYLOAD_B64__", "base64").toString("utf8"));
const crypto = require("crypto");
const knex = require("knex");
const Dialect = require("knex/lib/dialects/sqlite3/index.js");
Dialect.prototype._driver = () => require("@louislam/sqlite3");
const jwt = require("jsonwebtoken");
const { shake256, SHAKE256_LENGTH } = require("./server/util-server");
const { io } = require("socket.io-client");

const CONFIG_COLUMNS = [
    "id", "name", "active", "user_id", "type", "interval", "url",
    "hostname", "port", "maxretries", "ignore_tls", "upside_down",
    "maxredirects", "accepted_statuscodes_json", "dns_resolve_type",
    "dns_resolve_server", "retry_interval", "method", "expiry_notification",
    "resend_interval", "packet_size", "timeout"
];

function stable(value) {
    if (Array.isArray(value)) return value.map(stable);
    if (value && typeof value === "object") {
        return Object.fromEntries(Object.keys(value).sort().map(
            key => [key, stable(value[key])]));
    }
    return value;
}

function equal(left, right) {
    return JSON.stringify(stable(left)) === JSON.stringify(stable(right));
}

function desiredFields(monitor, defaults) {
    const type = monitor.type;
    const fields = {
        name: monitor.name,
        active: defaults.active ? 1 : 0,
        type,
        interval: defaults.interval_seconds,
        maxretries: defaults.retries,
        retry_interval: defaults.retry_interval_seconds,
        resend_interval: defaults.resend_interval_seconds,
        timeout: defaults.timeout_seconds,
        method: "GET",
        ignore_tls: 0,
        expiry_notification: type === "http" && defaults.http_expiry_notification ? 1 : 0,
        upside_down: monitor.expected_failure ? 1 : 0,
        packet_size: defaults.ping_packet_size,
        maxredirects: defaults.max_redirects,
        accepted_statuscodes_json: JSON.stringify(defaults.accepted_status_codes),
    };
    if (type === "http") fields.url = monitor.url;
    if (["port", "ping"].includes(type)) fields.hostname = monitor.hostname;
    if (type === "port") fields.port = monitor.port;
    if (type === "dns") {
        fields.hostname = monitor.query;
        fields.port = monitor.port;
        fields.dns_resolve_type = monitor.record_type;
        fields.dns_resolve_server = monitor.resolver;
    }
    return fields;
}

function canonicalName(name, policy) {
    for (const monitor of policy.monitors) {
        const old = policy.previous_names[monitor.name] || [];
        if (name === monitor.name || old.includes(name)) return monitor.name;
    }
    return name;
}

async function readState() {
    const db = knex({
        client: Dialect,
        connection: { filename: "/app/data/kuma.db" },
        useNullAsDefault: true,
    });
    const version = require("./package.json").version;
    const users = await db("user").where({ active: 1 });
    if (users.length !== 1) throw new Error(
        `expected one active Uptime Kuma user, found ${users.length}`);
    const user = users[0];
    const notifications = await db("notification").where({
        user_id: user.id, active: 1, is_default: 1,
    });
    if (notifications.length !== 1) throw new Error(
        `expected one active default notification, found ${notifications.length}`);
    const monitors = await db("monitor").where({ user_id: user.id })
        .select(CONFIG_COLUMNS).orderBy("id");
    const monitorNotifications = await db("monitor_notification")
        .select("monitor_id", "notification_id").orderBy("monitor_id")
        .orderBy("notification_id");
    const page = await db("status_page")
        .where({ slug: payload.policy.status_page.slug }).first();
    const groups = [];
    if (page) {
        const rows = await db("group").where({ status_page_id: page.id })
            .select("id", "name", "weight").orderBy("weight").orderBy("id");
        for (const group of rows) {
            const members = await db("monitor_group as relation")
                .join("monitor", "monitor.id", "relation.monitor_id")
                .where("relation.group_id", group.id)
                .select("monitor.name").orderBy("relation.weight")
                .orderBy("relation.id");
            groups.push({ ...group, monitors: members.map(row => row.name) });
        }
    }
    const secret = await db("setting").where({ key: "jwtSecret" }).first();
    if (!secret) throw new Error("Uptime Kuma JWT secret is absent");
    await db.destroy();
    const fingerprint = crypto.createHash("sha256").update(JSON.stringify(stable({
        monitors, monitorNotifications, page: page ? {
            id: page.id, slug: page.slug, title: page.title,
        } : null, groups,
    }))).digest("hex");
    return {
        version, user, notification: notifications[0], monitors,
        monitorNotifications, page, groups, secret: secret.value, fingerprint,
    };
}

function buildPlan(state) {
    const policy = payload.policy;
    const major = Number(state.version.split(".")[0]);
    if (major !== policy.uptime_kuma_major) throw new Error(
        `policy supports Uptime Kuma major ${policy.uptime_kuma_major}, found ${state.version}`);
    const claimed = new Set();
    const matches = new Map();
    const adds = [];
    const updates = [];
    for (const desired of policy.monitors) {
        const names = new Set([desired.name, ...(policy.previous_names[desired.name] || [])]);
        const candidates = state.monitors.filter(row => names.has(row.name));
        if (candidates.length > 1) throw new Error(
            `${desired.name}: more than one current or previous name exists`);
        if (candidates.length === 0) {
            adds.push(desired.name);
            continue;
        }
        const current = candidates[0];
        claimed.add(current.id);
        matches.set(desired.name, current.id);
        const wanted = desiredFields(desired, policy.defaults);
        const changed = [];
        for (const [field, value] of Object.entries(wanted)) {
            if (!equal(current[field], value)) changed.push(field);
        }
        const notificationIDs = state.monitorNotifications
            .filter(row => row.monitor_id === current.id)
            .map(row => row.notification_id);
        if (!equal(notificationIDs, [state.notification.id])) changed.push("notification");
        if (changed.length) updates.push({
            id: current.id, name: desired.name, fields: changed.sort(),
        });
    }
    const extras = state.monitors.filter(row => !claimed.has(row.id))
        .map(row => ({ id: row.id, name: row.name }));
    const actualGroups = state.groups.map(group => ({
        name: group.name,
        monitors: group.monitors.map(name => canonicalName(name, policy)),
    }));
    const wantedPage = {
        slug: policy.status_page.slug,
        title: policy.status_page.title,
    };
    const currentPage = state.page ? {
        slug: state.page.slug, title: state.page.title,
    } : null;
    const statusPage = !equal(currentPage, wantedPage) ||
        !equal(actualGroups, policy.status_page.groups);
    return {
        fingerprint: state.fingerprint,
        adds, updates, extras, statusPage,
        hasChanges: Boolean(adds.length || updates.length || extras.length || statusPage),
        matches: Object.fromEntries(matches),
    };
}

function updateMonitorObject(current, desired, defaults, notificationID) {
    current.name = desired.name;
    current.type = desired.type;
    current.interval = defaults.interval_seconds;
    current.maxretries = defaults.retries;
    current.retryInterval = defaults.retry_interval_seconds;
    current.resendInterval = defaults.resend_interval_seconds;
    current.timeout = defaults.timeout_seconds;
    current.method = "GET";
    current.ignoreTls = false;
    current.expiryNotification = desired.type === "http" && defaults.http_expiry_notification;
    current.upsideDown = Boolean(desired.expected_failure);
    current.packetSize = defaults.ping_packet_size;
    current.maxredirects = defaults.max_redirects;
    current.accepted_statuscodes = defaults.accepted_status_codes;
    current.notificationIDList = { [notificationID]: true };
    current.url = desired.type === "http" ? desired.url : null;
    current.hostname = ["port", "ping"].includes(desired.type) ? desired.hostname : null;
    current.port = desired.type === "port" ? desired.port : null;
    if (desired.type === "dns") {
        current.hostname = desired.query;
        current.port = desired.port;
        current.dns_resolve_type = desired.record_type;
        current.dns_resolve_server = desired.resolver;
    }
    if (!Array.isArray(current.kafkaProducerBrokers)) current.kafkaProducerBrokers = [];
    if (!current.kafkaProducerSaslOptions || typeof current.kafkaProducerSaslOptions !== "object") {
        current.kafkaProducerSaslOptions = {};
    }
    return current;
}

function newMonitor(desired, defaults, notificationID) {
    return updateMonitorObject({
        description: "",
        parent: null,
        url: null,
        method: "GET",
        body: null,
        headers: null,
        basic_auth_user: null,
        basic_auth_pass: null,
        keyword: null,
        invertKeyword: false,
        dns_resolve_type: "A",
        dns_resolve_server: "1.1.1.1",
        proxyId: null,
        kafkaProducerBrokers: [],
        kafkaProducerSaslOptions: {},
        active: true,
    }, desired, defaults, notificationID);
}

async function connect(state) {
    const token = jwt.sign({
        username: state.user.username,
        h: shake256(state.user.password, SHAKE256_LENGTH),
    }, state.secret);
    const socket = io("http://127.0.0.1:3001", { transports: ["websocket"] });
    await new Promise((resolve, reject) => {
        socket.once("connect", resolve);
        socket.once("connect_error", reject);
    });
    const call = (event, ...args) => new Promise((resolve, reject) =>
        socket.emit(event, ...args, result => result && result.ok
            ? resolve(result)
            : reject(new Error((result && result.msg) || `${event} failed`))));
    await call("loginByToken", token);
    return { socket, call };
}

async function applyPlan(state, plan) {
    if (plan.fingerprint !== payload.expectedFingerprint) throw new Error(
        "live configuration changed after the audit; run the audit again");
    if (plan.extras.length && !payload.prune) throw new Error(
        "unmanaged monitors exist; rerun with --prune after reviewing the dry run");
    const { socket, call } = await connect(state);
    const ids = new Map(Object.entries(plan.matches));
    const desiredByName = new Map(payload.policy.monitors.map(item => [item.name, item]));
    try {
        for (const update of plan.updates) {
            const current = (await call("getMonitor", update.id)).monitor;
            const desired = desiredByName.get(update.name);
            updateMonitorObject(current, desired, payload.policy.defaults, state.notification.id);
            await call("editMonitor", current);
            if (desired.active !== false && !state.monitors.find(row => row.id === update.id).active) {
                await call("resumeMonitor", update.id);
            }
            ids.set(desired.name, update.id);
        }
        for (const name of plan.adds) {
            const desired = desiredByName.get(name);
            const result = await call("add", newMonitor(
                desired, payload.policy.defaults, state.notification.id));
            ids.set(name, result.monitorID);
        }
        if (plan.statusPage || plan.adds.length || plan.updates.length || plan.extras.length) {
            let status;
            try {
                status = (await call("getStatusPage", payload.policy.status_page.slug)).config;
            } catch (error) {
                await call("addStatusPage", payload.policy.status_page.title,
                    payload.policy.status_page.slug);
                status = (await call("getStatusPage", payload.policy.status_page.slug)).config;
            }
            status.slug = payload.policy.status_page.slug;
            status.title = payload.policy.status_page.title;
            const groups = payload.policy.status_page.groups.map((group, index) => {
                const exact = state.groups.find(item => item.name === group.name);
                const prior = state.groups[index];
                const result = {
                    name: group.name,
                    monitorList: group.monitors.map(name => ({
                        id: Number(ids.get(name)), sendUrl: false,
                    })),
                };
                if (exact || prior) result.id = (exact || prior).id;
                return result;
            });
            for (const group of groups) for (const monitor of group.monitorList) {
                if (!monitor.id) throw new Error(`missing monitor for status group ${group.name}`);
            }
            await call("saveStatusPage", payload.policy.status_page.slug,
                status, status.logo || "", groups);
        }
        if (payload.prune) {
            for (const extra of plan.extras) await call("deleteMonitor", extra.id);
        }
    } finally {
        socket.close();
    }
    return {
        added: plan.adds,
        updated: plan.updates.map(item => item.name),
        pruned: payload.prune ? plan.extras.map(item => item.name) : [],
        statusPageUpdated: plan.statusPage,
    };
}

(async () => {
    const state = await readState();
    const plan = buildPlan(state);
    const result = payload.mode === "apply" ? await applyPlan(state, plan) : plan;
    console.log("RECONCILE_RESULT=" + JSON.stringify(result));
    process.exit(0);
})().catch(error => {
    console.error("RECONCILE_ERROR=" + error.message);
    process.exit(1);
});
'''


def read_json(path):
    with path.open(encoding='utf-8') as handle:
        return json.load(handle)


def read_env(path):
    values = {}
    for number, raw in enumerate(path.read_text().splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            raise ValueError(f'{path}:{number}: expected KEY=VALUE')
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        values[key] = value
    return values


def validate_policy(policy):
    required = {'schema_version', 'uptime_kuma_major', 'inputs', 'defaults',
                'previous_names', 'status_page', 'monitors'}
    missing = sorted(required - set(policy))
    if missing:
        raise ValueError('policy fields absent: ' + ', '.join(missing))
    if policy['schema_version'] != 1:
        raise ValueError('unsupported policy schema_version')
    monitors = policy['monitors']
    names = [item.get('name') for item in monitors]
    if not names or any(not isinstance(name, str) or not name for name in names):
        raise ValueError('every monitor requires a non-empty name')
    if len(names) != len(set(names)):
        raise ValueError('monitor names must be unique')
    previous = policy['previous_names']
    if not set(previous).issubset(names):
        raise ValueError('previous_names contains an unknown current monitor name')
    identities = set(names)
    for current, old_names in previous.items():
        if not isinstance(old_names, list) or any(
                not isinstance(name, str) or not name for name in old_names):
            raise ValueError(f'{current}: previous names must be non-empty strings')
        for old in old_names:
            if old in identities:
                raise ValueError(f'duplicate current or previous monitor name: {old}')
            identities.add(old)
    allowed_types = {'http', 'port', 'ping', 'dns'}
    for monitor in monitors:
        monitor_type = monitor.get('type')
        if monitor_type not in allowed_types:
            raise ValueError(f"{monitor['name']}: unsupported type {monitor_type!r}")
        if not isinstance(monitor.get('target'), str) or not monitor['target']:
            raise ValueError(f"{monitor['name']}: target is required")
        if monitor_type == 'dns':
            for field in ('query', 'record_type', 'expected_failure'):
                if field not in monitor:
                    raise ValueError(f"{monitor['name']}: {field} is required")
    groups = policy['status_page'].get('groups', [])
    grouped = [name for group in groups for name in group.get('monitors', [])]
    if len(grouped) != len(set(grouped)):
        raise ValueError('a monitor appears in more than one status-page group')
    if set(grouped) != set(names):
        raise ValueError('status-page membership must contain every monitor exactly once')
    inputs = policy['inputs']
    if not isinstance(inputs.get('public_domain_env'), str):
        raise ValueError('inputs.public_domain_env is required')
    hosts = inputs.get('host_env', {})
    if not isinstance(hosts, dict) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in hosts.items()):
        raise ValueError('inputs.host_env must map logical hosts to environment keys')


def require_env(values, name):
    value = values.get(name, '').strip()
    if not value:
        raise ValueError(f'required private input is absent: {name}')
    return value


def is_test_address(value):
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return False
    return any(address in network for network in TEST_NETWORKS)


def resolve_policy(policy, environment, allow_placeholders=False):
    validate_policy(policy)
    resolved = json.loads(json.dumps(policy))
    inputs = policy['inputs']
    domain = require_env(environment, inputs['public_domain_env']).rstrip('.')
    if '://' in domain or '/' in domain:
        raise ValueError('UPTIME_KUMA_PUBLIC_DOMAIN must be a hostname only')
    if not allow_placeholders and domain == 'example.com':
        raise ValueError('refusing placeholder UPTIME_KUMA_PUBLIC_DOMAIN')
    hosts = {}
    for logical, env_name in inputs['host_env'].items():
        value = require_env(environment, env_name)
        if '://' in value or '/' in value or ':' in value:
            raise ValueError(f'{env_name} must be an IPv4 address or hostname')
        if not allow_placeholders and is_test_address(value):
            raise ValueError(f'refusing placeholder {env_name}')
        hosts[logical] = value
    for monitor in resolved['monitors']:
        target = monitor.pop('target')
        if monitor['type'] == 'http':
            parts = urlsplit(target)
            if parts.scheme not in {'http', 'https'} or not parts.hostname:
                raise ValueError(f"{monitor['name']}: invalid HTTP target")
            if parts.hostname == 'example.com':
                hostname = domain
            elif parts.hostname.endswith('.example.com'):
                hostname = parts.hostname[:-len('example.com')] + domain
            else:
                raise ValueError(f"{monitor['name']}: HTTP target must use example.com")
            netloc = hostname + (f':{parts.port}' if parts.port else '')
            monitor['url'] = urlunsplit(
                (parts.scheme, netloc, parts.path, parts.query, parts.fragment))
        elif monitor['type'] == 'ping':
            if target not in hosts:
                raise ValueError(f"{monitor['name']}: unknown logical host {target}")
            monitor['hostname'] = hosts[target]
        else:
            logical, separator, port = target.rpartition(':')
            if not separator or logical not in hosts:
                raise ValueError(f"{monitor['name']}: target must be logical-host:port")
            try:
                port_number = int(port)
            except ValueError as error:
                raise ValueError(f"{monitor['name']}: invalid target port") from error
            if not 1 <= port_number <= 65535:
                raise ValueError(f"{monitor['name']}: target port is out of range")
            monitor['port'] = port_number
            if monitor['type'] == 'dns':
                monitor['resolver'] = hosts[logical]
            else:
                monitor['hostname'] = hosts[logical]
    return resolved


def redact(text, environment, policy):
    sensitive = []
    inputs = policy.get('inputs', {})
    keys = [inputs.get('public_domain_env')] + list(inputs.get('host_env', {}).values())
    for key in keys:
        if key and environment.get(key):
            sensitive.append(environment[key])
    result = text
    for value in sorted(sensitive, key=len, reverse=True):
        result = result.replace(value, '<private-input>')
    return result


def run_node(container, payload, environment, policy):
    encoded = base64.b64encode(json.dumps(payload, separators=(',', ':')).encode()).decode()
    program = NODE_PROGRAM.replace('__PAYLOAD_B64__', encoded)
    docker = shutil.which('docker')
    if not docker:
        raise RuntimeError('docker CLI is required')
    result = subprocess.run(
        [docker, 'exec', '-i', container, 'node', '-'], input=program,
        text=True, capture_output=True, timeout=120)
    marker = 'RECONCILE_RESULT='
    line = next((item for item in result.stdout.splitlines()
                 if item.startswith(marker)), None)
    if result.returncode or line is None:
        detail = '\n'.join(value for value in (result.stdout, result.stderr) if value).strip()
        raise RuntimeError(redact(detail or 'Uptime Kuma reconcile failed', environment, policy))
    return json.loads(line[len(marker):])


def write_new(path, data, mode=0o600):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
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


def backup_database(data_dir, backup_root, config_path, env_path):
    source_path = data_dir / 'kuma.db'
    if not source_path.is_file():
        raise RuntimeError(f'Uptime Kuma database is absent: {source_path}')
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    destination = backup_root / f'pre-monitor-reconcile-{timestamp}'
    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    backup_path = destination / 'kuma.db'
    source = sqlite3.connect(f'file:{source_path}?mode=ro', uri=True)
    backup = sqlite3.connect(backup_path)
    try:
        source.backup(backup)
        if backup.execute('pragma quick_check').fetchone()[0] != 'ok':
            raise RuntimeError('backup SQLite quick_check failed')
    finally:
        backup.close()
        source.close()
    files = [backup_path]
    for path in (ROOT / 'docker-compose.yml', config_path, ROOT / 'reconcile.py', env_path):
        if path.is_file():
            target = destination / path.name
            shutil.copy2(path, target)
            files.append(target)
    lines = []
    for path in files:
        os.chmod(path, 0o600)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f'{digest}  {path.name}\n')
    write_new(destination / 'SHA256SUMS', ''.join(lines).encode())
    return destination


def print_plan(plan):
    print('changes_required=' + str(plan['hasChanges']).lower())
    print('would_add=' + (','.join(plan['adds']) if plan['adds'] else 'none'))
    updates = [f"{item['name']}({','.join(item['fields'])})" for item in plan['updates']]
    print('would_update=' + (','.join(updates) if updates else 'none'))
    print('would_prune=' + (','.join(item['name'] for item in plan['extras'])
                            if plan['extras'] else 'none'))
    print('would_update_status_page=' + str(plan['statusPage']).lower())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG)
    parser.add_argument('--env-file', type=Path, default=DEFAULT_ENV)
    parser.add_argument('--container', default='uptime-kuma')
    parser.add_argument('--data-dir', type=Path, default=DEFAULT_DATA)
    parser.add_argument('--backup-dir', type=Path, default=DEFAULT_BACKUPS)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--prune', action='store_true')
    parser.add_argument('--check-config', action='store_true')
    args = parser.parse_args()
    if args.check_config and (args.apply or args.prune):
        parser.error('--check-config cannot be combined with --apply or --prune')
    policy = read_json(args.config)
    environment = read_env(args.env_file)
    resolved = resolve_policy(policy, environment,
                              allow_placeholders=args.check_config)
    if args.check_config:
        print(f"configuration=valid monitors={len(resolved['monitors'])} "
              f"groups={len(resolved['status_page']['groups'])}")
        return
    audit = run_node(args.container, {
        'mode': 'audit', 'policy': resolved, 'prune': args.prune,
    }, environment, policy)
    print_plan(audit)
    if not args.apply:
        return
    if not audit['hasChanges']:
        print('applied=none')
        print('verified=idempotent')
        return
    if audit['extras'] and not args.prune:
        raise RuntimeError('unmanaged monitors exist; review the dry run and add --prune')
    backup = backup_database(args.data_dir, args.backup_dir,
                             args.config, args.env_file)
    print(f'backup={backup}')
    applied = run_node(args.container, {
        'mode': 'apply', 'policy': resolved, 'prune': args.prune,
        'expectedFingerprint': audit['fingerprint'],
    }, environment, policy)
    print('added=' + (','.join(applied['added']) if applied['added'] else 'none'))
    print('updated=' + (','.join(applied['updated']) if applied['updated'] else 'none'))
    print('pruned=' + (','.join(applied['pruned']) if applied['pruned'] else 'none'))
    print('status_page_updated=' + str(applied['statusPageUpdated']).lower())
    verified = run_node(args.container, {
        'mode': 'audit', 'policy': resolved, 'prune': True,
    }, environment, policy)
    if verified['hasChanges']:
        raise RuntimeError('post-apply verification found remaining drift')
    print('verified=idempotent')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, sqlite3.Error,
            subprocess.SubprocessError) as error:
        print(f'error: {error}', file=sys.stderr)
        raise SystemExit(1)
