"""Private, bounded House Alpha library API. Run behind a local HTTPS proxy.

gunicorn --bind 127.0.0.1:8766 --workers 2 --threads 2 'library_server:create_app()'
Required: HOUSE_ALPHA_ORIGIN=https://your-host
Optional: HOUSE_ALPHA_DATABASE, HOUSE_ALPHA_REGISTRATION (invite/open/closed).
The proxy must overwrite X-Real-IP; forwarded headers are ignored from nonlocal peers.
"""

import hashlib
from contextlib import closing
import ipaddress
import json
import math
import os
from pathlib import Path
import re
import secrets
import shutil
import sqlite3
import threading
import time
from urllib.parse import urlsplit

from flask import Flask, g, jsonify, request
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash


MAX_ITEMS = 100
MAX_LIBRARY_BYTES = 12 * 1024 * 1024
MAX_ITEM_BYTES = 350 * 1024
MAX_PHOTO_CHARS = 220000
SESSION_SECONDS = 7 * 24 * 60 * 60
PASSWORD_METHOD = "scrypt:32768:8:1"
COOKIE_NAME = "__Host-house_alpha_session"
USERNAME = re.compile(r"^[a-z0-9][a-z0-9_.-]{2,39}$")
TOKEN = re.compile(r"^[A-Za-z0-9_-]{40,100}$")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
 id TEXT PRIMARY KEY, username TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
 created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS libraries (
 user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
 revision INTEGER NOT NULL DEFAULT 0, items_json TEXT NOT NULL DEFAULT '[]',
 updated_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
 token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 csrf_token TEXT NOT NULL, created_at INTEGER NOT NULL, expires_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS session_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS session_expiry ON sessions(expires_at);
CREATE TABLE IF NOT EXISTS invites (
 token_hash TEXT PRIMARY KEY, created_at INTEGER NOT NULL, expires_at INTEGER NOT NULL,
 used_at INTEGER, used_by TEXT REFERENCES users(id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS rate_limits (
 bucket TEXT PRIMARY KEY, window_start INTEGER NOT NULL, count INTEGER NOT NULL
);
PRAGMA user_version=1;
"""


class APIError(Exception):
    def __init__(self, status, error, message):
        self.status, self.error, self.message = status, error, message


def token_hash(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def connect_database(path):
    db = sqlite3.connect(path, timeout=10, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA busy_timeout=10000")
    return db


def initialize_database(path):
    directory = Path(path).resolve().parent
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    # The directory should be service-owned and private; never loosen an existing mode.
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(descriptor)
    except FileExistsError:
        pass
    with closing(connect_database(path)) as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.executescript(SCHEMA)


def create_invite(path, hours=72):
    """Offline administrative primitive; only its caller may disclose the new token."""
    initialize_database(path)
    value, now = secrets.token_urlsafe(32), int(time.time())
    with closing(connect_database(path)) as db:
        db.execute("DELETE FROM invites WHERE expires_at < ?", (now,))
        db.execute("INSERT INTO invites VALUES (?, ?, ?, NULL, NULL)",
                   (token_hash(value), now, now + int(hours * 3600)))
    return value


def normalize_username(value):
    if not isinstance(value, str):
        raise APIError(400, "invalid_username", "Choose a username with 3–40 letters, numbers, dots, underscores, or hyphens.")
    normalized = value.strip().lower()
    if not USERNAME.fullmatch(normalized):
        raise APIError(400, "invalid_username", "Choose a username with 3–40 letters, numbers, dots, underscores, or hyphens.")
    return normalized


def validate_password(value):
    if not isinstance(value, str) or len(value) < 12 or len(value) > 256:
        raise APIError(400, "invalid_password", "Use a password between 12 and 256 characters.")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeEncodeError:
        raise APIError(400, "invalid_password", "Use a password with valid text characters.") from None
    if size > 1024:
        raise APIError(400, "invalid_password", "That password is too long.")
    return value


def encode_json(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def validate_json_tree(value, depth=0, budget=None):
    if budget is None:
        budget = [0]
    budget[0] += 1
    if budget[0] > 30000 or depth > 16:
        raise APIError(400, "invalid_library", "A saved property contains too much nested data.")
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        if abs(value) > 1e100 or not math.isfinite(value):
            raise APIError(400, "invalid_library", "Saved properties must contain finite numbers.")
        return
    if isinstance(value, str):
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            raise APIError(400, "invalid_library", "Saved properties must contain valid text characters.") from None
        if len(value) > MAX_PHOTO_CHARS:
            raise APIError(400, "invalid_library", "A saved property contains text or a thumbnail that is too large.")
        return
    if isinstance(value, list):
        if len(value) > 2000:
            raise APIError(400, "invalid_library", "A saved property contains too many fields.")
        for item in value:
            validate_json_tree(item, depth + 1, budget)
        return
    if isinstance(value, dict):
        if len(value) > 2000:
            raise APIError(400, "invalid_library", "A saved property contains too many fields.")
        for key, item in value.items():
            if not isinstance(key, str) or len(key) > 200 or key in ("__proto__", "prototype", "constructor"):
                raise APIError(400, "invalid_library", "A saved property has an invalid field name.")
            try:
                key.encode("utf-8")
            except UnicodeEncodeError:
                raise APIError(400, "invalid_library", "A saved property has an invalid field name.") from None
            validate_json_tree(item, depth + 1, budget)
        return
    raise APIError(400, "invalid_library", "Saved properties must contain valid JSON data.")


def validate_items(items):
    if not isinstance(items, list) or len(items) > MAX_ITEMS:
        raise APIError(400, "invalid_library", "A library can contain up to 100 saved properties.")
    seen = set()
    for item in items:
        if not isinstance(item, dict):
            raise APIError(400, "invalid_library", "Each saved property must be an object.")
        identifier, snapshot = item.get("id"), item.get("snapshot")
        if not isinstance(identifier, str) or not 1 <= len(identifier) <= 80 or any(ord(c) < 32 for c in identifier):
            raise APIError(400, "invalid_library", "Each saved property needs a valid ID.")
        if identifier in seen:
            raise APIError(400, "duplicate_id", "Saved property IDs must be unique.")
        seen.add(identifier)
        if not isinstance(snapshot, dict) or not isinstance(snapshot.get("controls"), dict):
            raise APIError(400, "invalid_library", "Each saved property needs its saved input snapshot.")
        validate_json_tree(item)
        photo = snapshot.get("propertyPhoto")
        if photo is not None:
            data = photo.get("data") if isinstance(photo, dict) else None
            if not isinstance(data, str) or not re.fullmatch(r"data:image/jpeg;base64,[A-Za-z0-9+/=]+", data) or len(data) > MAX_PHOTO_CHARS:
                raise APIError(400, "invalid_library", "Thumbnails must be resized JPEG images.")
        if len(encode_json(item).encode("utf-8")) > MAX_ITEM_BYTES:
            raise APIError(413, "item_too_large", "One saved property exceeds the 350 KB limit.")
    encoded = encode_json(items)
    if len(encoded.encode("utf-8")) > MAX_LIBRARY_BYTES:
        raise APIError(413, "library_too_large", "The library exceeds its 12 MB storage limit. Export and remove some photos or properties.")
    return encoded


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        DATABASE=os.environ.get("HOUSE_ALPHA_DATABASE", "/var/lib/house-alpha/library.sqlite3"),
        ORIGIN=os.environ.get("HOUSE_ALPHA_ORIGIN", ""),
        REGISTRATION=os.environ.get("HOUSE_ALPHA_REGISTRATION", "invite"),
        MAX_ACCOUNTS=100,
        MIN_FREE_BYTES=2 * 1024 * 1024 * 1024,
        MAX_CONTENT_LENGTH=MAX_LIBRARY_BYTES + 65536,
        AUTH_IP_LIMIT=30,
        AUTH_USER_LIMIT=10,
        AUTH_WINDOW=900,
        PASSWORD_METHOD=PASSWORD_METHOD,
    )
    if config:
        app.config.update(config)
    origin = app.config["ORIGIN"]
    parsed = urlsplit(origin)
    if (parsed.scheme != "https" and not app.testing) or not parsed.netloc or parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.password:
        raise RuntimeError("HOUSE_ALPHA_ORIGIN must be the exact HTTPS origin, without a path or trailing slash")
    if app.config["REGISTRATION"] not in ("invite", "open", "closed"):
        raise RuntimeError("HOUSE_ALPHA_REGISTRATION must be invite, open, or closed")
    initialize_database(app.config["DATABASE"])
    hashing_slots = threading.BoundedSemaphore(2)
    # Unknown-account login follows the same costly path without revealing existence.
    dummy_hash = generate_password_hash(secrets.token_urlsafe(32), method=app.config["PASSWORD_METHOD"])

    def database():
        if "database" not in g:
            g.database = connect_database(app.config["DATABASE"])
        return g.database

    @app.teardown_appcontext
    def close_database(_error):
        db = g.pop("database", None)
        if db:
            db.close()

    def client_ip():
        peer = request.remote_addr or "unknown"
        if peer in ("127.0.0.1", "::1"):
            forwarded = request.headers.get("X-Real-IP", "")
            try:
                return str(ipaddress.ip_address(forwarded))
            except ValueError:
                pass
        return peer

    def consume_limits(buckets, window):
        now, db = int(time.time()), database()
        db.execute("BEGIN IMMEDIATE")
        try:
            db.execute("DELETE FROM rate_limits WHERE window_start < ?", (now - 86400,))
            for raw, maximum in buckets:
                bucket = token_hash(raw)
                row = db.execute("SELECT window_start,count FROM rate_limits WHERE bucket=?", (bucket,)).fetchone()
                if row and row["window_start"] > now - window and row["count"] >= maximum:
                    raise APIError(429, "rate_limited", "Too many attempts. Please wait before trying again.")
            for raw, _maximum in buckets:
                bucket = token_hash(raw)
                db.execute("INSERT INTO rate_limits VALUES (?, ?, 1) ON CONFLICT(bucket) DO UPDATE SET count=CASE WHEN window_start<=? THEN 1 ELSE count+1 END, window_start=CASE WHEN window_start<=? THEN ? ELSE window_start END", (bucket, now, now - window, now - window, now))
            db.commit()
        except Exception:
            db.rollback()
            raise

    def auth_limits(username):
        consume_limits([("auth-ip:" + client_ip(), app.config["AUTH_IP_LIMIT"]),
                        ("auth-user:" + username, app.config["AUTH_USER_LIMIT"])], app.config["AUTH_WINDOW"])

    def require_storage_capacity():
        available = shutil.disk_usage(Path(app.config["DATABASE"]).resolve().parent).free
        if available < app.config["MIN_FREE_BYTES"]:
            raise APIError(503, "storage_capacity", "Cloud storage is temporarily full. Keep your local copy and try again later.")

    def costly_hash(password, existing=None):
        if not hashing_slots.acquire(blocking=False):
            raise APIError(503, "busy", "Sign-in is busy. Please try again in a moment.")
        try:
            return check_password_hash(existing, password) if existing else generate_password_hash(password, method=app.config["PASSWORD_METHOD"])
        finally:
            hashing_slots.release()

    def body(maximum=16384):
        if request.mimetype != "application/json":
            raise APIError(415, "json_required", "Send JSON data.")
        if request.content_length is not None and request.content_length > maximum:
            raise APIError(413, "request_too_large", "This request is too large.")
        raw = request.get_data(cache=False)
        if len(raw) > maximum:
            raise APIError(413, "request_too_large", "This request is too large.")
        def reject_duplicate_keys(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError("Duplicate JSON key")
                result[key] = value
            return result
        try:
            value = json.loads(raw, object_pairs_hook=reject_duplicate_keys,
                               parse_constant=lambda _value: (_ for _ in ()).throw(ValueError("Nonfinite number")))
        except (ValueError, UnicodeDecodeError, RecursionError):
            raise APIError(400, "invalid_json", "Send valid JSON data.") from None
        if not isinstance(value, dict):
            raise APIError(400, "invalid_json", "Send a JSON object.")
        return value

    def current_session(required=True):
        if "library_session" not in g:
            value = request.cookies.get(COOKIE_NAME, "")
            g.library_session = None
            if TOKEN.fullmatch(value):
                g.library_session = database().execute("SELECT s.*, u.username FROM sessions s JOIN users u ON u.id=s.user_id WHERE token_hash=? AND expires_at>?", (token_hash(value), int(time.time()))).fetchone()
        if required and not g.library_session:
            raise APIError(401, "authentication_required", "Sign in to use your synced library.")
        return g.library_session

    def session_payload(session):
        result = {"authenticated": bool(session), "registration": app.config["REGISTRATION"],
                  "limits": {"items": MAX_ITEMS, "bytes": MAX_LIBRARY_BYTES}}
        if session:
            result.update(user={"id": session["user_id"], "username": session["username"]}, csrfToken=session["csrf_token"])
        return result

    def create_session(user_id, username):
        db, now = database(), int(time.time())
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        db.execute("DELETE FROM sessions WHERE expires_at<=?", (now,))
        # At most ten active devices per account; newest sessions survive.
        db.execute("DELETE FROM sessions WHERE user_id=? AND token_hash NOT IN (SELECT token_hash FROM sessions WHERE user_id=? ORDER BY created_at DESC,rowid DESC LIMIT 9)", (user_id, user_id))
        old = request.cookies.get(COOKIE_NAME, "")
        if TOKEN.fullmatch(old):
            db.execute("DELETE FROM sessions WHERE token_hash=?", (token_hash(old),))
        db.execute("INSERT INTO sessions VALUES (?, ?, ?, ?, ?)", (token_hash(token), user_id, csrf, now, now + SESSION_SECONDS))
        response = jsonify(session_payload({"user_id": user_id, "username": username, "csrf_token": csrf}))
        response.set_cookie(COOKIE_NAME, token, max_age=SESSION_SECONDS, secure=True, httponly=True, samesite="Lax", path="/")
        return response

    @app.before_request
    def protect_request():
        if request.headers.get("Sec-Fetch-Site") == "cross-site":
            raise APIError(403, "cross_site_request", "Open House Alpha directly to use your library.")
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            if request.headers.get("Origin") != app.config["ORIGIN"]:
                raise APIError(403, "origin_required", "Reload House Alpha before trying again.")
            if request.path not in ("/api/library/login", "/api/library/register"):
                session = current_session()
                provided = request.headers.get("X-CSRF-Token", "")
                if not TOKEN.fullmatch(provided) or not secrets.compare_digest(provided, session["csrf_token"]):
                    raise APIError(403, "csrf_required", "Reload House Alpha before trying again.")

    @app.after_request
    def private_response(response):
        response.headers["Cache-Control"] = "no-store, private"
        response.headers["Pragma"] = "no-cache"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        response.headers["Vary"] = "Cookie, Origin"
        if response.status_code in (429, 503):
            response.headers["Retry-After"] = "60"
        return response

    @app.errorhandler(APIError)
    def handle_api_error(error):
        return jsonify(error=error.error, message=error.message), error.status

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return jsonify(error="request_error", message=error.description), error.code

    @app.errorhandler(sqlite3.OperationalError)
    def handle_database_error(_error):
        # Avoid exposing queries, usernames, filesystem paths, or database contents.
        app.logger.error("Library database temporarily unavailable")
        return jsonify(error="storage_unavailable", message="Library storage is temporarily unavailable. Your local changes are still on this device."), 503

    @app.get("/api/library/session")
    def session_info():
        return jsonify(session_payload(current_session(False)))

    @app.post("/api/library/register")
    def register():
        data = body()
        username = normalize_username(data.get("username"))
        auth_limits(username)
        require_storage_capacity()
        password = validate_password(data.get("password"))
        registration = app.config["REGISTRATION"]
        if registration == "closed":
            raise APIError(403, "registration_closed", "New accounts are currently closed.")
        invite = data.get("invite", "")
        if not isinstance(invite, str) or len(invite) > 100 or (invite and not TOKEN.fullmatch(invite)):
            raise APIError(400, "invalid_invite", "Enter a valid invitation code.")
        invite_digest, now = token_hash(invite), int(time.time())
        db = database()
        if registration == "invite" and not db.execute("SELECT 1 FROM invites WHERE token_hash=? AND used_at IS NULL AND expires_at>?", (invite_digest, now)).fetchone():
            raise APIError(403, "invalid_invite", "That invitation code is invalid, expired, or already used.")
        password_hash = costly_hash(password)
        identifier = secrets.token_hex(16)
        db.execute("BEGIN IMMEDIATE")
        try:
            if db.execute("SELECT count(*) FROM users").fetchone()[0] >= app.config["MAX_ACCOUNTS"]:
                raise APIError(403, "account_limit", "New accounts are temporarily full.")
            if registration == "invite":
                changed = db.execute("UPDATE invites SET used_at=?,used_by=NULL WHERE token_hash=? AND used_at IS NULL AND expires_at>?", (now, invite_digest, now)).rowcount
                if changed != 1:
                    raise APIError(403, "invalid_invite", "That invitation code is invalid, expired, or already used.")
            db.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (identifier, username, password_hash, now))
            db.execute("INSERT INTO libraries(user_id,updated_at) VALUES (?, ?)", (identifier, now))
            if registration == "invite":
                db.execute("UPDATE invites SET used_by=? WHERE token_hash=?", (identifier, invite_digest))
            response = create_session(identifier, username)
            db.commit()
        except sqlite3.IntegrityError:
            db.rollback()
            raise APIError(409, "username_unavailable", "That username is unavailable. Choose another.") from None
        except Exception:
            db.rollback()
            raise
        return response, 201

    @app.post("/api/library/login")
    def login():
        data = body()
        username = normalize_username(data.get("username"))
        auth_limits(username)
        password = validate_password(data.get("password"))
        user = database().execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        correct = costly_hash(password, user["password_hash"] if user else dummy_hash)
        if not user or not correct:
            raise APIError(401, "invalid_credentials", "The username or password is incorrect.")
        db = database()
        db.execute("BEGIN IMMEDIATE")
        try:
            response = create_session(user["id"], user["username"])
            db.commit()
        except Exception:
            db.rollback()
            raise
        return response

    @app.post("/api/library/logout")
    def logout():
        session = current_session()
        database().execute("DELETE FROM sessions WHERE token_hash=?", (session["token_hash"],))
        response = jsonify(ok=True)
        response.delete_cookie(COOKIE_NAME, secure=True, httponly=True, samesite="Lax", path="/")
        return response

    def owned_library():
        session = current_session()
        # Full responses can contain photos. Bound their transfer separately
        # from cheap unchanged-revision checks, including export requests.
        consume_limits([("full-read:" + session["user_id"], 10)], 60)
        row = database().execute("SELECT revision,items_json FROM libraries WHERE user_id=?", (session["user_id"],)).fetchone()
        return {"revision": row["revision"], "items": json.loads(row["items_json"]),
                "user": {"id": session["user_id"], "username": session["username"]}}

    @app.get("/api/library")
    def get_library():
        # Avoid retransmitting thumbnails on each visible-tab refresh. This is an
        # authenticated JSON response, never an HTTP/shared-cache validator.
        requested = request.args.get("revision", "")
        if requested.isascii() and requested.isdecimal() and len(requested) <= 16:
            session = current_session()
            current = database().execute("SELECT revision FROM libraries WHERE user_id=?", (session["user_id"],)).fetchone()[0]
            if int(requested) == current:
                return jsonify(unchanged=True, revision=current,
                               user={"id": session["user_id"], "username": session["username"]})
        return jsonify(owned_library())

    @app.get("/api/library/export")
    def export_library():
        response = jsonify(owned_library())
        response.headers["Content-Disposition"] = 'attachment; filename="house-alpha-library.json"'
        return response

    @app.put("/api/library")
    def put_library():
        session = current_session()
        require_storage_capacity()
        consume_limits([("write:" + session["user_id"], 60)], 60)
        data = body(MAX_LIBRARY_BYTES + 65536)
        if set(data) != {"revision", "items"} or type(data.get("revision")) is not int or not 0 <= data["revision"] < 2**53:
            raise APIError(400, "invalid_revision", "Include the library revision and saved items.")
        encoded = validate_items(data["items"])
        db = database()
        updated = db.execute("UPDATE libraries SET items_json=?,revision=revision+1,updated_at=? WHERE user_id=? AND revision=?", (encoded, int(time.time()), session["user_id"], data["revision"])).rowcount
        if not updated:
            current = db.execute("SELECT revision FROM libraries WHERE user_id=?", (session["user_id"],)).fetchone()[0]
            return jsonify(error="revision_conflict", message="Your library changed on another device. Refresh it before saving; your changes have not been overwritten.", revision=current), 409
        return jsonify(revision=data["revision"] + 1, items=data["items"],
                       user={"id": session["user_id"], "username": session["username"]})

    @app.post("/api/library/password")
    def change_password():
        session, data = current_session(), body()
        auth_limits(session["username"])
        current = validate_password(data.get("currentPassword"))
        new = validate_password(data.get("newPassword"))
        db = database()
        old_hash = db.execute("SELECT password_hash FROM users WHERE id=?", (session["user_id"],)).fetchone()[0]
        if not costly_hash(current, old_hash):
            raise APIError(401, "invalid_credentials", "The current password is incorrect.")
        new_hash = costly_hash(new)
        db.execute("BEGIN IMMEDIATE")
        try:
            db.execute("UPDATE users SET password_hash=? WHERE id=?", (new_hash, session["user_id"]))
            db.execute("DELETE FROM sessions WHERE user_id=?", (session["user_id"],))
            response = create_session(session["user_id"], session["username"])
            db.commit()
        except Exception:
            db.rollback()
            raise
        return response

    return app
