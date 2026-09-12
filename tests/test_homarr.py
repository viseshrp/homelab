"""Offline contract tests for the Falling Rock Homarr board."""

import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load_reconciler():
    path = ROOT / "configs/homarr/reconcile-board.py"
    spec = importlib.util.spec_from_file_location("homarr_reconciler", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HomarrPolicyTests(unittest.TestCase):
    def setUp(self):
        self.board = json.loads((ROOT / "configs/homarr/vis.json").read_text())
        self.kuma = json.loads(
            (ROOT / "configs/uptime-kuma/monitors.json").read_text()
        )

    def test_every_kuma_application_has_a_board_tile(self):
        kuma_apps = {
            monitor["name"]
            for monitor in self.kuma["monitors"]
            if monitor["type"] in {"http", "port"}
        }
        kuma_apps.remove("Pi-hole Web")
        kuma_apps.add("Pi-hole")

        board_apps = {app["name"] for app in self.board["apps"]}
        self.assertEqual(board_apps - kuma_apps, {"Paperless"})
        self.assertEqual(kuma_apps - board_apps, set())

        by_name = {app["name"]: app for app in self.board["apps"]}
        for name in kuma_apps:
            with self.subTest(name=name):
                self.assertTrue(by_name[name]["network"]["enabledStatusChecker"])

    def test_board_application_ids_and_positions_are_unique(self):
        apps = self.board["apps"]
        ids = [app["id"] for app in apps]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(apps), 22)

        for breakpoint in ("md", "lg"):
            positions = [
                (
                    app["area"]["properties"]["location"],
                    app["shape"][breakpoint]["location"]["x"],
                    app["shape"][breakpoint]["location"]["y"],
                )
                for app in apps
            ]
            self.assertEqual(len(positions), len(set(positions)))

    def test_deployment_keeps_template_separate_from_private_board(self):
        manifest = json.loads((ROOT / "deployments.json").read_text())
        assets = manifest["homarr"]["assets"]
        self.assertEqual(
            assets["configs/homarr/vis.json"], "homarr/templates/vis.json"
        )
        self.assertEqual(
            assets["configs/homarr/reconcile-board.py"], "reconcile-board.py"
        )
        self.assertNotIn("homarr/configs/vis.json", assets.values())


class HomarrReconcilerTests(unittest.TestCase):
    def test_merge_preserves_private_state_and_adds_missing_apps(self):
        reconciler = load_reconciler()
        full = json.loads((ROOT / "configs/homarr/vis.json").read_text())
        wanted = {"Planka", "Homebridge", "Anki", "Scrutiny"}
        desired = {
            "apps": [app for app in full["apps"] if app["name"] in wanted]
        }
        live = {
            "apps": [
                {
                    "id": "private-planka-id",
                    "name": "boards",
                    "url": "http://private-lan/planka",
                    "behaviour": {
                        "externalUrl": "https://boards.example.net/private-path"
                    },
                    "network": {"enabledStatusChecker": False},
                    "integration": {"properties": [{"field": "private-value"}]},
                    "shape": {"lg": {"location": {"x": 7, "y": 3}}},
                },
                {
                    "id": "private-homebridge-id",
                    "name": "homebridge",
                    "url": "http://private-lan/homebridge",
                    "behaviour": {"externalUrl": "http://private-lan/homebridge"},
                    "network": {"enabledStatusChecker": False},
                },
            ],
            "widgets": [{"properties": {"credential": "private-widget-value"}}],
        }

        merged, summary = reconciler.merge_board(desired, live)
        by_name = {app["name"]: app for app in merged["apps"]}
        self.assertEqual(summary["added"], ["Anki", "Scrutiny"])
        self.assertEqual(
            merged["widgets"], [{"properties": {"credential": "private-widget-value"}}]
        )
        self.assertEqual(by_name["Planka"]["url"], "http://private-lan/planka")
        self.assertEqual(
            by_name["Planka"]["integration"]["properties"][0]["field"],
            "private-value",
        )
        self.assertEqual(
            by_name["Planka"]["shape"]["lg"]["location"], {"x": 7, "y": 3}
        )
        self.assertEqual(by_name["Anki"]["url"], "https://anki.example.net/health")
        self.assertEqual(
            by_name["Anki"]["behaviour"]["externalUrl"],
            "https://anki.example.net",
        )
        self.assertEqual(by_name["Scrutiny"]["url"], "http://rpimon:8083")
        self.assertTrue(by_name["Homebridge"]["network"]["enabledStatusChecker"])


if __name__ == "__main__":
    unittest.main()
