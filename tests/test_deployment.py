"""Deployment privacy/resource invariants without live network or paid requests."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
import io
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import app
from deploy import resource_guard


class MemorySocket:
    def __init__(self, request):
        self.input = io.BytesIO(request)
        self.output = bytearray()

    def makefile(self, *_args, **_kwargs):
        return self.input

    def sendall(self, data):
        self.output.extend(data)


class PublicServerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        for name, text in (("index.html", "<html>Public</html>"), ("library-sync.js", "window.publicAsset=true;"),
                           ("app.py", "PRIVATE SOURCE"), ("library.sqlite3", "PRIVATE DATABASE"),
                           (".env", "PRIVATE SECRET")):
            (self.root / name).write_text(text)

    def tearDown(self):
        self.directory.cleanup()

    def request(self, method, target):
        connection = MemorySocket(f"{method} {target} HTTP/1.1\r\nHost: house.example.test\r\nConnection: close\r\n\r\n".encode())
        with patch.object(app, "ROOT", self.root):
            app.Handler(connection, ("127.0.0.1", 1234), object(), directory=str(self.root))
        headers, _, body = bytes(connection.output).partition(b"\r\n\r\n")
        status = int(headers.split(b" ", 2)[1])
        return status, headers, body

    def test_get_and_head_never_serve_source_secrets_database_or_directories(self):
        forbidden = ("/app.py", "/library_server.py", "/library_admin.py", "/library.sqlite3", "/.env",
                     "/.git/config", "/deploy/backup.py", "/README.txt", "/requirements-sync.txt",
                     "/icons/", "/%61pp.py", "/index.html/../app.py", "/icons/../app.py", "/%2eenv")
        for method in ("GET", "HEAD"):
            for path in forbidden:
                with self.subTest(method=method, path=path):
                    status, _headers, body = self.request(method, path)
                    self.assertEqual(status, 404)
                    self.assertNotIn(b"PRIVATE", body)
                    if method == "HEAD":
                        self.assertEqual(body, b"")

    def test_public_assets_and_root_still_work(self):
        for path in ("/", "/index.html", "/library-sync.js?version=43"):
            self.assertEqual(self.request("GET", path)[0], 200)
            status, _headers, body = self.request("HEAD", path)
            self.assertEqual(status, 200)
            self.assertEqual(body, b"")
        self.assertIn(b"javascript", self.request("GET", "/library-sync.js")[1])


class MarketBoundsTests(unittest.TestCase):
    def setUp(self):
        app.MARKET_CACHE.clear()

    def tearDown(self):
        app.MARKET_CACHE.clear()

    def test_hour_cache_reuses_result_and_expired_cache_refreshes(self):
        with patch.object(app, "build_market", side_effect=[{"result": 1}, {"result": 2}]) as build:
            self.assertEqual(app.market("mammoth"), {"result": 1})
            self.assertEqual(app.market("mammoth"), {"result": 1})
            self.assertEqual(build.call_count, 1)
            app.MARKET_CACHE["mammoth"] = (time.monotonic() - 3601, {"result": 1})
            self.assertEqual(app.market("mammoth"), {"result": 2})
            self.assertEqual(build.call_count, 2)

    def test_simultaneous_same_market_fetches_once(self):
        gate = threading.Barrier(8)
        def build(_location, live=True):
            time.sleep(0.04)
            return {"live": live}
        def fetch(_index):
            gate.wait()
            return app.market("mammoth")
        with patch.object(app, "build_market", side_effect=build) as mocked:
            with ThreadPoolExecutor(8) as executor:
                results = list(executor.map(fetch, range(8)))
            self.assertEqual(mocked.call_count, 1)
            self.assertEqual(results, [{"live": True}] * 8)

    def test_distinct_markets_limit_live_fetches_to_three(self):
        gate, lock = threading.Barrier(8), threading.Lock()
        active = peak = 0
        def build(location, live=True):
            nonlocal active, peak
            if live:
                with lock:
                    active += 1
                    peak = max(peak, active)
                time.sleep(0.06)
                with lock:
                    active -= 1
            return {"location": location, "live": live}
        def fetch(location):
            gate.wait()
            return app.market(location)
        with patch.object(app, "build_market", side_effect=build):
            with ThreadPoolExecutor(8) as executor:
                results = list(executor.map(fetch, list(app.LOCATIONS)[:8]))
        self.assertEqual(peak, 3)
        self.assertEqual(sum(result["live"] for result in results), 3)

    def test_unknown_market_and_oversized_fetch_rejected(self):
        with self.assertRaises(ValueError):
            app.market("not-a-real-market")
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = b"x" * 6_000_001
        with patch.object(app, "urlopen", return_value=response) as opened:
            with self.assertRaises(ValueError):
                app.fetch("https://example.test/public-data")
            response.read.assert_called_once_with(6_000_001)
            self.assertEqual(opened.call_args.kwargs["timeout"], 10)

    def test_fallback_never_requests_external_sources(self):
        with patch.object(app, "fetch", side_effect=AssertionError("No outbound requests allowed")) as fetched:
            result = app.build_market("mammoth", live=False)
            fetched.assert_not_called()
        self.assertEqual(result["location_key"], "mammoth")
        self.assertGreater(result["mortgage_rate"], 0)


class ResourceGuardTests(unittest.TestCase):
    def test_usage_baseline_restart_reboot_and_month_rollover(self):
        state = resource_guard.usage_after(None, "2026-10", "boot1", 1000)
        self.assertEqual(state["bytes"], 0)
        state = resource_guard.usage_after(state, "2026-10", "boot1", 1400)
        self.assertEqual(state["bytes"], 400)
        state = resource_guard.usage_after(state, "2026-10", "boot1", 1400)
        self.assertEqual(state["bytes"], 400)
        state = resource_guard.usage_after(state, "2026-10", "boot2", 150)
        self.assertEqual(state["bytes"], 550)
        state = resource_guard.usage_after(state, "2026-11", "boot2", 200)
        self.assertEqual(state["bytes"], 50)
        state = resource_guard.usage_after(state, "2026-11", "boot2", 100)
        self.assertEqual(state["bytes"], 50)
        state = resource_guard.usage_after(state, "2026-11", "boot2", 120)
        self.assertEqual(state["bytes"], 70)

    def test_50_gib_pauses_and_pause_remains_sticky_after_month_rollover(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def mapped(value):
                return root / str(value).lstrip("/")
            files = {"/proc/net/route": "Iface Destination\nens3 00000000\n",
                     "/proc/sys/kernel/random/boot_id": "boot1\n",
                     "/sys/class/net/ens3/statistics/tx_bytes": "1000\n",
                     "/proc/meminfo": "MemAvailable: 5000000 kB\n"}
            for name, contents in files.items():
                path = mapped(name)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(contents)
            mapped("/var/lib").mkdir(parents=True)
            with patch.object(resource_guard, "Path", side_effect=mapped), patch.object(resource_guard.os, "umask"), \
                 patch.object(resource_guard.shutil, "disk_usage", return_value=SimpleNamespace(free=10 * resource_guard.GIB)), redirect_stdout(io.StringIO()):
                resource_guard.main()
                mapped("/sys/class/net/ens3/statistics/tx_bytes").write_text(str(1000 + 50 * resource_guard.GIB))
                resource_guard.main()
                marker = mapped("/var/lib/house-alpha-guard/paused")
                self.assertIn("50 GiB", marker.read_text())
                usage = mapped("/var/lib/house-alpha-guard/usage.json")
                state = json.loads(usage.read_text())
                self.assertEqual(state["bytes"], 50 * resource_guard.GIB)
                state["month"] = "1900-01"
                usage.write_text(json.dumps(state))
                resource_guard.main()
                self.assertTrue(json.loads(usage.read_text())["paused"])
                self.assertEqual(json.loads(usage.read_text())["bytes"], 0)


class BackupTests(unittest.TestCase):
    def test_snapshot_includes_wal_changes_and_retains_seven_private_backups(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            backups = root / "backups"
            backups.mkdir(mode=0o700)
            for days in range(1, 10):
                date = datetime.now(timezone.utc) - timedelta(days=days)
                (backups / date.strftime("library-%Y%m%d.sqlite3")).write_bytes(b"older backup")
            source = sqlite3.connect(root / "library.sqlite3")
            try:
                source.execute("PRAGMA journal_mode=WAL")
                source.execute("CREATE TABLE test_data(value TEXT)")
                source.execute("INSERT INTO test_data VALUES ('private saved property')")
                source.commit()
                # Execute the real backup program with only its root directory
                # redirected, leaving SQLite backup/integrity/retention intact.
                script = (app.ROOT / "deploy/backup.py").read_text()
                original = "root = Path('/var/lib/house-alpha')"
                self.assertEqual(script.count(original), 1)
                script = script.replace(original, "root = Path(" + repr(str(root)) + ")")
                previous_mask = os.umask(0o077)
                try:
                    with redirect_stdout(io.StringIO()):
                        exec(compile(script, "deploy/backup.py", "exec"), {})
                finally:
                    os.umask(previous_mask)
                files = sorted(backups.glob("library-*.sqlite3"))
                self.assertEqual(len(files), 7)
                self.assertFalse(list(backups.glob("*.tmp")))
                self.assertEqual(files[-1].stat().st_mode & 0o777, 0o600)
                with sqlite3.connect(files[-1]) as restored:
                    self.assertEqual(restored.execute("PRAGMA integrity_check").fetchone()[0], "ok")
                    self.assertEqual(restored.execute("SELECT value FROM test_data").fetchone()[0], "private saved property")
            finally:
                source.close()


if __name__ == "__main__":
    unittest.main()
