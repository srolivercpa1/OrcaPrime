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
- [ ] Add failing tests for disabled/wrong token, CSRF origin, successful setup and repeated/concurrent setup, hashing and production configuration.
- [ ] Implement helpers, UI and blueprint; preserve existing bootstrap CLI.
- [ ] Run the API tests and actual browser setup flow; commit.

### Task 2: Encrypted external backup
Files: webapp/backup.py, webapp/cli.py, tests/web/test_hosting.py, .github/workflows/web-backup.yml, .github/workflows/web.yml, webapp/README.md.
Interface: backup(engine, directory, keep=14, encryption_key=None); restore(url, path, encryption_key=None); CLI backup --encrypted requires BACKUP_ENCRYPTION_KEY and never initializes schema.
- [ ] Add failing tests for encryption roundtrip, photos/no sessions, missing/wrong key, tampering, nonempty destination and read-only backup connection.
- [ ] Add authenticated encryption around gzip bytes before atomic private file write; schedule encrypted-only artifacts with 14-day retention and credentials only at the backup step.
- [ ] Run web and regression tests, Docker and browser CI; obtain independent review and fix important findings.

### Task 3: Publish
- [ ] Verify connections to both providers, create only the authorized free resources and configure private environment variables.
- [ ] Publish the tested web branch, verify health and owner setup; activate scheduled backups on the default branch only once deployment exists.
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
