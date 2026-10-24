"""Security and persistence contracts for the synced property library.

Run: python -m unittest discover -s tests -p 'test_library.py' -v
"""
from concurrent.futures import ThreadPoolExecutor
import json
import os
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from library_server import (COOKIE_NAME, MAX_ITEMS, MAX_LIBRARY_BYTES, PASSWORD_METHOD,
                            connect_database, create_app, create_invite, token_hash)
from werkzeug.security import check_password_hash, generate_password_hash


ORIGIN = "https://house.example.test"
PASSWORD = "correct-horse-private-library"


def item(identifier="property-1", title="Test property"):
    return {"id": identifier, "title": title, "address": "123 Example Road",
            "snapshot": {"version": 1, "controls": {"price": {"value": "100000"}},
                         "flags": {}, "result": {"adv": 12.3}}}


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.directory.name, "library.sqlite3")
        self.config = {"TESTING": True, "DATABASE": self.path, "ORIGIN": ORIGIN,
                       "PASSWORD_METHOD": "scrypt:1024:8:1", "MIN_FREE_BYTES": 0}
        self.app = create_app(self.config)
        self.client = self.app.test_client()

    def tearDown(self):
        self.directory.cleanup()

    def get(self, path="/api/library", client=None, **kwargs):
        return (client or self.client).get(path, base_url=ORIGIN, **kwargs)

    def post(self, path, data=None, client=None, csrf=None, headers=None):
        request_headers = {"Origin": ORIGIN}
        if csrf:
            request_headers["X-CSRF-Token"] = csrf
        if headers:
            request_headers.update(headers)
        return (client or self.client).post(path, json=data or {}, headers=request_headers, base_url=ORIGIN)

    def register(self, username="alice", client=None, invite=None):
        return self.post("/api/library/register", {"username": username, "password": PASSWORD,
                         "invite": invite or create_invite(self.path)}, client=client)

    def login(self, username="alice", client=None):
        return self.post("/api/library/login", {"username": username, "password": PASSWORD}, client=client)

    def put(self, items=None, revision=0, client=None, csrf=None):
        if csrf is None:
            csrf = self.get("/api/library/session", client=client).json.get("csrfToken", "")
        return (client or self.client).put("/api/library", json={"revision": revision, "items": [item()] if items is None else items},
                                         headers={"Origin": ORIGIN, "X-CSRF-Token": csrf}, base_url=ORIGIN)

    def test_invite_registration_single_use_hashed_secrets_secure_cookie(self):
        invite = create_invite(self.path)
        response = self.register(invite=invite)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json["authenticated"])
        self.assertEqual(response.json["user"]["username"], "alice")
        cookie = response.headers["Set-Cookie"]
        for attribute in ("Secure", "HttpOnly", "SameSite=Lax", "Path=/"):
            self.assertIn(attribute, cookie)
        self.assertNotIn("Domain=", cookie)
        with connect_database(self.path) as db:
            user = db.execute("SELECT * FROM users").fetchone()
            self.assertTrue(check_password_hash(user["password_hash"], PASSWORD))
            session = db.execute("SELECT * FROM sessions").fetchone()
            token = self.client.get_cookie(COOKIE_NAME, domain="house.example.test").value
            self.assertNotEqual(token, session["token_hash"])
            self.assertEqual(token_hash(token), session["token_hash"])
            self.assertEqual(db.execute("SELECT token_hash FROM invites").fetchone()[0], token_hash(invite))
        other = self.app.test_client()
        self.assertEqual(self.register("other", other, invite).status_code, 403)

    def test_missing_expired_invite_and_closed_registration(self):
        self.assertEqual(self.post("/api/library/register", {"username": "alice", "password": PASSWORD}).status_code, 403)
        expired = create_invite(self.path, hours=-1)
        self.assertEqual(self.register(invite=expired).status_code, 403)
        self.app.config["REGISTRATION"] = "closed"
        self.assertEqual(self.register().json["error"], "registration_closed")

    def test_open_registration_bounded_account_limit(self):
        self.app.config.update(REGISTRATION="open", MAX_ACCOUNTS=1)
        self.assertEqual(self.register().status_code, 201)
        self.assertEqual(self.register("bobby", self.app.test_client()).json["error"], "account_limit")

    def test_duplicate_username_does_not_consume_invite(self):
        self.register()
        invite = create_invite(self.path)
        self.assertEqual(self.register(invite=invite).status_code, 409)
        self.assertEqual(self.register("bobby", self.app.test_client(), invite).status_code, 201)

    def test_login_logout_expiry_and_session_rotation(self):
        registration = self.register()
        old = self.client.get_cookie(COOKIE_NAME, domain="house.example.test").value
        logged_in = self.login()
        self.assertEqual(logged_in.status_code, 200)
        new = self.client.get_cookie(COOKIE_NAME, domain="house.example.test").value
        self.assertNotEqual(old, new)
        replay = self.app.test_client()
        replay.set_cookie(COOKIE_NAME, old, domain="house.example.test")
        self.assertFalse(self.get("/api/library/session", replay).json["authenticated"])
        self.assertEqual(self.post("/api/library/logout", csrf=logged_in.json["csrfToken"]).status_code, 200)
        self.assertEqual(self.get().status_code, 401)
        self.login()
        with connect_database(self.path) as db:
            db.execute("UPDATE sessions SET expires_at=?", (int(time.time()) - 1,))
        self.assertFalse(self.get("/api/library/session").json["authenticated"])

    def test_origin_and_csrf_required_for_mutations(self):
        self.assertEqual(self.client.post("/api/library/login", json={}, base_url=ORIGIN).status_code, 403)
        self.assertEqual(self.post("/api/library/register", headers={"Origin": "https://attacker.test"}).status_code, 403)
        csrf = self.register().json["csrfToken"]
        self.assertEqual(self.put(csrf="bad").status_code, 403)
        self.assertEqual(self.put(csrf="é").status_code, 403)
        self.assertEqual(self.post("/api/library/logout").status_code, 403)
        self.assertEqual(self.get(headers={"Sec-Fetch-Site": "cross-site"}).status_code, 403)
        self.assertEqual(self.put(csrf=csrf).status_code, 200)

    def test_account_isolation_and_export_identity(self):
        alice = self.register().json
        self.assertEqual(self.put().status_code, 200)
        bob = self.app.test_client()
        self.assertEqual(self.register("bobby", bob).status_code, 201)
        self.assertEqual(self.get(client=bob).json["items"], [])
        self.assertEqual(self.put([item("bob-private")], client=bob).status_code, 200)
        self.assertEqual(self.get().json["items"][0]["id"], "property-1")
        self.assertEqual(self.get(client=bob).json["items"][0]["id"], "bob-private")
        self.assertEqual(self.put(client=bob, revision=1, csrf=alice["csrfToken"]).status_code, 403)
        exported = self.get("/api/library/export")
        self.assertEqual(exported.json["user"]["id"], alice["user"]["id"])
        self.assertIn("attachment", exported.headers["Content-Disposition"])

    def test_optimistic_conflict_preserves_newer_data(self):
        self.register()
        self.assertEqual(self.put([item(title="Newer")]).json["revision"], 1)
        conflict = self.put([item(title="Stale")])
        self.assertEqual(conflict.status_code, 409)
        self.assertEqual(conflict.json["revision"], 1)
        self.assertEqual(self.get().json["items"][0]["title"], "Newer")

    def test_unchanged_revision_returns_identity_without_redownloading_items(self):
        user = self.register().json["user"]
        self.put()
        response = self.get("/api/library?revision=1")
        self.assertEqual(response.json, {"unchanged": True, "revision": 1, "user": user})
        self.assertEqual(response.headers["Cache-Control"], "no-store, private")
        self.assertEqual(self.get("/api/library?revision=0").json["items"], [item()])
        self.assertEqual(self.get("/api/library?revision=bad").json["items"], [item()])
        anonymous = self.app.test_client()
        self.assertEqual(self.get("/api/library?revision=1", anonymous).status_code, 401)
        bob = self.app.test_client()
        self.register("bobby", bob)
        self.assertEqual(self.get("/api/library?revision=1", bob).json["items"], [])

    def test_full_reads_exports_share_persistent_limit_but_unchanged_checks_are_exempt(self):
        user = self.register().json["user"]
        for count in range(10):
            path = "/api/library/export" if count % 2 else "/api/library"
            self.assertEqual(self.get(path).status_code, 200)
        self.assertEqual(self.get().status_code, 429)
        self.assertEqual(self.get("/api/library/export").status_code, 429)
        response = self.get("/api/library?revision=0")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"unchanged": True, "revision": 0, "user": user})
        cookie = self.client.get_cookie(COOKIE_NAME, domain="house.example.test").value
        restarted = create_app(self.config).test_client()
        restarted.set_cookie(COOKIE_NAME, cookie, domain="house.example.test")
        self.assertEqual(self.get(client=restarted).status_code, 429)
        self.assertEqual(self.get("/api/library?revision=0", restarted).status_code, 200)

    def test_simultaneous_writes_only_one_wins(self):
        self.register()
        clients = [self.app.test_client(), self.app.test_client()]
        tokens = [self.login(client=c).json["csrfToken"] for c in clients]
        gate = threading.Barrier(2)
        def write(index):
            gate.wait()
            return self.put([item(title=str(index))], client=clients[index], csrf=tokens[index]).status_code
        with ThreadPoolExecutor(2) as pool:
            statuses = list(pool.map(write, range(2)))
        self.assertEqual(sorted(statuses), [200, 409])
        self.assertEqual(self.get().json["revision"], 1)

    def test_library_and_session_persist_after_app_restart(self):
        self.register()
        self.put()
        cookie = self.client.get_cookie(COOKIE_NAME, domain="house.example.test").value
        restarted = create_app(self.config).test_client()
        restarted.set_cookie(COOKIE_NAME, cookie, domain="house.example.test")
        result = self.get(client=restarted)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json["revision"], 1)
        self.assertEqual(result.json["items"], [item()])

    def test_duplicate_ids_missing_snapshots_bad_types_and_nonfinite(self):
        self.register()
        invalid = [[item(), item()], [{"id": "missing"}], [{**item(), "id": ""}], [None],
                   [{**item(), "price": float("inf")}], [{**item(), "price": 10**500}],
                   [{**item(), "title": "\ud800"}], [{**item(), "\ud800": "bad key"}],
                   [{**item(), "__proto__": {}}]]
        for entries in invalid:
            with self.subTest(entries=str(entries)[:70]):
                self.assertEqual(self.put(entries).status_code, 400)
        self.assertEqual(self.get().json["revision"], 0)

    def test_item_count_thumbnail_and_storage_bounds(self):
        self.register()
        self.assertEqual(self.put([item(str(i)) for i in range(MAX_ITEMS + 1)]).status_code, 400)
        photo = item()
        photo["snapshot"]["propertyPhoto"] = {"data": "data:image/svg+xml,<svg/>"}
        self.assertEqual(self.put([photo]).status_code, 400)
        photo["snapshot"]["propertyPhoto"]["data"] = "data:image/jpeg;base64," + "A" * 219970
        self.assertEqual(self.put([photo]).status_code, 200)
        large = item()
        large["notes"] = "a" * 200000
        large["other"] = "b" * 200000
        self.assertEqual(self.put([large], revision=1).status_code, 413)
        many_photos = [{**photo, "id": str(i)} for i in range(60)]
        self.assertEqual(self.put(many_photos, revision=1).status_code, 413)
        self.assertEqual(self.get().json["revision"], 1)

    def test_invalid_json_duplicate_keys_content_type_and_depth(self):
        csrf = self.register().json["csrfToken"]
        headers = {"Origin": ORIGIN, "X-CSRF-Token": csrf}
        for raw in ('{"revision":0,"revision":1,"items":[]}', '{"revision":NaN,"items":[]}', "[]", "{"):
            response = self.client.put("/api/library", data=raw, content_type="application/json", headers=headers, base_url=ORIGIN)
            self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.put("/api/library", data="x", headers=headers, base_url=ORIGIN).status_code, 415)
        nested = {}
        for _ in range(20):
            nested = {"deep": nested}
        self.assertEqual(self.put([{**item(), "nested": nested}]).status_code, 400)

    def test_persistent_auth_rate_limit(self):
        self.app.config["AUTH_USER_LIMIT"] = 2
        self.assertEqual(self.login("absent").status_code, 401)
        self.assertEqual(self.login("absent").status_code, 401)
        self.assertEqual(self.login("absent").status_code, 429)
        restarted = create_app({**self.config, "AUTH_USER_LIMIT": 2}).test_client()
        self.assertEqual(self.login("absent", restarted).status_code, 429)

    def test_untrusted_client_cannot_spoof_proxy_ip(self):
        self.app.config["AUTH_IP_LIMIT"] = 1
        data = {"username": "nobody", "password": PASSWORD}
        def attempt(forwarded):
            return self.client.post("/api/library/login", json=data, base_url=ORIGIN,
                                    headers={"Origin": ORIGIN, "X-Real-IP": forwarded},
                                    environ_overrides={"REMOTE_ADDR": "203.0.113.9"})
        self.assertEqual(attempt("1.1.1.1").status_code, 401)
        self.assertEqual(attempt("2.2.2.2").status_code, 429)

    def test_no_store_on_success_auth_failure_and_invalid_request(self):
        for response in (self.get(), self.get("/api/library/session"), self.get("/api/library/missing")):
            self.assertEqual(response.headers["Cache-Control"], "no-store, private")
            self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
            self.assertEqual(response.headers["X-Frame-Options"], "DENY")
            self.assertNotIn("Access-Control-Allow-Origin", response.headers)
        self.assertEqual(self.get("/api/library/session").json["registration"], "invite")

    def test_password_change_revokes_other_sessions(self):
        csrf = self.register().json["csrfToken"]
        other = self.app.test_client()
        self.login(client=other)
        response = self.post("/api/library/password", {"currentPassword": PASSWORD, "newPassword": "a-new-private-password"}, csrf=csrf)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.get("/api/library/session").json["authenticated"])
        self.assertFalse(self.get("/api/library/session", other).json["authenticated"])
        self.assertEqual(self.login().status_code, 401)

    def test_username_password_validation_and_normalization(self):
        self.assertEqual(self.register(invite="\ud800").status_code, 400)
        for username, password in [("ab", PASSWORD), ("has space", PASSWORD), ("alice", "short"), ("alice", "x" * 257), ("alice", "\ud800" * 12)]:
            self.assertEqual(self.post("/api/library/register", {"username": username, "password": password}).status_code, 400)
        response = self.register("  Alice.Example  ")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["user"]["username"], "alice.example")

    def test_secure_configuration_and_database_mode(self):
        self.assertEqual(os.stat(self.path).st_mode & 0o777, 0o600)
        with connect_database(self.path) as db:
            self.assertEqual(db.execute("PRAGMA journal_mode").fetchone()[0], "wal")
        self.assertTrue(PASSWORD_METHOD.startswith("scrypt:"))
        hashed = generate_password_hash(PASSWORD, method=PASSWORD_METHOD)
        self.assertTrue(check_password_hash(hashed, PASSWORD))
        for origin in ("", "http://house.test", "https://house.test/", "https://user:pass@house.test"):
            with self.assertRaises(RuntimeError):
                create_app({"DATABASE": self.path, "ORIGIN": origin})

    def test_low_disk_prevents_registration_and_library_write_without_data_loss(self):
        self.register()
        self.put()
        self.app.config["MIN_FREE_BYTES"] = 2 * 1024**3
        with patch("library_server.shutil.disk_usage") as disk:
            disk.return_value.free = 1024
            self.assertEqual(self.register("bobby", self.app.test_client()).json["error"], "storage_capacity")
            self.assertEqual(self.put([], revision=1).status_code, 503)
        self.assertEqual(self.get().json["revision"], 1)
        self.assertEqual(self.get().json["items"], [item()])


if __name__ == "__main__":
    unittest.main()
