# RIMIT B2B Aggregator & Centralized Admission Management System

Production-ready Django backend implementing the RIMIT Education & SPES Education RFP for a unified B2B University Aggregator and Centralized Admission Management platform.

## Status

✅ **All 4 RFP modules implemented and tested** — 97/97 tests passing, 84% line coverage.

## Architecture

Per the development plan (Section 4): **Pragmatic Modular Monolith** on a minimalist open-source stack.

| Layer | Technology | Role |
|-------|-----------|------|
| Ingress | Nginx 1.26 | Reverse proxy, SSL, rate limiting |
| Backend | Django 5.x + DRF 3.15 | Monolith serving all 4 modules |
| Database | PostgreSQL 16 (SQLite for dev) | Persistence, RLS multi-tenancy, full-text search |
| Async | Celery 5.4 + Redis 7 | Notifications, webhooks, document processing |
| Identity | Keycloak 24 (OIDC) | RBAC, MFA — Token auth used as dev fallback |
| Storage | MinIO (S3-compatible) | Encrypted document vault |
| Docs | drf-spectacular | OpenAPI 3.1 auto-generation |

## Project Structure

```
rimit/
├── config/
│   ├── settings/{base,dev,prod}.py     # 3-tier settings
│   ├── urls.py                          # URL routing
│   ├── celery.py                        # Celery app
│   └── wsgi.py / asgi.py
├── apps/
│   ├── common/        # Base models, middleware, permissions
│   ├── aggregator/    # Module 1: Universities, courses, fees, prospectus
│   ├── partners/      # Module 2: Sub-centers, system users
│   ├── admissions/    # Module 2: Students, docs, enrollments
│   ├── rules/         # Module 3: Intake sessions, Session Enforcement Matrix
│   ├── integrations/  # Module 4: Meta + Razorpay webhooks
│   ├── notifications/ # Module 4: WhatsApp/SMS/Email + broadcast
│   ├── finance/       # Cross-cutting: Payment ledger, financial dashboard
│   └── audit/         # Cross-cutting: Audit trail (partitioned in prod)
├── tests/             # 97 tests across 7 modules
├── docker-compose.yml # Full dev stack (Django + Celery + PG + Redis + Keycloak + MinIO)
├── Dockerfile
├── requirements.txt
├── pytest.ini
├── conftest.py
└── schema.yml         # Generated OpenAPI 3.1 schema (132KB, 28+ endpoints)
```

## Quick Start

### Dev environment (SQLite + eager Celery)

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

API available at http://localhost:8000/api/v1/
Swagger UI at http://localhost:8000/api/v1/schema/swagger-ui/

### Full stack (Docker Compose)

```bash
docker-compose up
```

Brings up: Django app, Celery worker, Celery beat, PostgreSQL 16, Redis 7, Keycloak 24, MinIO.

### Run tests

```bash
pytest                          # All 97 tests
pytest --cov=apps              # With coverage (84%)
pytest tests/test_module2_b2b_portal.py::TestTenantIsolation -v  # RLS isolation tests
```

## Modules Implemented

### Module 1: Centralized University Aggregator Hub
- ✅ University CRUD (super_admin writes, all roles read)
- ✅ Course search with multi-attribute filters (stream, duration, budget)
- ✅ Fee structures (one-to-many per course)
- ✅ Document vault with presigned URL downloads (15-min TTL)
- ✅ 17 tests

### Module 2: B2B Sub-Center Partner Portal
- ✅ Sub-center management (super_admin)
- ✅ Student registration with Aadhar SHA-256 hashing (never plaintext)
- ✅ **Row-Level Security equivalent** via TenantManager (auto-filter by sub_center)
- ✅ Cross-tenant access returns 404 (7 dedicated RLS tests)
- ✅ Document upload + verify/reject workflow
- ✅ Enrollment state machine (Applied → Doc Verified → Fee Pending → Fee Paid → Enrolled)
- ✅ 24 tests

### Module 3: Advanced Business Logic & Intake Controls
- ✅ Intake sessions (active/inactive, fresh_allowed flag)
- ✅ Rules configurations (JSONB conditions, super_admin only)
- ✅ **Session Enforcement Matrix engine** — implements RFP example:
  fresh candidates blocked from July, routed to October with suggestion
- ✅ Pre-flight validation endpoint: `/api/v1/rules/validate/`
- ✅ Rule priority ordering, inactive rule bypass
- ✅ 18 tests

### Module 4: Marketing & Communication Integrations
- ✅ Meta Lead Ads webhook (HMAC-SHA256 signature verification, idempotent dedup by leadgen_id)
- ✅ Razorpay payment webhook (idempotent on transaction_ref, auto-transitions enrollment to Fee Paid)
- ✅ WhatsApp/SMS/Email notification pipeline via Celery
- ✅ Broadcast endpoint (super_admin only, rate-limited)
- ✅ Webhook verification challenge (Meta subscription handshake)
- ✅ 16 tests

### Cross-cutting
- ✅ Audit log middleware (auto-logs all POST/PUT/PATCH/DELETE)
- ✅ Payment ledger with financial dashboard (summary + by_sub_center)
- ✅ RBAC matrix: 4 roles (super_admin, academic_head, counselor, finance) + unauthenticated
- ✅ MFA stub endpoint (accepts 6-digit OTP in dev)
- ✅ Token auth + profile endpoint
- ✅ 16 tests + 6 integration tests

## Critical Security Controls

1. **Tenant isolation**: `TenantManager` auto-filters all tenant-scoped queries by `sub_center_id` from JWT claim. Bypassed only for `super_admin` and `academic_head` roles. **In production with PostgreSQL, Row-Level Security policies provide authoritative DB-level enforcement** — the app-layer manager is the safety net.

2. **PII protection**: Aadhar numbers stored as SHA-256 hashes with salt (via `hash_aadhar()`), never plaintext. Phone/email stored plaintext (required for notifications) but masked in audit displays.

3. **Webhook signature verification**: Meta webhooks verified via HMAC-SHA256. Razorpay signature verification stubbed in dev (configurable in prod).

4. **Idempotency**: 
   - `lead_ingestion_logs.leadgen_id` unique → duplicate Meta webhooks don't create duplicates
   - `payment_ledgers.transaction_ref` unique → duplicate Razorpay webhooks don't double-charge
   - `notification_logs.external_message_id` → Celery retries don't double-send

5. **State machine validation**: Enrollment status transitions validated against `Enrollment.TRANSITIONS` dict; invalid transitions return 400.

## Test Coverage Summary

```
97 tests passed in 6.42s
84% line coverage on apps/ (excluding migrations)

tests/test_module1_aggregator.py         17 tests  ✅
tests/test_module2_b2b_portal.py         24 tests  ✅ (incl. 7 RLS isolation tests)
tests/test_module3_business_logic.py     18 tests  ✅
tests/test_module4_marketing.py          16 tests  ✅
tests/test_module5_6_crosscutting.py     16 tests  ✅
tests/test_module7_integration.py         6 tests  ✅ (end-to-end lifecycle)
```

## Production Deployment Notes

Per development plan Section 14:

1. **Settings**: `DJANGO_SETTINGS_MODULE=config.settings.prod`
2. **Database**: PostgreSQL 16 Multi-AZ (RDS), RLS policies required (see `apps/common/models.py` comments for DDL)
3. **Identity**: Configure Keycloak realm with 4 roles, OTP-over-WhatsApp MFA flow
4. **Storage**: MinIO 3-node cluster, AES-256 bucket encryption
5. **Backup**: WAL archiving every 15min, nightly pg_dump, quarterly DR drill
6. **Monitoring**: structlog JSON → Loki, django-prometheus → Prometheus, Sentry for errors
7. **CI/CD**: GitHub Actions (lint → test → build → deploy staging → manual prod gate)

## Open Items (per Development Plan Section 15)

- 6 strategic RFIs for RIMIT to answer (Section 15.3)
- 8 assumptions to validate (Section 15.1)
- 5 hard constraints documented (Section 15.2)

## License

Proprietary — RIMIT Educational Charitable Trust. All rights reserved.
