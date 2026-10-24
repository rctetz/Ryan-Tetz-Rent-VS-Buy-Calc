#!/usr/bin/env python3
"""Consistent SQLite snapshots, seven-day retention, private filesystem only."""
from datetime import datetime, timezone
from contextlib import closing
import os
from pathlib import Path
import sqlite3

os.umask(0o077)
root = Path('/var/lib/house-alpha')
directory = root / 'backups'
directory.mkdir(mode=0o700, exist_ok=True)
name = datetime.now(timezone.utc).strftime('library-%Y%m%d.sqlite3')
target = directory / name
temporary = directory / (name + '.tmp')
with closing(sqlite3.connect(f'file:{root / "library.sqlite3"}?mode=ro', uri=True)) as source:
    with closing(sqlite3.connect(temporary)) as destination:
        source.backup(destination)
        destination.execute('PRAGMA journal_mode=DELETE')
        assert destination.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
os.replace(temporary, target)
for old in sorted(directory.glob('library-*.sqlite3'), reverse=True)[7:]:
    old.unlink()
print('Verified daily library snapshot; at most seven snapshots retained.')

