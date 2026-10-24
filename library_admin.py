"""Offline library administration. Run as the service user with its environment.

No password argument is accepted: recovery reads it from a protected terminal.
Invites are one-use credentials. The create-invite command prints only the new
invitation code; do not include it in logs, public URLs, or source control.
"""

import argparse
import getpass
import os
import time

from library_server import (PASSWORD_METHOD, connect_database, create_invite,
                            initialize_database, normalize_username, validate_password)
from werkzeug.security import generate_password_hash


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", default=os.environ.get("HOUSE_ALPHA_DATABASE", "/var/lib/house-alpha/library.sqlite3"))
    commands = parser.add_subparsers(dest="command", required=True)
    invite = commands.add_parser("create-invite")
    invite.add_argument("--hours", type=int, choices=range(1, 721), default=72, metavar="1..720")
    reset = commands.add_parser("reset-password")
    reset.add_argument("username")
    commands.add_parser("status")
    commands.add_parser("cleanup")
    args = parser.parse_args()
    if args.command == "create-invite":
        print(create_invite(args.database, args.hours))
        return
    initialize_database(args.database)
    with connect_database(args.database) as db:
        if args.command == "reset-password":
            username = normalize_username(args.username)
            user = db.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
            if not user:
                parser.error("No such account")
            password = validate_password(getpass.getpass("New password (at least 12 characters): "))
            if password != getpass.getpass("Repeat new password: "):
                parser.error("Passwords did not match")
            hashed = generate_password_hash(password, method=PASSWORD_METHOD)
            db.execute("BEGIN IMMEDIATE")
            db.execute("UPDATE users SET password_hash=? WHERE id=?", (hashed, user["id"]))
            db.execute("DELETE FROM sessions WHERE user_id=?", (user["id"],))
            db.commit()
            print("Password changed; all existing sessions revoked.")
        elif args.command == "cleanup":
            now = int(time.time())
            db.execute("DELETE FROM sessions WHERE expires_at<=?", (now,))
            db.execute("DELETE FROM invites WHERE expires_at<=?", (now,))
            db.execute("DELETE FROM rate_limits WHERE window_start<?", (now - 86400,))
            db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            print("Expired sessions, invites, and rate buckets removed.")
        else:
            count = db.execute("SELECT count(*) FROM users").fetchone()[0]
            size = db.execute("SELECT coalesce(sum(length(CAST(items_json AS BLOB))),0) FROM libraries").fetchone()[0]
            print(f"Accounts: {count}; saved library bytes: {size}")


if __name__ == "__main__":
    main()
