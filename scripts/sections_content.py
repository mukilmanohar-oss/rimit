"""
Content sections for the RIMIT Development Plan.

Each section_* function returns a list of ReportLab flowables.
Imports helpers.py for shared styles and helpers.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from helpers import (
    h1, h2, h3, p, pl, bullet, caption, code, spacer,
    make_table, fit_image, safe_keep,
    PAGE_W, PAGE_H, MARGIN, CONTENT_W, CONTENT_H,
    HEADER_FILL, ACCENT, ACCENT_2, BORDER, TEXT_PRIMARY, TEXT_MUTED,
    CARD_BG, TABLE_STRIPE, SEM_SUCCESS, SEM_WARNING, SEM_ERROR, SEM_INFO,
    BODY, BODY_LEFT, BULLET, TABLE_CELL_STYLE,
)
from reportlab.platypus import Paragraph, Spacer, PageBreak, Table, TableStyle, Image, KeepTogether, CondPageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors

DIAG_DIR = "/home/z/my-project/scripts/diagrams"

# ═══════════════════════════════════════════════════════════════════════
# Section 1: Executive Technical Strategy
# ═══════════════════════════════════════════════════════════════════════
def section_exec_strategy():
    s = []
    s.append(h1("1. Executive Technical Strategy"))
    s.append(p(
        "This document presents the comprehensive engineering blueprint for the RIMIT Education &amp; SPES Education Unified B2B University Aggregator and Centralized Admission Management System. The proposed architecture deliberately adopts a <b>Pragmatic Modular Monolith</b> paradigm built on a minimalist open-source stack &mdash; Django 5.x, PostgreSQL 16, Celery with Redis, Keycloak, and Nginx &mdash; deliberately avoiding distributed-systems complexity such as Elasticsearch, EventBridge, or microservices for a project of this scale and team composition."
    ))
    s.append(p(
        "The architectural philosophy is anchored on three principles articulated in the RIMIT backend guidelines: <b>leverage frameworks over custom code</b>, <b>treat PostgreSQL as the single source of truth</b> for persistence, search, and multi-tenancy, and <b>handle all non-critical-path logic asynchronously</b> via Celery. This approach maximizes feature velocity for a 5-engineer team, minimizes monthly cloud spend (estimated at INR 35,000&ndash;50,000 for a single-region production deployment), and reduces operational toil by eliminating the moving parts that typically plague distributed systems &mdash; CDC pipelines, schema registries, inter-service auth, and event replay logic."
    ))
    s.append(p(
        "All four RFP functional modules map cleanly onto this stack. Module 1 (University Aggregator Hub) is delivered through Django REST Framework ViewSets exposing the universities, courses, fee_structures, and university_doc_vault tables, with PostgreSQL GIN-indexed tsvector columns providing sub-100ms multi-attribute search across the entire course catalogue. Module 2 (B2B Sub-Center Portal) is built on Appsmith Community Edition bound to the same DRF APIs, with PostgreSQL Row-Level Security (RLS) policies guaranteeing that no sub-center can ever read another tenant&rsquo;s student records &mdash; the database itself enforces isolation, not application-layer filters that are vulnerable to programmer error."
    ))
    s.append(p(
        "Module 3 (Advanced Business Logic) is implemented as a rules-configurations table storing JSONB conditions, evaluated by a thin Django service layer that programmatically enforces session constraints (e.g., blocking fresh candidates from July intake and routing them to October). Module 4 (Marketing &amp; Communication) integrates Meta Lead Ads webhooks, WhatsApp Business API, and SMTP via Celery workers with exponential backoff and dead-letter queues, ensuring that no inbound lead is ever silently dropped. Multi-Factor Authentication for B2B sub-center logins is enforced at the Keycloak layer via OTP-over-WhatsApp or SMS, satisfying the RFP&rsquo;s explicit MFA requirement without bespoke authentication code."
    ))
    s.append(p(
        "Commercially, this minimalist stack delivers a <b>30&ndash;45% reduction in Year-1 total cost of ownership</b> versus a comparable microservices+OpenSearch architecture, while preserving a clear migration path: if the course catalogue exceeds 500,000 searchable entities or daily search volume crosses 1 million queries, the SearchVector layer can be transparently replaced with OpenSearch without rewriting application code. The 20-week delivery timeline aligns directly with the RFP&rsquo;s five-phase structure (Discovery, Alpha, Beta, UAT, Deployment), with each phase producing demonstrable, testable artifacts that RIMIT staff can validate incrementally rather than a single &ldquo;big bang&rdquo; release at week 20."
    ))
    s.append(spacer(6))
    s.append(p(
        "The remainder of this document deconstructs the RFP, presents architectural visualizations, details the component selection rationale, walks through the database schema and API specifications, enumerates the UI screen inventory, specifies external integration designs, and concludes with a sprint-by-sprint delivery plan, cost estimate, risk register, test strategy, DevOps runbook, and an explicit architectural validation ledger certifying production readiness."
    ))
    s.append(PageBreak())
    return s


# ═══════════════════════════════════════════════════════════════════════
# Section 2: RFP Deconstruction & Functional Mapping
# ═══════════════════════════════════════════════════════════════════════
def section_rfp_deconstruction():
    s = []
    s.append(h1("2. RFP Deconstruction &amp; Functional Mapping"))
    s.append(p(
        "The RFP specifies four functional modules, a set of technical requirements (cloud-native deployment, enterprise search, secure document storage, MFA, RESTful APIs), a five-phase delivery timeline, and five evaluation criteria weighted toward technical approach (30%) and B2B portal execution (25%). This section deconstructs each functional module into concrete technical sub-systems and isolates the implicit Non-Functional Requirements (NFRs) that any winning proposal must address."
    ))

    s.append(h2("2.1 Functional Module &rarr; Sub-System Mapping"))
    s.append(p(
        "The table below maps each RFP functional module to its constituent Django applications, database tables, and primary user roles. This mapping serves as the master traceability matrix used throughout the document &mdash; every architectural decision in subsequent sections can be traced back to a row in this table."
    ))
    s.append(spacer(4))
    module_map = [
        ["RFP Module", "Django App", "Primary Tables", "User Roles"],
        ["Module 1: Aggregator Hub",
         "aggregator",
         "universities, courses, fee_structures, university_doc_vault",
         "Super Admin (write), All roles (read)"],
        ["Module 2: B2B Sub-Center Portal",
         "admissions + partners",
         "sub_centers, system_users, students, student_academic_histories, student_docs, enrollments",
         "Sub-Center Staff (write own), Counselor (read assigned)"],
        ["Module 3: Business Logic",
         "rules",
         "rules_configurations, intake_sessions, enrollments.status",
         "Super Admin (configure), System (enforce)"],
        ["Module 4: Marketing &amp; Comms",
         "integrations + notifications",
         "lead_ingestion_logs, notification_logs",
         "System (auto), Academic Head (monitor)"],
        ["Cross-Cutting: Finance",
         "finance",
         "payment_ledgers, fee_structures",
         "Finance Officer (read/write), Academic Head (read)"],
        ["Cross-Cutting: Audit",
         "audit",
         "audit_logs (partitioned)",
         "Super Admin (read all), System (write)"],
    ]
    s.append(make_table(module_map, col_weights=[1.4, 1.0, 2.2, 1.4], font_size=8.5))
    s.append(caption("Table 2.1 &mdash; RFP module to Django application mapping with primary tables and role boundaries."))

    s.append(h2("2.2 Non-Functional Requirement (NFR) Extraction"))
    s.append(p(
        "While the RFP states technical requirements at a high level (cloud-native, enterprise search, secure storage, MFA, RESTful APIs), a credible technical proposal must quantify the implicit NFRs that flow from the stated business context. RIMIT operates as National Coordinator for Kerala for Mangalayatan University and Regional Center Coordinator for BOSSE, with decentralized sub-centers across India. The NFRs below are derived from this operational context and from industry benchmarks for B2B educational platforms."
    ))
    s.append(spacer(4))
    nfr_table = [
        ["NFR Category", "Target", "Derived From", "Architectural Implication"],
        ["Throughput (peak)",
         "200 RPS sustained, 1000 RPS burst",
         "500 sub-centers &times; 4 staff &times; 1 req/sec",
         "PgBouncer connection pool, Gunicorn 8 workers &times; 2 containers"],
        ["Latency (p95 API)",
         "&lt; 500ms read, &lt; 800ms write",
         "Sub-center UX threshold",
         "GIN indexes on search vectors, N+1 query prevention via select_related"],
        ["Latency (search p95)",
         "&lt; 200ms multi-attribute filter",
         "Enterprise search requirement",
         "PostgreSQL tsvector + GIN (sufficient to 500K records)"],
        ["Availability",
         "99.9% (8.76h downtime/yr)",
         "B2B operational hours",
         "Multi-AZ RDS, ECS Fargate x2, ALB health checks"],
        ["RPO / RTO",
         "RPO 15 min, RTO 1 hour",
         "Educational records retention",
         "WAL archiving to S3, PITR, cross-region read replica"],
        ["Concurrent sessions",
         "2,000 authenticated users",
         "Peak admission season (Jul/Oct)",
         "Keycloak HA, JWT RS256, Redis session cache"],
        ["Document upload size",
         "10&ndash;100 MB per file",
         "High-res identity proofs, marklists",
         "TemporaryFileUploadHandler spool-to-disk, MinIO multipart"],
        ["Search index size",
         "&lt; 500K course rows",
         "All India university aggregator",
         "Postgres GIN; OpenSearch migration path documented"],
        ["Audit retention",
         "7 years",
         "Educational compliance norms",
         "audit_logs partitioned monthly by created_at"],
        ["MFA enforcement",
         "All B2B sub-center logins",
         "RFP Security Protocols section",
         "Keycloak OTP-over-WhatsApp/SMS, fallback to TOTP"],
    ]
    s.append(make_table(nfr_table, col_weights=[1.2, 1.4, 1.8, 2.0], font_size=8.5))
    s.append(caption("Table 2.2 &mdash; Quantified NFRs derived from RFP business context, with architectural implications."))

    s.append(h2("2.3 Regulatory &amp; Compliance Alignment"))
    s.append(p(
        "Although the RFP does not explicitly cite regulatory frameworks, operating an educational records platform in India triggers several implicit compliance obligations. The architecture aligns with the <b>Digital Personal Data Protection Act 2023 (DPDP)</b> by minimizing PII storage (Aadhar numbers stored as SHA-256 hashes via pgcrypto, never in plaintext), enforcing data-subject access requests via the audit_logs table, and supporting data-erasure workflows. <b>WCAG 2.1 AA</b> accessibility is mandated for all sub-center-facing screens. The audit_logs partitioned table provides the seven-year retention trail required by educational record-keeping norms, and the system&rsquo;s RBAC model maps cleanly onto <b>ISO 27001</b> access-control audit requirements should RIMIT pursue certification."
    ))
    s.append(PageBreak())
    return s


# ═══════════════════════════════════════════════════════════════════════
# Section 3: Architectural Visualizations
# ═══════════════════════════════════════════════════════════════════════
def section_arch_visualizations():
    s = []
    s.append(h1("3. Architectural Visualizations"))
    s.append(p(
        "This section presents four multi-layered architectural visualizations following the C4 model convention: a Level-1 System Context diagram showing human actors and external systems, a Level-2 Container Architecture diagram showing internal runtimes and data stores, a Cloud Infrastructure &amp; Deployment Topology showing the physical VPC/AZ layout, and a Critical System Transaction Sequence diagram tracing the most complex business workflow &mdash; student enrollment with session enforcement. All diagrams are rendered as Mermaid.js source and exported as 2&times; resolution PNGs for print quality."
    ))

    s.append(h2("3.1 C4 Level 1 &mdash; System Context Diagram"))
    s.append(p(
        "The system context shows the RIMIT-SPES platform at the center, surrounded by five human actor categories (Super Admin, Academic Heads, Counselors, Finance Officers, Sub-Center Staff) and six external systems (Meta Ads, WhatsApp Business API, SMTP/SES, Razorpay, MinIO/S3, Keycloak). All actor categories interact exclusively through the Django monolith; no actor has direct database or storage access. External integrations are unidirectional where possible (Meta pushes leads in; the platform pushes notifications out via WhatsApp/SMTP) to minimize attack surface."
    ))
    s.append(fit_image(f"{DIAG_DIR}/01_system_context.png"))
    s.append(caption("Figure 3.1 &mdash; C4 Level 1 System Context. Slate-blue nodes are internal system; terracotta nodes are external third-party systems; amber node is the identity provider."))

    s.append(h2("3.2 C4 Level 2 &mdash; Container Architecture Diagram"))
    s.append(p(
        "At the container level, the Django 5.x monolith is decomposed into four internal layers: DRF ViewSets (HTTP boundary, auto-documented via drf-spectacular), DRF Serializers (payload validation), the RLS Middleware (sets the PostgreSQL session variable <code>app.current_sub_center_id</code> on every request based on the JWT&rsquo;s tenant claim), and Django Signals (post_save triggers that enqueue Celery tasks). Celery workers consume from Redis and handle all outbound I/O &mdash; WhatsApp API calls, SMTP sends, S3 uploads, payment gateway interactions &mdash; keeping the request-response cycle fast. Keycloak issues RS256-signed JWTs that the Django app verifies on every request via the OIDC userinfo endpoint (cached in Redis for 60 seconds)."
    ))
    s.append(fit_image(f"{DIAG_DIR}/02_container_diagram.png"))
    s.append(caption("Figure 3.2 &mdash; C4 Level 2 Container Architecture. Single Django monolith with internal layers; Celery workers handle all async I/O."))

    s.append(h2("3.3 Cloud Infrastructure &amp; Deployment Topology"))
    s.append(p(
        "The production deployment targets a single AWS region (ap-south-1, Mumbai) for India data residency, with a two-AZ layout for high availability. Cloudflare provides edge DNS and DDoS protection in front of an Application Load Balancer. Nginx runs as a sidecar container on ECS Fargate handling SSL termination (TLS 1.3), rate limiting (limit_req zone=api:10r/s), and static file serving. Django app containers run with 2 vCPU / 4 GB each, autoscaled 2&ndash;6 based on ALB CPU &gt; 70%. Celery workers scale independently (2&ndash;8) based on Redis queue depth. RDS PostgreSQL 16 runs in Multi-AZ with a synchronous standby and an async cross-region read replica for disaster recovery. MinIO is deployed as a 3-node cluster striped across AZs with erasure coding."
    ))
    s.append(fit_image(f"{DIAG_DIR}/03_deployment_topology.png"))
    s.append(caption("Figure 3.3 &mdash; Cloud deployment topology. Mumbai region (ap-south-1), 2 AZs, isolated data subnet, cross-region S3 backup."))

    s.append(h2("3.4 Critical Transaction Sequence &mdash; Student Enrollment"))
    s.append(p(
        "The most complex and highest-value transaction in the system is the student enrollment workflow, which must atomically validate session-enforcement rules, write to the enrollments table under RLS, trigger a post_save signal, enqueue a Celery task that creates a Razorpay payment link and dispatches a WhatsApp notification, and finally update the enrollment status &mdash; all while returning a 201 response to the sub-center staff within 800ms p95. The sequence diagram below traces this flow end-to-end, including the failure branch where session enforcement rejects the enrollment and the success branch where the full async pipeline completes."
    ))
    s.append(fit_image(f"{DIAG_DIR}/04_enrollment_sequence.png", max_h=PAGE_H * 0.55))
    s.append(caption("Figure 3.4 &mdash; Enrollment sequence with Session Enforcement Matrix validation, RLS-protected DB write, and async notification/payment pipeline."))

    s.append(h2("3.5 Draw.io Visual Styling Specification"))
    s.append(p(
        "For RIMIT to import these diagrams into Draw.io for stakeholder presentations, the following visual styling specification is provided. The color palette maps directly to the cascade palette used in this document&rsquo;s body, ensuring visual consistency between the proposal and any client-facing derivative materials."
    ))
    s.append(spacer(4))
    style_table = [
        ["Node Category", "Fill Color", "Stroke Color", "Draw.io Shape"],
        ["Compute / Routing (Nginx, Django, Celery)", "#6c8ebf", "#4f73a5", "Rounded rectangle"],
        ["Data Stores (PostgreSQL, Redis, MinIO)", "#82b366", "#5a8f43", "Cylinder (database)"],
        ["Security / Identity (Keycloak)", "#d6b656", "#ae8c28", "Hexagon"],
        ["External Actors (Meta, WhatsApp, Razorpay)", "#b85450", "#943a37", "Rectangle (dashed border)"],
        ["Subgraph / Boundary Lines", "#f5f5f5", "#999999", "Dashed container"],
    ]
    s.append(make_table(style_table, col_weights=[2.2, 1.0, 1.0, 1.6], font_size=9))
    s.append(caption("Table 3.1 &mdash; Draw.io visual styling guide for converting Mermaid sources into board-ready presentation graphics."))
    s.append(PageBreak())
    return s


# ═══════════════════════════════════════════════════════════════════════
# Section 4: Component Specification & Technology Evaluation Matrix
# ═══════════════════════════════════════════════════════════════════════
def section_component_spec():
    s = []
    s.append(h1("4. Component Specification &amp; Technology Evaluation Matrix"))
    s.append(p(
        "Every critical technology choice in this architecture was evaluated against at least two industry-standard alternatives. The evaluation matrix below documents the selected technology, its specific architectural scope, the technical justification grounded in the RFP&rsquo;s NFRs, the alternatives considered, and the detailed rejection rationale. This transparent evaluation demonstrates technical rigor and provides RIMIT with a defensible audit trail should any choice be questioned during the proposal evaluation phase."
    ))
    s.append(spacer(4))

    # Component 1: Ingress
    s.append(h2("4.1 Ingress / Edge Routing"))
    eval_table = [
        ["Dimension", "Detail"],
        ["Selected Technology", "Nginx 1.26 (open-source, containerized)"],
        ["Architectural Scope",
         "Reverse proxy, TLS 1.3 termination, static file serving for Django admin assets, rate limiting (limit_req zone=api:10r/s, burst=20), security headers (HSTS, X-Frame-Options DENY, X-Content-Type-Options nosniff), request body size limit 100MB for document uploads."],
        ["Technical Justification",
         "RFP requires SSL/TLS in transit and continuous rate-limiting. Nginx is the industry-standard open-source reverse proxy with the lowest memory footprint (~10MB per worker), mature configuration syntax, and native support for upstream health checks. Removing the AWS WAF layer (per backend_architecture.md) requires Nginx to absorb basic DDoS mitigation duties, which it handles via limit_req and limit_conn directives."],
        ["Alternatives Considered",
         "<b>(1) Kong API Gateway</b> &mdash; plugin ecosystem, JWT verification at edge. <b>(2) AWS ALB</b> &mdash; managed, native integration with ECS."],
        ["Rejection Rationale",
         "Kong adds operational complexity (Postgres/Cassandra backing store, plugin upgrade matrix) for features DRF already handles natively (JWT verification, rate limiting via django-ratelimit). AWS ALB lacks request-body size limits above 60MB without custom Lambda, and locks RIMIT into AWS pricing &mdash; the minimalist stack explicitly preserves deployment portability."],
    ]
    s.append(make_table(eval_table, col_weights=[1.0, 3.0], font_size=9))
    s.append(spacer(8))

    # Component 2: Compute
    s.append(h2("4.2 Compute / Application Layer"))
    eval_table = [
        ["Dimension", "Detail"],
        ["Selected Technology", "Django 5.x + Django REST Framework 3.15 (monolithic)"],
        ["Architectural Scope",
         "Single deployable artifact serving all four RFP modules via internal app packages (aggregator, admissions, partners, rules, integrations, notifications, finance, audit). DRF ModelViewSet for CRUD, drf-spectacular for OpenAPI 3.1 schema auto-generation, django-filter for multi-attribute search, django-guardian for object-level permissions where RLS is insufficient."],
        ["Technical Justification",
         "Backend_Development_Guidelines.md explicitly mandates Django monolith with the rule: &lsquo;If Django or its ecosystem has a built-in feature, use it.&rsquo; DRF ModelViewSet eliminates boilerplate CRUD code; the Django Admin provides a free back-office CMS for Super Admins to manage university data without custom UI. A monolith of this size (~25 models, ~60 endpoints) is well below the complexity threshold where microservices yield net benefit."],
        ["Alternatives Considered",
         "<b>(1) FastAPI microservices</b> &mdash; async, type-safe, OpenAPI-native. <b>(2) Node.js + NestJS</b> &mdash; single language across stack."],
        ["Rejection Rationale",
         "FastAPI microservices would split 25 models across 4&ndash;6 services, requiring service discovery, distributed transactions (saga pattern), and inter-service auth &mdash; at least 6 weeks of additional infrastructure work for zero user-facing benefit at this scale. Node.js lacks Django Admin (RFP Module 1 explicitly requires admin CMS), and the Python ecosystem has superior libraries for the data-heavy work this platform requires (Celery, pandas for reporting, WeasyPrint for receipt PDFs)."],
    ]
    s.append(make_table(eval_table, col_weights=[1.0, 3.0], font_size=9))
    s.append(spacer(8))

    # Component 3: Database
    s.append(h2("4.3 Data Persistence (OLTP)"))
    eval_table = [
        ["Dimension", "Detail"],
        ["Selected Technology", "PostgreSQL 16 (AWS RDS Multi-AZ)"],
        ["Architectural Scope",
         "Primary OLTP store for all 17 tables across 5 schema modules. Provides three critical capabilities natively: (1) Row-Level Security (RLS) for sub-center tenant isolation, (2) tsvector + GIN index for full-text search replacing Elasticsearch, (3) JSONB columns for semi-structured data (student address_data, rules conditions, audit old_data/new_data). Listens for Celery Beat WAL archiving every 15 minutes."],
        ["Technical Justification",
         "dbschema.md defines 17 tables with explicit JSONB columns and partitioned audit tables &mdash; PostgreSQL is the only open-source database that satisfies all three requirements (RLS, JSONB, declarative partitioning) without external additions. GIN-indexed tsvector delivers sub-200ms search on 500K records, well above the projected course catalogue size of 50K&ndash;100K. The minimalist architecture explicitly removes Elasticsearch from the stack."],
        ["Alternatives Considered",
         "<b>(1) MySQL 8</b> &mdash; widespread, simpler ops. <b>(2) MongoDB</b> &mdash; document-native, JSONB-like."],
        ["Rejection Rationale",
         "MySQL lacks native RLS (requires application-layer views, defeating the security purpose), has weaker JSONB performance, and its full-text search (FULLTEXT index) does not support multi-weight ts_rank. MongoDB has no relational integrity (the schema has 9 foreign keys), no RLS equivalent, and would require mongoose-style application-level validation that the guidelines explicitly forbid in favor of DB-level enforcement."],
    ]
    s.append(make_table(eval_table, col_weights=[1.0, 3.0], font_size=9))
    s.append(spacer(8))

    # Component 4: Cache / Tasks
    s.append(h2("4.4 Caching &amp; Asynchronous Messaging"))
    eval_table = [
        ["Dimension", "Detail"],
        ["Selected Technology", "Celery 5.4 + Redis 7 (ElastiCache Multi-AZ)"],
        ["Architectural Scope",
         "Redis serves three roles: (1) Celery broker for ~15 task types (WhatsApp send, SMTP send, S3 upload, payment link creation, lead dedup, receipt PDF gen, broadcast fanout, etc.), (2) application cache for university/course catalogue (TTL 5 min) and Keycloak userinfo (TTL 60s), (3) rate-limit counter store for django-ratelimit. Celery Beat schedules nightly tasks (lead re-attribution, payment reconciliation, audit archival)."],
        ["Technical Justification",
         "Backend_Development_Guidelines.md mandates Celery+Redis as the only allowed async task stack. Redis&rsquo; sub-millisecond latency and native data structures (lists, sets, sorted sets) make it ideal for both queue and cache. Celery&rsquo;s retry-with-exponential-backoff and dead-letter queue patterns handle the WhatsApp API&rsquo;s 5% transient failure rate without manual intervention."],
        ["Alternatives Considered",
         "<b>(1) Dramatiq</b> &mdash; simpler API, no broker quirks. <b>(2) Django-RQ</b> &mdash; Redis-native, lightweight."],
        ["Rejection Rationale",
         "Dramatiq lacks Celery Beat (would require APScheduler sidecar) and has smaller middleware ecosystem. Django-RQ has weaker monitoring (no Flower equivalent) and no native task-chaining for the enrollment &rarr; payment &rarr; notification pipeline. Celery&rsquo;s apparent complexity is offset by deterministic behavior once configured with `task_acks_late=True` and `worker_prefetch_multiplier=1`."],
    ]
    s.append(make_table(eval_table, col_weights=[1.0, 3.0], font_size=9))
    s.append(spacer(8))

    # Component 5: Identity
    s.append(h2("4.5 Identity &amp; Access Management (IAM)"))
    eval_table = [
        ["Dimension", "Detail"],
        ["Selected Technology", "Keycloak 24 (self-hosted on ECS, DB-backed)"],
        ["Architectural Scope",
         "Centralized OIDC/OAuth2 identity provider for all 5 user roles. Issues RS256-signed JWTs (15-min access, 7-day refresh). Enforces MFA via OTP-over-WhatsApp (primary) and SMS (fallback) for sub-center logins. Hosts the RBAC role matrix mapping 4 roles (super_admin, academic_head, counselor, finance) to permission strings consumed by DRF&rsquo;s DjangoModelPermissions."],
        ["Technical Justification",
         "RFP requires MFA for B2B sub-center logins &mdash; Keycloak provides this out-of-the-box via Authentication Flows, no custom code. Self-hosting avoids per-user SaaS pricing (Auth0 charges $0.007/MAU; for 5000 sub-center users = $35/month, comparable to self-host compute but with vendor lock-in). DB-backed sessions (PostgreSQL schema) enable HA without sticky sessions."],
        ["Alternatives Considered",
         "<b>(1) Auth0</b> &mdash; managed, MFA-native. <b>(2) Django allauth</b> &mdash; native, simple."],
        ["Rejection Rationale",
         "Auth0 per-MAU pricing scales poorly for an educational platform targeting 5000+ sub-center users; vendor lock-in conflicts with the minimalist OSS mandate. Django allauth lacks native MFA, federated identity, and admin UI for user management &mdash; building these would violate the &lsquo;no custom auth&rsquo; rule in Backend_Development_Guidelines.md."],
    ]
    s.append(make_table(eval_table, col_weights=[1.0, 3.0], font_size=9))
    s.append(spacer(8))

    # Component 6: Storage
    s.append(h2("4.6 Object Storage / Document Vault"))
    eval_table = [
        ["Dimension", "Detail"],
        ["Selected Technology", "MinIO self-hosted (production), S3-compatible API"],
        ["Architectural Scope",
         "Stores all documents from university_doc_vault (prospectus PDFs, academic calendars, syllabi) and student_docs (identity proofs, marklists, migration certificates). All objects encrypted at rest (SSE-S3 equivalent via MinIO bucket encryption with AES-256). Presigned URLs valid for 15 minutes used for all downloads. Bucket versioning enabled for forensic recovery. Lifecycle rules tier objects &gt; 90 days old to S3 IA."],
        ["Technical Justification",
         "RFP requires secure cloud storage with encryption at rest optimized for high-volume PDFs. MinIO provides S3 API compatibility without AWS lock-in, runs as a 3-node cluster across AZs for HA, and costs ~INR 3000/month vs S3&rsquo;s INR 15000/month for 500GB storage &mdash; 80% cost reduction at this volume. S3-compatible API preserves a one-line migration path to AWS S3 if MinIO ops becomes burdensome."],
        ["Alternatives Considered",
         "<b>(1) AWS S3 (managed)</b> &mdash; zero ops, native IAM. <b>(2) Wasabi</b> &mdash; S3-compatible, no egress fees."],
        ["Rejection Rationale",
         "AWS S3 egress fees (INR 7/GB) become significant for high-frequency prospectus downloads &mdash; 1000 downloads/month of 5MB PDFs = INR 35K/year just in egress. Wasabi has a 90-day minimum storage duration that conflicts with the lifecycle tiering strategy and has no Mumbai region (latency from Singapore ~50ms). MinIO on ECS gives RIMIT full control over data residency, which is critical for DPDP Act compliance."],
    ]
    s.append(make_table(eval_table, col_weights=[1.0, 3.0], font_size=9))
    s.append(PageBreak())
    return s


# ═══════════════════════════════════════════════════════════════════════
# Re-export sections 5-16 from companion modules
# ═══════════════════════════════════════════════════════════════════════
from sections_part2 import (
    section_db_schema,
    section_api_specs,
    section_ui_inventory,
    section_integrations,
)
from sections_part3 import (
    section_security,
    section_sprint_plan,
    section_cost,
    section_risk,
    section_test_strategy,
    section_devops,
    section_assumptions,
    section_validation,
)
