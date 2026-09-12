#!/usr/bin/env python3
"""Audit or reconcile Uptime Kuma's default ntfy notification."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent
DEFAULT_POLICY = ROOT / 'notification.json'
DEFAULT_ENV = ROOT / '.env'
DEFAULT_DATA = ROOT / 'uptime-kuma-data'
DEFAULT_BACKUPS = ROOT / 'backups'
DEFAULT_MONITOR_RECONCILER = ROOT / 'reconcile.py'
DEFAULT_MONITOR_POLICY = ROOT / 'monitors.json'


NODE_PROGRAM = r'''
const fs = require("fs");
const crypto = require("crypto");
const knex = require("knex");
const Dialect = require("knex/lib/dialects/sqlite3/index.js");
Dialect.prototype._driver = () => require("@louislam/sqlite3");
const jwt = require("jsonwebtoken");
const { shake256, SHAKE256_LENGTH } = require("./server/util-server");
const { io } = require("socket.io-client");

const payload = JSON.parse(fs.readFileSync(0, "utf8"));
const CONFIG_KEYS = [
    "name", "type", "ntfyserverurl", "ntfytopic",
    "ntfyAuthenticationMethod", "ntfyaccesstoken", "ntfyPriority"
];

function equal(left, right) {
    return JSON.stringify(left) === JSON.stringify(right);
}

function parseConfig(row) {
    const config = JSON.parse(row.config);
    return { ...row, parsed: config };
}

function configMatches(row, desired) {
    return CONFIG_KEYS.every(key => equal(row.parsed[key], desired[key]));
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
    const notifications = (await db("notification")
        .where({ user_id: user.id }).orderBy("id")).map(parseConfig);
    const monitors = await db("monitor").where({ user_id: user.id })
        .select("id").orderBy("id");
    const links = await db("monitor_notification")
        .select("monitor_id", "notification_id")
        .orderBy("monitor_id").orderBy("notification_id");
    const secret = await db("setting").where({ key: "jwtSecret" }).first();
    if (!secret) throw new Error("Uptime Kuma JWT secret is absent");
    await db.destroy();

    const desiredRows = notifications.filter(row =>
        row.parsed.name === payload.notification.name &&
        row.parsed.type === payload.notification.type);
    if (desiredRows.length > 1) throw new Error(
        "more than one notification matches the declared ntfy identity");
    const desired = desiredRows[0] || null;
    const other = notifications.filter(row => !desired || row.id !== desired.id);
    const configurationMatches = Boolean(desired &&
        desired.active === 1 && desired.is_default === 1 &&
        configMatches(desired, payload.notification));
    const allMonitorsLinked = Boolean(desired && monitors.every(monitor => {
        const ids = links.filter(link => link.monitor_id === monitor.id)
            .map(link => link.notification_id);
        return equal(ids, [desired.id]);
    }));
    const fingerprint = crypto.createHash("sha256").update(JSON.stringify({
        notifications: notifications.map(row => ({
            id: row.id, active: row.active, is_default: row.is_default,
            config: row.config,
        })),
        links,
    })).digest("hex");
    return {
        version, user, secret: secret.value, notifications, desired, other,
        monitorCount: monitors.length, configurationMatches,
        allMonitorsLinked, fingerprint,
    };
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

function publicAudit(state) {
    const pruneNeeded = payload.prune && state.other.length > 0;
    return {
        fingerprint: state.fingerprint,
        changesRequired: !state.configurationMatches ||
            !state.allMonitorsLinked || pruneNeeded,
        providerConfigured: state.configurationMatches,
        allMonitorsLinked: state.allMonitorsLinked,
        monitorCount: state.monitorCount,
        otherNotifications: state.other.map(row => row.parsed.name || "unnamed"),
    };
}

async function configure(state) {
    if (payload.expectedFingerprint !== state.fingerprint) throw new Error(
        "live notification configuration changed after the audit");
    const client = await connect(state);
    try {
        await client.call("testNotification", payload.notification);
        const first = await client.call(
            "addNotification",
            { ...payload.notification, isDefault: false, applyExisting: false },
            state.desired ? state.desired.id : null);
        const desiredID = state.desired ? state.desired.id : first.id;
        await client.call(
            "addNotification",
            { ...payload.notification, isDefault: true, applyExisting: true },
            desiredID);
        for (const row of state.other) {
            if (row.is_default === 1) {
                await client.call(
                    "addNotification",
                    { ...row.parsed, isDefault: false, applyExisting: false },
                    row.id);
            }
        }
        return { tested: true, desiredID };
    } finally {
        client.socket.disconnect();
    }
}

async function prune(state) {
    const client = await connect(state);
    try {
        const removed = [];
        for (const row of state.other) {
            await client.call("deleteNotification", row.id);
            removed.push(row.parsed.name || "unnamed");
        }
        return { removed };
    } finally {
        client.socket.disconnect();
    }
}

async function test(state) {
    const client = await connect(state);
    try {
        await client.call("testNotification", payload.notification);
        return { tested: true };
    } finally {
        client.socket.disconnect();
    }
}

(async () => {
    const state = await readState();
    const major = Number(state.version.split(".")[0]);
    if (major !== payload.uptimeKumaMajor) throw new Error(
        `policy supports Uptime Kuma major ${payload.uptimeKumaMajor}, found ${state.version}`);
    let result;
    if (payload.mode === "audit") result = publicAudit(state);
    else if (payload.mode === "configure") result = await configure(state);
    else if (payload.mode === "prune") result = await prune(state);
    else if (payload.mode === "test") result = await test(state);
    else throw new Error(`unknown mode ${payload.mode}`);
    console.log("NOTIFICATION_RESULT=" + JSON.stringify(result));
})().catch(error => {
    console.error(error && error.stack ? error.stack : String(error));
    process.exit(1);
});
'''


def read_json(path):
    with path.open() as handle:
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


def require_env(values, key):
    value = values.get(key, '').strip()
    if not value:
        raise ValueError(f'required private input is absent: {key}')
    return value


def resolve_policy(policy, environment, allow_placeholders=False):
    if policy.get('schema_version') != 1 or policy.get('type') != 'ntfy':
        raise ValueError('unsupported notification policy')
    if policy.get('authentication_method') != 'accessToken':
        raise ValueError('ntfy notification must use an access token')
    priority = policy.get('priority')
    if not isinstance(priority, int) or not 1 <= priority <= 5:
        raise ValueError('ntfy priority must be an integer from 1 through 5')
    server_url = require_env(environment, policy['server_url_env']).rstrip('/')
    parts = urlsplit(server_url)
    if (parts.scheme != 'https' or not parts.hostname or parts.path
            or parts.query or parts.fragment):
        raise ValueError('ntfy server URL must be an HTTPS origin')
    topic = require_env(environment, policy['topic_env'])
    token = require_env(environment, policy['access_token_env'])
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', topic):
        raise ValueError('ntfy topic contains unsupported characters')
    if not re.fullmatch(r'tk_[a-z0-9]{29}', token):
        raise ValueError('ntfy access token has an unexpected format')
    if not allow_placeholders and ('example.com' in server_url or 'REPLACE_' in topic):
        raise ValueError('refusing placeholder ntfy inputs')
    return {
        'name': policy['name'],
        'type': 'ntfy',
        'ntfyserverurl': server_url,
        'ntfytopic': topic,
        'ntfyAuthenticationMethod': 'accessToken',
        'ntfyaccesstoken': token,
        'ntfyPriority': priority,
    }


def redact(text, notification):
    result = text
    for value in sorted(notification.values(), key=lambda item: len(str(item)),
                        reverse=True):
        if isinstance(value, str) and value:
            result = result.replace(value, '<private-input>')
    return result


def run_node(container, payload, notification):
    docker = shutil.which('docker')
    if not docker:
        raise RuntimeError('docker CLI is required')
    result = subprocess.run(
        [docker, 'exec', '-i', container, 'node', '-e', NODE_PROGRAM],
        input=json.dumps(payload, separators=(',', ':')), text=True,
        capture_output=True, timeout=120)
    marker = 'NOTIFICATION_RESULT='
    line = next((item for item in result.stdout.splitlines()
                 if item.startswith(marker)), None)
    if result.returncode or line is None:
        detail = '\n'.join(
            value for value in (result.stdout, result.stderr) if value).strip()
        raise RuntimeError(redact(
            detail or 'Uptime Kuma notification reconcile failed', notification))
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


def backup_database(data_dir, backup_root, files):
    source_path = data_dir / 'kuma.db'
    if not source_path.is_file():
        raise RuntimeError(f'Uptime Kuma database is absent: {source_path}')
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    destination = backup_root / f'pre-notification-reconcile-{timestamp}'
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
    copied = [backup_path]
    for path in files:
        if path.is_file():
            target = destination / path.name
            shutil.copy2(path, target)
            copied.append(target)
    lines = []
    for path in copied:
        os.chmod(path, 0o600)
        lines.append(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n')
    write_new(destination / 'SHA256SUMS', ''.join(lines).encode())
    return destination


def print_audit(audit):
    print('changes_required=' + str(audit['changesRequired']).lower())
    print('provider_configured=' + str(audit['providerConfigured']).lower())
    print('all_monitors_linked=' + str(audit['allMonitorsLinked']).lower())
    print('monitor_count=' + str(audit['monitorCount']))
    print('other_notifications=' + (
        ','.join(audit['otherNotifications'])
        if audit['otherNotifications'] else 'none'))


def run_monitor_reconcile(args):
    command = [
        sys.executable, str(args.monitor_reconciler),
        '--config', str(args.monitor_policy),
        '--env-file', str(args.env_file),
        '--container', args.container,
        '--data-dir', str(args.data_dir),
        '--backup-dir', str(args.backup_dir),
        '--apply', '--prune',
    ]
    result = subprocess.run(command, text=True, check=False)
    if result.returncode:
        raise RuntimeError('monitor reconciliation failed after ntfy configuration')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--policy', type=Path, default=DEFAULT_POLICY)
    parser.add_argument('--env-file', type=Path, default=DEFAULT_ENV)
    parser.add_argument('--container', default='uptime-kuma')
    parser.add_argument('--data-dir', type=Path, default=DEFAULT_DATA)
    parser.add_argument('--backup-dir', type=Path, default=DEFAULT_BACKUPS)
    parser.add_argument('--monitor-reconciler', type=Path,
                        default=DEFAULT_MONITOR_RECONCILER)
    parser.add_argument('--monitor-policy', type=Path,
                        default=DEFAULT_MONITOR_POLICY)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--prune', action='store_true')
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--check-config', action='store_true')
    args = parser.parse_args()
    if args.check_config and (args.apply or args.prune or args.test):
        parser.error('--check-config cannot be combined with mutation or test flags')

    policy = read_json(args.policy)
    environment = read_env(args.env_file)
    notification = resolve_policy(
        policy, environment, allow_placeholders=args.check_config)
    if args.check_config:
        print('configuration=valid provider=ntfy authentication=accessToken')
        return

    base_payload = {
        'notification': notification,
        'uptimeKumaMajor': policy['uptime_kuma_major'],
        'prune': args.prune,
    }
    audit = run_node(args.container, {**base_payload, 'mode': 'audit'}, notification)
    print_audit(audit)

    if args.test and not args.apply:
        run_node(args.container, {**base_payload, 'mode': 'test'}, notification)
        print('notification_test=sent')
        return
    if not args.apply:
        return
    if not audit['changesRequired']:
        if args.test:
            run_node(args.container, {**base_payload, 'mode': 'test'}, notification)
            print('notification_test=sent')
        print('applied=none')
        print('verified=idempotent')
        return

    backup = backup_database(args.data_dir, args.backup_dir, [
        ROOT / 'docker-compose.yml', args.policy,
        ROOT / 'reconcile-notification.py', args.monitor_reconciler,
        args.monitor_policy, args.env_file,
    ])
    print(f'backup={backup}')
    configured = run_node(args.container, {
        **base_payload, 'mode': 'configure',
        'expectedFingerprint': audit['fingerprint'],
    }, notification)
    if not configured.get('tested'):
        raise RuntimeError('ntfy test message was not confirmed')
    print('notification_test=sent')
    print('provider_saved=true')

    run_monitor_reconcile(args)
    if args.prune:
        pruned = run_node(
            args.container, {**base_payload, 'mode': 'prune'}, notification)
        print('notifications_pruned=' + (
            ','.join(pruned['removed']) if pruned['removed'] else 'none'))

    verified = run_node(
        args.container, {**base_payload, 'mode': 'audit'}, notification)
    print_audit(verified)
    if verified['changesRequired']:
        raise RuntimeError('post-apply notification audit found remaining drift')
    print('verified=idempotent')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, sqlite3.Error,
            subprocess.SubprocessError) as error:
        print(f'error: {error}', file=sys.stderr)
        raise SystemExit(1)
