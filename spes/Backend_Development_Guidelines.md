
# Backend Development Strategy & Standards: Rapid & Low-Effort Delivery

This document defines the "Minimalist Engineering Protocol" for the RIMIT Education B2B Aggregator. Our primary objective is to maximize feature velocity by leveraging built-in framework capabilities, minimizing infrastructure complexity, and enforcing strict "No-Custom-Code" rules.

---

## 1. Development Principles
*   **Leverage Frameworks:** If Django or its ecosystem has a built-in feature, use it. Never build custom auth, search, or task-queueing if a library exists.
*   **Database as Source of Truth:** Let PostgreSQL do the heavy lifting (filtering, sorting, full-text search, RLS).
*   **Infrastructure Minimalism:** No external event buses (like EventBridge) or WAFs. Rely on Nginx and Django’s internal security posture.
*   **Asynchronous-by-Default:** Any logic that is not strictly needed for the immediate API response (e.g., notifications, file S3-transfers) must be handled by Celery in the background.

## 2. Technical Stack
*   **Backend:** Python + Django 5.x (Monolith structure).
*   **Database:** PostgreSQL 16+ (Search, RLS, JSONB).
*   **Tasks:** Celery + Redis (Standardized for background jobs).
*   **Identity:** Keycloak (OIDC/OAuth2).
*   **Ingress:** Nginx (Reverse Proxy/SSL/Security Headers).

## 3. Development Standards (The "Least Effort" Rules)
1.  **Search Implementation:** Use PostgreSQL `SearchVector` and `GIN` indexes.
    *   *Rule:* Do not add Elasticsearch/OpenSearch for search needs unless the dataset exceeds 500,000+ complex searchable entities.
2.  **Event Orchestration:** Use **Django Signals** for simple post-save triggers and **Celery** for complex background workflows.
    *   *Rule:* Never use external event buses (EventBridge/SNS) for inter-service communication within the same monolith.
3.  **File Management:**
    *   *Rule:* All file uploads (10MB-100MB) must use `TemporaryFileUploadHandler` to spool to disk. Direct-to-S3 is only permitted if local disk space becomes a scaling bottleneck.
4.  **Security:**
    *   *Rule:* Nginx handles rate-limiting (`limit_req`) and SSL. Django `SecurityMiddleware` handles CSRF, clickjacking, and XSS.
5.  **Multi-Tenancy:**
    *   *Rule:* PostgreSQL **Row-Level Security (RLS)** is the *only* way to handle tenant isolation. Never trust application-layer ORM `filter(sub_center_id=...)` alone for security-critical data.

## 4. Rapid Development Workflow
*   **Rapid API Creation:** Use **Django REST Framework (DRF)**.
    *   *Rule:* Use `ModelViewSet` for all CRUD operations. Do not manually write Views unless the logic is non-standard.
*   **Admin Back-office:**
    *   *Rule:* Use the Django Admin for all "internal" data management. Do not build custom UI screens for internal data maintenance.
*   **Validation:** Use `DRF Serializers` for all incoming payload validation.

## 5. Deployment & Maintenance Standards
*   **Environment Parity:** Docker Compose for development; Docker Swarm or simple K8s/ECS for production. No deviation.
*   **Documentation:** All API endpoints must be documented using `drf-spectacular` (OpenAPI/Swagger auto-generation). Do not write manual API docs.
*   **Logging:** Centralized logs in JSON format via `structlog` for easy ingestion into local observability stacks.

---
