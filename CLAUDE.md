# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A web application that allows users to upload files, compute their hashes, and query MISP and VirusTotal to determine if the files are malicious. Results are displayed on a results page and emailed to the logged-in user.

**Key capabilities:**
- File upload → SHA256/MD5/SHA1 hash calculation → MISP + VirusTotal lookup
- Compressed archive handling (zip, 7z, rar, tar, tar.gz, tar.bz2): hash the archive itself, then extract (if no password) and hash each inner file
- Authentication: local accounts (SQLite) and Active Directory (LDAP)
- Role-based access: `admin` and `user` groups
- Admin UI: manage users and their email addresses, configure MISP/VT/AD/SMTP settings
- Results emailed to the user's registered email address

## Tech Stack

- **Backend**: Python / Flask
- **Database**: SQLite via SQLAlchemy (local user accounts, settings)
- **Auth**: Flask-Login for session management; `ldap3` for Active Directory
- **File extraction**: `zipfile` (stdlib), `py7zr` (7z), `rarfile` (RAR), `tarfile` (stdlib)
- **Hash**: `hashlib` (stdlib) — SHA256, MD5, SHA1
- **MISP**: `pymisp`
- **VirusTotal**: `vt-py` (async) or `requests` against VT API v3
- **Email**: `Flask-Mail` (SMTP)
- **Frontend**: Jinja2 templates + Bootstrap 5

## Project Structure

```
Uploader4MISP/
├── app/
│   ├── __init__.py          # Flask app factory, extensions init
│   ├── models.py            # SQLAlchemy models: User, Role, Setting
│   ├── auth/                # Blueprint: login, logout, AD auth
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── ldap_helper.py   # LDAP/AD authentication logic
│   ├── main/                # Blueprint: file upload, results
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── hash_utils.py    # Hash calculation helpers
│   │   ├── archive_utils.py # Archive detection & extraction
│   │   ├── misp_client.py   # PyMISP wrapper
│   │   ├── vt_client.py     # VirusTotal API wrapper
│   │   └── email_utils.py   # Email result sending
│   └── admin/               # Blueprint: user mgmt, settings
│       ├── __init__.py
│       └── routes.py
├── templates/
│   ├── base.html
│   ├── auth/login.html
│   ├── main/upload.html
│   ├── main/results.html
│   └── admin/
│       ├── users.html
│       └── settings.html
├── static/
├── config.py                # Config classes (Development, Production)
├── requirements.txt
├── run.py                   # Entry point: `python run.py`
└── instance/
    └── app.db               # SQLite DB (auto-created)
```

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python run.py

# Initialize/reset the database (creates admin:admin account)
flask db-init

# Run with a specific config
FLASK_ENV=production python run.py
```

## Configuration (via Admin UI or environment variables)

| Setting | Env var | Description |
|---|---|---|
| MISP URL | `MISP_URL` | e.g. `https://misp.local` |
| MISP API Key | `MISP_KEY` | Auth key |
| MISP verify SSL | `MISP_VERIFYCERT` | `true`/`false` |
| VirusTotal API Key | `VT_API_KEY` | |
| SMTP host/port/user/pass | `MAIL_*` | Flask-Mail settings |
| AD server | `AD_SERVER` | LDAP server hostname |
| AD base DN | `AD_BASE_DN` | Search base |
| AD bind DN / password | `AD_BIND_DN`, `AD_BIND_PW` | Service account |

Settings are persisted in the `Setting` table and override environment variables at runtime.

## Architecture Notes

### Authentication flow
- Login page accepts username + password.
- Try local DB first; if not found (or if AD is enabled and user is flagged as AD user), try LDAP bind against AD.
- AD-authenticated users are auto-provisioned in the local DB on first login with role `user`.

### File processing flow (`main/routes.py` → helpers)
1. Save upload to `instance/uploads/<uuid>/`
2. `hash_utils.compute_hashes(path)` → `{md5, sha1, sha256}`
3. Query MISP (`misp_client.search_hash`) and VirusTotal (`vt_client.lookup_hash`) for each hash
4. If file is an archive (`archive_utils.is_archive`):
   - Record archive-level results
   - Attempt extraction to `instance/temp/<uuid>/` via `archive_utils.extract`
   - Repeat steps 2–3 for each extracted file
5. Assemble combined results dict
6. Render `results.html` and return to user
7. `email_utils.send_results(user.email, results)` in a background thread

### Temp file cleanup
Uploaded files and temp extraction dirs are deleted after results are assembled (or on a timed cleanup job). Files are never stored permanently.

### Admin settings page
Persists MISP URL/key, VT key, SMTP config, and AD config to the `Setting` table. Changes take effect immediately without restart.
