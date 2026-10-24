#!/usr/bin/env python3
"""Pause public service at conservative resource thresholds; never resize or pay.

All primary-interface transmit bytes count, including unrelated VM traffic.
Counters are durable across restarts; one initial baseline excludes prior setup.
The marker is sticky until an administrator reviews usage and removes it.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import time

GIB = 1024 ** 3

def usage_after(previous, month, boot, total):
    if not previous:
        return {'month': month, 'boot': boot, 'last_tx': total, 'bytes': 0}
    delta = max(0, total - previous['last_tx']) if previous['boot'] == boot else total
    used = previous['bytes'] if previous['month'] == month else 0
    return {'month': month, 'boot': boot, 'last_tx': total, 'bytes': used + delta}

def main():
    os.umask(0o022)
    directory = Path('/var/lib/house-alpha-guard')
    directory.mkdir(mode=0o755, exist_ok=True)
    route = [line.split()[0] for line in Path('/proc/net/route').read_text().splitlines()[1:]
             if line.split()[1] == '00000000'][0]
    total = int(Path(f'/sys/class/net/{route}/statistics/tx_bytes').read_text())
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    now = datetime.now(timezone.utc)
    path = directory / 'usage.json'
    previous = json.loads(path.read_text()) if path.exists() else None
    state = usage_after(previous, now.strftime('%Y-%m'), boot, total)
    state['checked_at'] = now.isoformat()
    state['free_bytes'] = shutil.disk_usage('/var/lib/house-alpha').free
    state['memory_available_bytes'] = next(int(line.split()[1]) * 1024 for line in
        Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:'))
    state['low_memory_checks'] = (previous or {}).get('low_memory_checks', 0) + 1 if state['memory_available_bytes'] < 512 * 1024 ** 2 else 0
    reason = ('monthly traffic threshold (50 GiB)' if state['bytes'] >= 50 * GIB else
              'free disk below 2 GiB' if state['free_bytes'] < 2 * GIB else
              'low available memory for 15 minutes' if state['low_memory_checks'] >= 3 else '')
    if reason:
        (directory / 'paused').write_text(reason + '\n')
        print('Public app paused: ' + reason)
    state['paused'] = (directory / 'paused').exists()
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(state, indent=2) + '\n')
    os.replace(temporary, path)

if __name__ == '__main__':
    try:
        main()
    except Exception:
        # A broken meter must not silently remove the cost-control safeguard.
        directory = Path('/var/lib/house-alpha-guard')
        directory.mkdir(mode=0o755, exist_ok=True)
        (directory / 'paused').write_text('Resource checks need administrator review.\n')
        raise

