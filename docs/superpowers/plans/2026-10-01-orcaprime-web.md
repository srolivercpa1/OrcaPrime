# OrçaPrime Web Implementation Plan

> Execute inline using superpowers:executing-plans; authorization already supplied by the owner.

**Goal:** Deliver a functional, separately deployable OrçaPrime Web with the approved Apex-inspired navigation.
**Architecture:** FastAPI same-origin HTML/JS application, SQLAlchemy transactions with PostgreSQL in production and SQLite for local tests. Private image data in the database initially, included in compressed backups; move to object storage once hosting credentials are available.
**Spec:** docs/superpowers/specs/2026-10-01-orcaprime-web.md

## Global Constraints
Visible version 1.0. Preserve desktop files. Portuguese UI. Never trust tenant IDs from clients. No public signup creating owner permissions. No fake operational metrics. Fiscal integration explicitly unavailable until configured.

## Review Focus
Tenant isolation, revoked sessions, CSRF and XSS; duplicate transitions/stock changes; destructive deletion accounting; mobile scroll/layout; empty state and failed requests.

## Task 1 — Authentication and storage
Files: webapp/db.py, webapp/security.py, webapp/api.py, tests/web/test_web.py.
Interface: create_app(database_url, secure_cookie=False); bootstrap(database_url, email, password) creates sole owner; /api/login and /api/me return session identity/CSRF.
- [ ] Test failed login, logout, cookie flags, CSRF, tenant isolation and owner-only company provisioning; observe RED.
- [ ] Implement models, password hashing, session tokens, role authorization, company suspension and audit.
- [ ] Run tests and record GREEN.

## Task 2 — Operations
Files: webapp/operations.py, webapp/documents.py, tests/web/test_web.py.
Interface: /api/{customers,orders,quotes,parts,entries}, /api/dashboard; /api/orders/{id}/photos and /document.
- [ ] Test isolation, customer/OS deletion, transition history, idempotent quote conversion, inventory atomicity, images and document access; observe RED.
- [ ] Implement transactional operations, validation and PDF generation.
- [ ] Verify with full API suite.

## Task 3 — Interface
Files: webapp/static/{index.html,app.css,app.js}, assets/brand.png reused through server route.
- [ ] Build login, sidebar, dashboard, forms, tables, delivered list, company configuration, user and owner panels.
- [ ] Exercise real browser flows with local automation where available; test desktop and mobile dimensions, screenshots and CRUD.

## Task 4 — Delivery
Files: webapp/cli.py, webapp/README.md, webapp/Dockerfile, compose.web.yml, requirements-web.txt, .github/workflows/web.yml.
- [ ] Compressed backup and restore test, deployment configuration, no production default credentials.
- [ ] Full regression suite and independent review, fix material findings.
- [ ] Commit and publish separate web branch with CI. Public hosting is contingent on an available hosting account; report status accurately.

## Execution ledger
- API baseline: seven integration tests passed; initial red runs captured missing operations, validation, backup and password endpoint.
- Full local regression before review: 140 passed, 51 skipped (native Windows and optional browser).
- Review found finance projection leak, stale auth after company lock, role/action mismatch, missing deletion preview and period controls. Corrections added with regression tests, PostgreSQL concurrency test in CI and browser checks.
- Ruling: no new hosting project could be provisioned; Railway returned free-plan resource provision limit exceeded. Preserve existing licensing service; prepare deployable package and report the account block. No public deployment claim.
- Ruling: use database-backed private photos in this first deployment package to keep backup atomic. Object storage and desktop migration remain separate, explicitly documented work; no migration performed.
- Review identified financial date ambiguity: reports filter by creation date and clearly label this basis; paid_at is recorded on newly confirmed payments.
