#!/usr/bin/env python3
"""Merge the sanitized Homarr board policy into a private live board.

Existing application objects, widgets, credentials, status URLs, and layout are
preserved. Canonical application names and status-check policy are updated, missing
applications are added, and an optional LAN policy sets every click URL to a direct
IP address without storing private addresses in the repository.
"""

import argparse
import copy
import ipaddress
import json
import os
from pathlib import Path
import tempfile
from urllib.parse import urlsplit


LEGACY_NAMES = {
    "Plex": {"plex"},
    "Firezone": {"firezone"},
    "Nginx Proxy Manager": {"npm"},
    "Planka": {"boards"},
    "Blog": {"blog"},
    "Linkding": {"links"},
    "File Browser - media3": {"filebrowser", "file browser"},
    "qBittorrent": {"qbit"},
    "ArchiveBox": {"archivebox"},
    "Pi-hole": {"pihole"},
    "Uptime Kuma": {"status"},
    "Homebridge": {"homebridge"},
    "Dozzle": {"dozzle"},
    "Home Assistant": {"hass"},
    "Vaultwarden": {"pass"},
    "Paperless": {"paperless"},
}

PUBLIC_SUBDOMAINS = {
    "Anki": "anki",
    "Homarr": "home",
    "Ntfy": "ntfy",
}

PUBLIC_STATUS_PATHS = {
    "Anki": "/health",
    "Ntfy": "/v1/health",
}

PRIVATE_TARGETS = {
    "File Browser - media2": "http://optiplex:8080",
    "PairDrop": "http://rpihass:3000",
    "WG-Easy": "http://vpn-edge:51821",
    "pywb": "http://rpimon:8082",
    "Scrutiny": "http://rpimon:8083",
}

RFC1918_NETWORKS = tuple(
    ipaddress.ip_network(network)
    for network in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
)


def load_json(path):
    return json.loads(Path(path).read_text())


def normalized_names(desired_app):
    names = {desired_app["name"].casefold()}
    names.update(name.casefold() for name in LEGACY_NAMES.get(desired_app["name"], set()))
    return names


def find_live_app(live_apps, desired_app, used):
    for index, app in enumerate(live_apps):
        if index in used:
            continue
        if app.get("id") == desired_app["id"]:
            return index
    accepted = normalized_names(desired_app)
    for index, app in enumerate(live_apps):
        if index not in used and str(app.get("name", "")).casefold() in accepted:
            return index
    return None


def derive_public_domain(live_apps):
    preferred = {"boards", "planka", "status", "uptime kuma", "links", "linkding"}
    candidates = sorted(
        live_apps,
        key=lambda app: str(app.get("name", "")).casefold() not in preferred,
    )
    for app in candidates:
        external = app.get("behaviour", {}).get("externalUrl") or app.get("url", "")
        host = urlsplit(external).hostname
        if not host or len(host.split(".")) < 3:
            continue
        try:
            ipaddress.ip_address(host)
        except ValueError:
            return ".".join(host.split(".")[1:])
    raise ValueError("could not derive the private public domain from an existing app URL")


def missing_urls(app_name, public_domain):
    if app_name in PRIVATE_TARGETS:
        return PRIVATE_TARGETS[app_name], PRIVATE_TARGETS[app_name]
    subdomain = PUBLIC_SUBDOMAINS.get(app_name)
    if subdomain:
        external = f"https://{subdomain}.{public_domain}"
        return external + PUBLIC_STATUS_PATHS.get(app_name, ""), external
    raise ValueError(f"no private URL rule exists for missing app: {app_name}")


def compile_lan_links(desired, policy, addresses):
    if policy.get("schemaVersion") != 1 or not isinstance(policy.get("apps"), dict):
        raise ValueError("LAN link policy must have schemaVersion 1 and an apps object")
    if addresses.get("schemaVersion") != 1 or not isinstance(
        addresses.get("hosts"), dict
    ):
        raise ValueError("LAN address input must have schemaVersion 1 and a hosts object")

    desired_names = {app["name"] for app in desired.get("apps", [])}
    policy_names = set(policy["apps"])
    if policy_names != desired_names:
        missing = sorted(desired_names - policy_names)
        extra = sorted(policy_names - desired_names)
        raise ValueError(f"LAN link policy app mismatch: missing={missing}, extra={extra}")

    parsed_addresses = {}
    for host, value in addresses["hosts"].items():
        try:
            address = ipaddress.ip_address(value)
        except ValueError as error:
            raise ValueError(f"LAN address for {host!r} is not an IP address") from error
        if address.version != 4 or not any(address in network for network in RFC1918_NETWORKS):
            raise ValueError(f"LAN address for {host!r} must be an RFC1918 IPv4 address")
        parsed_addresses[host] = str(address)

    links = {}
    for app_name, target in policy["apps"].items():
        if not isinstance(target, dict):
            raise ValueError(f"LAN link target for {app_name!r} must be an object")
        host = target.get("host")
        if host not in parsed_addresses:
            raise ValueError(f"LAN address is missing for host {host!r}")
        scheme = target.get("scheme", "http")
        if scheme not in {"http", "https"}:
            raise ValueError(f"unsupported LAN link scheme for {app_name!r}: {scheme!r}")
        port = target.get("port")
        if not isinstance(port, int) or isinstance(port, bool) or not 1 <= port <= 65535:
            raise ValueError(f"invalid LAN link port for {app_name!r}: {port!r}")
        path = target.get("path", "/")
        if not isinstance(path, str) or not path.startswith("/") or "?" in path or "#" in path:
            raise ValueError(f"invalid LAN link path for {app_name!r}: {path!r}")
        links[app_name] = f"{scheme}://{parsed_addresses[host]}:{port}{path}"
    return links


def audit(desired, live, lan_links=None):
    desired_apps = desired.get("apps", [])
    live_apps = live.get("apps", [])
    ids = [app.get("id") for app in live_apps]
    if len(ids) != len(set(ids)):
        raise ValueError("live board contains duplicate application IDs")

    by_name = {}
    for app in live_apps:
        by_name.setdefault(str(app.get("name", "")).casefold(), []).append(app)

    for app in desired_apps:
        matches = by_name.get(app["name"].casefold(), [])
        if len(matches) != 1:
            raise ValueError(f"expected exactly one live app named {app['name']!r}")
        expected = app.get("network", {}).get("enabledStatusChecker")
        actual = matches[0].get("network", {}).get("enabledStatusChecker")
        if actual != expected:
            raise ValueError(f"status-check policy differs for {app['name']!r}")
        if lan_links is not None:
            external = matches[0].get("behaviour", {}).get("externalUrl")
            if external != lan_links[app["name"]]:
                raise ValueError(f"LAN click URL differs for {app['name']!r}")
            try:
                ipaddress.ip_address(urlsplit(external).hostname)
            except ValueError as error:
                raise ValueError(f"LAN click URL is not IP-based for {app['name']!r}") from error

    return {"apps": len(live_apps), "required_apps": len(desired_apps)}


def merge_board(desired, live, public_domain=None, lan_links=None):
    result = copy.deepcopy(live)
    live_apps = result.setdefault("apps", [])
    used = set()
    added = []
    renamed = []
    links_updated = []

    missing_names = []
    for desired_app in desired.get("apps", []):
        index = find_live_app(live_apps, desired_app, used)
        if index is None:
            missing_names.append(desired_app["name"])

    if lan_links is None and any(name in PUBLIC_SUBDOMAINS for name in missing_names):
        public_domain = public_domain or derive_public_domain(live_apps)

    for desired_app in desired.get("apps", []):
        index = find_live_app(live_apps, desired_app, used)
        if index is None:
            new_app = copy.deepcopy(desired_app)
            if lan_links is None:
                status_url, external_url = missing_urls(desired_app["name"], public_domain)
            else:
                status_url = external_url = lan_links[desired_app["name"]]
            new_app["url"] = status_url
            new_app.setdefault("behaviour", {})["externalUrl"] = external_url
            live_apps.append(new_app)
            used.add(len(live_apps) - 1)
            added.append(desired_app["name"])
            continue

        used.add(index)
        current = live_apps[index]
        if current.get("name") != desired_app["name"]:
            renamed.append({"from": current.get("name"), "to": desired_app["name"]})
        current["name"] = desired_app["name"]
        current["network"] = copy.deepcopy(desired_app.get("network", {}))
        if lan_links is not None:
            expected_url = lan_links[desired_app["name"]]
            behaviour = current.setdefault("behaviour", {})
            if behaviour.get("externalUrl") != expected_url:
                links_updated.append(desired_app["name"])
            behaviour["externalUrl"] = expected_url

    audit(desired, result, lan_links)
    return result, {
        "added": added,
        "renamed": renamed,
        "linksUpdated": links_updated,
        "apps": len(live_apps),
    }


def write_atomic(path, value):
    path = Path(path)
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o600
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    os.chmod(temporary, mode)
    os.replace(temporary, path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--desired", required=True, type=Path)
    parser.add_argument("--live", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--public-domain")
    parser.add_argument("--lan-links", type=Path)
    parser.add_argument("--lan-addresses", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check == bool(args.output):
        parser.error("choose exactly one of --check or --output")
    if bool(args.lan_links) != bool(args.lan_addresses):
        parser.error("--lan-links and --lan-addresses must be used together")

    desired = load_json(args.desired)
    live = load_json(args.live)
    lan_links = None
    if args.lan_links:
        lan_links = compile_lan_links(
            desired, load_json(args.lan_links), load_json(args.lan_addresses)
        )
    if args.check:
        print(json.dumps(audit(desired, live, lan_links), sort_keys=True))
        return

    merged, summary = merge_board(desired, live, args.public_domain, lan_links)
    write_atomic(args.output, merged)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
