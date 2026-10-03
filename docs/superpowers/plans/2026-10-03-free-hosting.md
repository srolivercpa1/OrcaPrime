# Free Hosting Implementation Plan

> Execute inline using superpowers:executing-plans; user authorization for recommended implementation and publishing already supplied.

**Goal:** Prepare and deploy OrçaPrime Web 1.0 on Render Free with Neon and external encrypted backups.
**Architecture:** Reuse the existing FastAPI app, bootstrap and compressed snapshot format. Add a token-protected one-time setup, a Render blueprint and an external GitHub Actions backup schedule.
**Tech Stack:** Python, FastAPI, SQLAlchemy, PostgreSQL, Fernet, GitHub Actions, Docker.
**Spec:** docs/superpowers/specs/2026-10-03-free-hosting.md

## Global Constraints
Version 1.0; preserve desktop and licensing deployment; free plans only; never expose secrets or store unencrypted cloud backups; no public unprotected owner registration.

## Review Focus
Concurrent first owners, setup token exposure through validation/logs, failed encryption creating plaintext, restoring a corrupted archive into production, scheduling that is configured but not actually active.

### Task 1: One-time setup and Render configuration
Files: webapp/security.py, webapp/setup.py, webapp/api.py, webapp/server.py, webapp/static/setup.html, webapp/static/setup.js, render.yaml, tests/web/test_hosting.py.
Interface: create_app(..., setup_token=None); create_owner(db, email, password) flushes a fixed singleton owner ID; setup endpoints check token and existing owner; production_config(environ) returns normalized database URL and validated origin.
- [x] Add failing tests for disabled/wrong token, CSRF origin, successful setup and repeated/concurrent setup, hashing and production configuration.
- [x] Implement helpers, UI and blueprint; preserve existing bootstrap CLI.
- [x] Run the API tests and actual browser setup flow; commit.

### Task 2: Encrypted external backup
Files: webapp/backup.py, webapp/cli.py, tests/web/test_hosting.py, .github/workflows/web-backup.yml, .github/workflows/web.yml, webapp/README.md.
Interface: backup(engine, directory, keep=14, encryption_key=None); restore(url, path, encryption_key=None); CLI backup --encrypted requires BACKUP_ENCRYPTION_KEY and never initializes schema.
- [x] Add failing tests for encryption roundtrip, photos/no sessions, missing/wrong key, tampering, nonempty destination and read-only backup connection.
- [x] Add authenticated encryption around gzip bytes before atomic private file write; schedule encrypted-only artifacts with 14-day retention and credentials only at the backup step.
- [x] Run web and regression tests, Docker and browser CI; obtain independent review and fix important findings.

### Task 3: Publish
- [x] Verify connections to both providers, create only the authorized free resources and configure private environment variables.
- [x] Publish the tested web branch, verify public health and availability of protected owner setup.
- [ ] Activate scheduled backups on the default branch and configure private GitHub Actions Secrets.
- [ ] Verify a real encrypted backup and isolated restore; provide the public URL, or state the exact remaining connection block.

## Execution ledger
- Existing isolated worktree verified: feat/orcaprime-web-1.0; base local commit 294deb1. No changes to the desktop worktree.
- Ruling: prior user authorization selects inline execution and recommended implementation; do not reopen design approval gates.
- Pre-flight: setup helper shared by CLI and HTTP to enforce singleton creation; backup CLI and workflow share encrypted snapshot format. No schema changes needed.
- Render plugin suggested; installation currently unconfirmed. Neon installed but callable tools have not yet appeared in this running tool registry. No provider resource has been created.
- Tests RED: six hosting tests failed against the original interfaces before implementation.
- Ruling: local sandbox stalls even a minimal FastAPI TestClient request in thread notification; running the same tests with the authorized sandbox escalation succeeds. No application change made for this environment restriction.
- API/backup GREEN: full local regression 148 passed, 53 skipped (platform, PostgreSQL and opt-in browser checks); node syntax checks and git diff --check passed. PostgreSQL and browser are delegated to the existing web CI.
- Cloud backup activation remains incomplete: no provider resources or live Secrets were created; workflow is prepared on the web branch and will not run daily until integrated on the default branch.
- Independent review: no material findings; three configuration/backup/CLI tests independently passed. Live deployment, PostgreSQL, browser and Docker remain external verification gates, not waived.
- Browser CI found two installation links: the initial unauthorized /me response and its outer catch each render login while their setup checks complete asynchronously. Bind each result to its original connected footer and make insertion idempotent; existing browser test reproduces the failure.
- Read-only backup test permits PostgreSQL driver SHOW queries as well as SELECT, based on SQLAlchemy's actual initialization code; neither changes data.

- Final CI GREEN on remote c69cbec53dc0cd50c068b39365e2c30cb142f154: run 37087919248, job 111101923738. Full suite 150 passed / 51 skipped, PostgreSQL 16 passed, both browser flows passed, Docker image built and returned health version 1.0. Setup mobile screenshot inspected.
- Artifact 11261058183 (OrcaPrime-Web-1.0) contains the verified deployment package. Old failure was run 37087774852; corrected run is successful.
- Pending: Render plugin still reports installed=false. Neon reports installed=true but no callable Neon tools are exposed in the current tool registry. No database, public site, installation code, production credentials or scheduled backup has been provisioned; continue account connection/provisioning next.

- Connection follow-up 2026-10-03: Neon tools are now available. describe_project({}) returned INVALID_ARGUMENT because connection is unscoped and project_id is required. This exposed tool set has neither list_projects nor create_project; no linked .neon file or authenticated CLI/API key is available. Need the user’s Neon project URL/ID to target the database. Render still reports installed=false. No resource was modified.

### Neon provisioning follow-up, 2026-10-03
- User supplied the existing project `noisy-breeze-33359018`, production branch `br-lucky-field-b53pwf5z`. Verified OrçaPrime, PostgreSQL 18, Ohio (`aws-us-east-2`), free plan. Existing `neon_auth` schema has nine tables and is preserved.
- Production endpoint `ep-weathered-violet-b52bte52`: connection pooling enabled, compute maximum reduced from 2 to 0.5 CU, minimum remains 0.25 CU. The free plan rejects explicit suspend-timeout changes; left its managed default unchanged. No paid resource was created.
- Created validation branch `br-broad-forest-b5o7letq` (`orcaprime-validation-20261003`), minimum/maximum 0.25 CU. Created the six application tables and seven indexes from the tested SQLAlchemy metadata there first.
- Direct PostgreSQL smoke execution was blocked by this environment's DNS resolution, including with approved network escalation. No direct API or backup test against live Neon is claimed. Existing CI PostgreSQL 16, browser, Docker and encrypted restore checks remain green.
- Through Neon's SQL integration, validated all six tables on PostgreSQL 18: temporary company, user, session, customer, order, photo bytes and audit writes succeeded under a restricted application role. Read-only backup role could read records but not sessions or write data; application role could not access `neon_auth`. Test inserts were rolled back in the same transaction. Validation branch retains the empty application schema and NOLOGIN roles.
- Applied the same six-table/seven-index schema to production in one transaction. Verified six app tables, nine preserved Neon Auth tables and zero application users. Created `orcaprime_app` with CRUD on the six app tables and `orcaprime_backup` with SELECT on five tables, excluding sessions; no schema creation or Neon Auth access granted. Both remain NOLOGIN until their credentials can be installed privately at the destinations.
- Set `region: ohio` in the Render blueprint to match the existing Neon region; confirmed against the official Blueprint reference. Application code and version 1.0 are unchanged.
- Render plugin now reports installed, but this session still exposes no Render operations. Fallback under prior user authorization opened the Render dashboard and reached its sign-in screen. No Render resource/public URL exists yet. Next: secure browser sign-in, create the free web service from the tested web branch, configure its private credentials, verify health and setup, then activate and verify external scheduled backup. Do not merge desktop-releasing main merely to deploy the web service.

### Render live, 2026-10-03
- After the user's Render login, browser automation was interrupted by an automatic approval-review usage limit; no service was created by that attempt. On the next continuation, Render MCP operations became available and were used directly.
- Confirmed the existing workspace `tea-db0doogu01pc739u1cu0` (Mateus's workspace), with no prior services. Because this MCP cannot specify Docker configuration, changed the deployment configuration to the equivalent native Python runtime: Python 3.12.15, the existing web requirements and Uvicorn factory, one worker, Render `$PORT`. Official Render version documentation and Python's released version were verified. Application code remains the previously tested version 1.0; Docker remains an optional deployment format.
- Enabled LOGIN only for `orcaprime_app` with a cryptographically random password and stored the pooled TLS Neon connection privately in Render `DATABASE_URL`. Provisioned a random private `SETUP_TOKEN`; did not create a default owner/password or expose either secret. `orcaprime_backup` still has NOLOGIN and no backup has been scheduled or generated from production.
- Created free Ohio service `srv-db0heemgekts739niug0`, name `orcaprime-web`, URL `https://orcaprime-web.onrender.com`, dashboard `https://dashboard.render.com/web/srv-db0heemgekts739niug0`. Auto-deploy is off. Native creation API leaves healthCheckPath empty (TCP health check); configure `/health` in the dashboard when panel access is available.
- Deployment `dep-db0hef6gekts739nj05g` of remote commit `76cccd20311eea042ad1209f5872e13e85254215` became LIVE at 2026-10-03T14:58:50Z. Render logs confirmed startup, binding to port 10000, and GET / 200.
- Public HTTP checks passed after the free service finished waking: GET /health 200 with {status:ok,version:1.0}; GET /api/setup 200 with available:true (live database read using the restricted application role); GET / 200; unauthenticated GET /api/companies 401. All responses included Content-Security-Policy. An earlier 25-second HTTP timeout occurred during startup; a subsequent bounded check succeeded. Cloud Browser blocked this application URL with ERR_BLOCKED_BY_CLIENT, so no live browser screenshot or authenticated owner flow is claimed.
- First owner must complete `/setup`, using SETUP_TOKEN from the Render Environment page and their own email/password. The protected enrollment page is available; no owner was created during verification.
- Backup blocker: GitHub connector cannot manage Actions Secrets. Browser fallback reached GitHub sign-in; the user chose Google in the secure authentication prompt, but the browser session reset before account selection completed. A fresh target-page check showed signed-out GitHub. No secrets were entered, backup role remains NOLOGIN, workflow remains only on the web branch, and main/desktop releases are untouched. Resume GitHub authentication, configure the two private backup Secrets, activate the scheduled workflow without triggering an unrelated Windows release, run a real backup and validate restoration.
