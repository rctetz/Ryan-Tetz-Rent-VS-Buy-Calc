# House Alpha deployment and recovery

This runbook describes the Oracle deployment and this source tree. It includes
the operator-confirmed **2026-10-24 21:40 UTC public HTTPS deployment** and the
subsequent successful certificate renewal rehearsal. Commands below are
operator instructions; writing this document did not deploy or change the VM.

## Current status

- VM: `161.153.24.254`, Ubuntu 24.04 ARM, Oracle Phoenix, A1 Flex with 2 OCPU,
  12 GB RAM and one 50 GB boot volume. The public address is ephemeral.
- Current release: `/opt/house-alpha/releases/sync-20261024`, selected by
  `/opt/house-alpha/current`.
- **Live URL: [https://house.ryantetz.com](https://house.ryantetz.com).**
  `HOUSE_ALPHA_ORIGIN=https://house.ryantetz.com`; HTTP redirects to the domain
  over HTTPS with status 308. Public HTTPS nginx configuration was deployed at
  21:40 UTC.
- Squarespace has an A record `house → 161.153.24.254`, TTL 1800 seconds.
  All eight authoritative nameservers were checked. The blank embedded
  verification screen was resolved with standalone Squarespace login and
  reauthentication before saving the record.
- `house-alpha`, `house-alpha-library`, `nginx`, `house-alpha-backup.timer`,
  `house-alpha-guard.timer`, and `house-alpha-certbot.timer` are active.
- Modern **Certbot 5.8.0** is installed at `/opt/certbot/bin/certbot`.
  nginx serves certificate `house-alpha-domain`, expiring **2027-01-22**.
  The custom timer checks every six hours, with up to 30 minutes of random
  delay, and renews **only** that certificate. The distribution `certbot.timer`
  is disabled. A domain renewal dry run with `--run-deploy-hooks` succeeded,
  including nginx configuration validation and reload.
- An earlier IP certificate is unused: it is neither served nor renewed by
  the custom timer. Use the domain URL, not the numeric IP, for the app.
- A server snapshot and an off-server Mac copy named
  `library-20261024.sqlite3` exist. The Mac copy passed SQLite integrity check.
  The guard reported `paused: false`.
- The original [Render app](https://mammoth-rent-vs-buy.onrender.com/?release=42)
  remains the migration source. Its browser saves do not automatically appear
  on a new hostname.
- **32 automated tests and 35 public HTTPS integration checks passed.**
  Browser sign-in, save, cloud restore after reload, Open, and clearing private
  data on sign-out also passed. Actual user migration has not been performed.

Earlier Oracle provisioning notes describe the VM before this app was installed.

## Layout and access

| Component | Location / behavior |
| --- | --- |
| Public calculator | `app.py`, systemd `house-alpha`, loopback `127.0.0.1:8765` |
| Private library API | `library_server.py`, systemd `house-alpha-library`, Gunicorn on `127.0.0.1:8766`, two workers and two threads each |
| HTTPS / routing | nginx; `/etc/nginx/sites-available/house-alpha`, `/etc/nginx/snippets/house-alpha-routes.conf`, `/etc/nginx/conf.d/house-alpha-limits.conf` |
| Staging listener | Prepared on loopback `127.0.0.1:8888`; this is not a public endpoint |
| Service account | `house-alpha`, no interactive shell; release files owned by root |
| Runtime configuration | `/etc/house-alpha.env`, root-owned and readable by the service group |
| Private SQLite database | `/var/lib/house-alpha/library.sqlite3`; outside the public asset directory |
| Server snapshots | `/var/lib/house-alpha/backups/` |
| Resource meter / pause marker | `/var/lib/house-alpha-guard/usage.json` and `/var/lib/house-alpha-guard/paused` |
| Modern certificate client | `/opt/certbot/bin/certbot`; verified renewal hook at `/usr/sbin/nginx-reload-house-alpha` |

The configured origin must exactly match the live HTTPS origin, without a path
or trailing slash. Changing the public hostname also requires updating
`HOUSE_ALPHA_ORIGIN` and restarting both application services. nginx must
overwrite `X-Real-IP` with its socket peer; the applications trust this header
only from loopback. Do not expose the application ports directly.

From the Mac, connect using the saved server identity and local key:

```sh
/Users/ryantetz/Documents/Codex/2026-10-24/do-x20/outputs/oracle-ssh/connect.sh
```

Keep that helper, `known_hosts`, and its private key together. Never copy the
private key into the release or database backup. SSH is currently permitted
only from `47.209.23.245/32` in both OCI and the host firewall; a changed home IP
requires updating both. HTTP/HTTPS are allowed publicly. Preserve Oracle's
internal-service and iSCSI firewall rules.

Useful read-only checks on the VM:

```sh
systemctl is-active house-alpha house-alpha-library nginx
systemctl list-timers 'house-alpha-*' --all --no-pager
sudo journalctl -u house-alpha-library -u house-alpha-guard -u house-alpha-backup -n 50 --no-pager
sudo cat /var/lib/house-alpha-guard/usage.json
sudo -u house-alpha /opt/house-alpha/venv/bin/python /opt/house-alpha/current/library_admin.py status
curl --fail --silent http://127.0.0.1:8766/api/library/session
```

`/healthz` is an nginx-only response. It remains HTTP 200 during a resource
pause and does not prove that the database, login, or library API is healthy.

## Limits and cost controls

The deployment adds no paid API, managed database, load balancer, paid backup
service, or subscription. No RentCast key is planned; the environment sets
`RENTCAST_PROCESS_CALL_LIMIT=0` as an additional stop. Public Census matching
and public market-source requests remain available. No OpenAI API is required.

The Oracle account was provisioned as Free Tier without a paid upgrade. The
existing 2 OCPU / 12 GB shape and 50 GB disk were selected within the verified
Always Free allocation. Application limits are conservative protection, not an
Oracle billing meter or a guarantee against all network traffic. Do not upgrade,
resize, add billable services, or enable paid provider keys automatically.

| Limit | Enforcement |
| --- | --- |
| Accounts | 100 total; registration configured `open`, with `invite` and `closed` modes also supported |
| Saved library | 100 properties and 12 MiB serialized JSON per account |
| One property | 350 KiB JSON; JPEG thumbnail data URL at most 220,000 characters |
| Payload | nginx 13 MiB; API library request limit 12 MiB + 64 KiB; smaller auth bodies |
| Sign-in / registration / password attempts | 30 per IP and 10 per username per 15 minutes, persisted in SQLite; nginx additionally limits auth requests to 10/minute per IP with a burst allowance |
| Full library reads and export | 10 per account per minute; unchanged revision checks return a small authenticated response without retransmitting photos |
| Library writes | 60 per account per minute; stale revisions return 409 without overwriting newer data |
| Proxy traffic | General 5 requests/second per IP with burst allowances; 16 concurrent connections per IP |
| Sessions | Seven-day lifetime, at most ten active sessions per account; password changes revoke existing sessions |
| Process resources | Public service 512 MiB / 100 tasks; library service 768 MiB / 40 tasks; public server also bounds request threads and market-source requests |
| Disk reserve | New accounts and library writes stop below 2 GiB free space |

Passwords use scrypt hashes. Session cookies are Secure, HttpOnly, and SameSite;
mutations require the exact origin plus a CSRF token once signed in. Private
APIs are not cached by the service worker. Signed-in libraries and unfinished
workspace edits stay in tab memory on the device; closing a tab can lose
unsynced edits. Export before closing when sync is failing. Exports include
private addresses, inputs, and thumbnails.

## Resource pause and recovery

`house-alpha-guard.timer` runs after boot and about every five minutes. It writes
a sticky pause marker when any of these conditions occurs:

- Transmitted traffic reaches **50 GiB in a UTC calendar month**.
- Free disk falls below **2 GiB**.
- Available memory stays below **512 MiB for three consecutive checks**.
- The resource meter itself fails.

The traffic counter uses the primary interface, counts other VM traffic as well
as House Alpha, and preserves its total across process restarts and VM reboots.
Its initial baseline excludes prior setup traffic. The five-minute interval
allows some overshoot. A pause blocks public app/API routes with HTTP 503;
it preserves the database and does not resize the VM or buy anything. It does
not stop the whole VM or unrelated traffic.

Investigate before resuming:

```sh
sudo cat /var/lib/house-alpha-guard/paused
sudo cat /var/lib/house-alpha-guard/usage.json
df -h /var/lib/house-alpha
free -h
sudo journalctl -u house-alpha-guard -u house-alpha-library -n 80 --no-pager
```

Fix the actual condition first. For traffic exhaustion, ordinarily wait for
the next monthly reset and review the cause; do not erase `usage.json` to hide
usage. Remove unnecessary temporary files only after identifying them, and keep
the database and required backups. A new month resets the meter but **does not
remove an existing pause marker**.

After an operator confirms the problem is resolved, these commands resume
service and immediately recheck the guard:

```sh
sudo rm -- /var/lib/house-alpha-guard/paused
sudo systemctl start house-alpha-guard.service
sudo cat /var/lib/house-alpha-guard/usage.json
```

If the marker returns, keep the app paused and investigate. No application
restart is required just to clear a valid resource pause. Never remove the
marker merely because `/healthz` succeeds.

## Backups: automated on the VM, manual off the VM

The active `house-alpha-backup.timer` runs at **09:00 UTC daily** and catches up
after downtime. `deploy/backup.py` uses SQLite's backup API, includes committed
WAL data, checks integrity, and atomically replaces the day's snapshot. It keeps
the newest seven dated snapshots. Repeated backups on the same date replace
that date's file; these are not seven separate restore points per day.

The service account owns a private directory and snapshots use owner-only
permissions. The backup includes all accounts, password hashes, sessions,
invitations, and property data. It is sensitive even though it contains no
plaintext account passwords. Do not put it in Git, a public web folder, or a
shared document.

Trigger a server snapshot manually:

```sh
sudo systemctl start house-alpha-backup.service
sudo journalctl -u house-alpha-backup -n 10 --no-pager
```

The Mac helper creates a fresh consistent server snapshot, downloads it through
SSH, checks SQLite integrity locally, and retains seven local dates:

```sh
/Users/ryantetz/Documents/Codex/2026-10-24/do-x20/outputs/house-alpha-backup.sh
```

Its destination is
`/Users/ryantetz/Documents/Codex/2026-10-24/do-x20/outputs/house-alpha-private-backups/`.
The helper and directory are mode 700, and downloaded databases are mode 600.
**Off-server backup is manual; no recurring Mac download is scheduled.** Run
the helper after important library changes and before server maintenance. A VM
snapshot on the same disk is not protection against loss/reclamation of that
VM. No separate cloud backup or off-device Mac backup has been configured here.

## Browser-library migration and account recovery

Use the live site's “Bring saved properties from the original app” instructions
to export from the original Render origin in the
same browser/profile that holds the saves. The supplied bookmarklet checks the
original hostname, reads only House Alpha's saved-property list, and downloads
a local JSON file. It does not transfer data to the server.

Sign in on the new site, choose **Import JSON**, inspect the count, and confirm.
Imports keep existing entries with matching IDs or deduplication keys and add
the others; they do not silently overwrite cloud versions. An old export can
re-add a property that was deleted later, so review an export before importing
it during conflict recovery. Signed-out saves on the new site can be imported
explicitly using **Import this device's library**. Signing in alone uploads
nothing and leaves the original browser library intact.

Browser JSON exports restore property data only, not account credentials or
server sessions. Account recovery is an operator task; no email reset service
is configured. On the VM, set a new password through a protected terminal:

```sh
sudo -u house-alpha /opt/house-alpha/venv/bin/python /opt/house-alpha/current/library_admin.py reset-password USERNAME
```

The command prompts rather than accepting a password in shell arguments and
revokes all sessions for that account. If registration is changed to `invite`,
`library_admin.py create-invite` creates a one-use invitation; treat its output
as a private credential. Use `library_admin.py cleanup` to remove expired
sessions, invitations, and rate buckets when needed.

## Database restore

Restore replaces the entire server database, including every user's library.
Prefer per-account JSON import when only property data needs recovery. Set aside
the chosen restore snapshot under a distinct private filename first: creating a
new backup replaces any snapshot with today's date. Then take an off-server copy
of the current database. Do not copy a running `library.sqlite3` alone: uncheckpointed
WAL data may be missing. Use the backup helper's consistent snapshot.

1. Check the selected snapshot with SQLite `PRAGMA integrity_check`; the result
   must be `ok`. For an off-server copy, upload through the existing SSH helper
   into a private temporary directory on the VM. Keep it outside the web root.
2. Create `/var/lib/house-alpha-guard/paused` with an operator-maintenance reason,
   then stop `house-alpha-library`. Keep any prior pause reason for later review.
3. Preserve the current `library.sqlite3`, `library.sqlite3-wal`, and
   `library.sqlite3-shm`, if present, together in a new root-owned mode-700
   recovery directory. The library service must remain stopped while moving
   them. Do not leave old WAL/SHM files alongside a replacement database.
4. Install the chosen snapshot as `/var/lib/house-alpha/library.sqlite3`, owned
   by `house-alpha:house-alpha`, mode 600.
5. While stopped, validate the restored database and revoke restored session
   and invitation tokens, so a previously invalidated token is not revived:

   ```sh
   sudo -u house-alpha /opt/house-alpha/venv/bin/python - <<'PY'
   import sqlite3
   with sqlite3.connect('/var/lib/house-alpha/library.sqlite3') as db:
       assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
       db.execute('DELETE FROM sessions')
       db.execute('DELETE FROM invites')
   print('Restore integrity checked; all users must sign in again.')
   PY
   ```

6. Start `house-alpha-library`, inspect its journal, and check the loopback
   `/api/library/session` endpoint. Sign in and verify a known library, then
   save and reopen one test change. The restored app recreates WAL mode at
   startup. Do not expose the database or use its contents in diagnostic logs.
7. Resume the public app only after the resource guard and any previous pause
   reason are resolved. Create and download a new verified backup. Retain the
   pre-restore recovery copy until the restored application is confirmed.

For a replacement VM, recreate the service user, private data directory,
Python environment, nginx configuration, and systemd units before restoring.
Update SSH host verification, firewall source IP, DNS, and TLS for the new
server. A changed public IP alone does not transfer browser storage or sessions.

## Certificate renewal and remaining verification

The domain certificate, HTTPS configuration, and renewal timer are deployed.
The successful rehearsal used the modern client, scoped to the served domain
certificate, and ran the deployment hook. To repeat that check during later
maintenance:

```sh
sudo /opt/certbot/bin/certbot renew --cert-name house-alpha-domain --dry-run --run-deploy-hooks --deploy-hook /usr/sbin/nginx-reload-house-alpha
systemctl list-timers house-alpha-certbot.timer --all --no-pager
sudo journalctl -u house-alpha-certbot -n 40 --no-pager
```

Keep `--cert-name house-alpha-domain` in the custom service so the unused IP
certificate is not renewed. Keep the distribution `certbot.timer` disabled to
avoid overlapping renewal jobs. A future real renewal updates nginx through
the hook; periodically verify the certificate actually served at the domain.
The currently observed expiry is 2027-01-22 and will change after renewal.

Public HTTPS integration passed 35 checks with normal certificate validation,
including registration, authentication, tenant isolation, save/read, revision
conflicts, Origin and CSRF protection, logout revocation, conditional reads,
export, and source-file denial for GET and HEAD. Browser QA also confirmed
save, cloud restore after reload, Open, and private workspace clearing on
sign-out. Disposable QA accounts were removed. Actual user migration has not
been performed.

For a later hostname or VM change, preserve the apex site and other subdomains;
update only the intended DNS record, validate authoritative DNS and the HTTP
ACME challenge path, obtain the matching certificate, set the exact origin,
restart application services, and validate/reload nginx before repeating those
public checks. Squarespace's embedded verification can require standalone
login and reauthentication if its challenge screen is blank.
