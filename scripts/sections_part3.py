"""
Sections 9-16 of the RIMIT Development Plan.
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


# ═══════════════════════════════════════════════════════════════════════
# Section 9: Security, Governance & Compliance Posture
# ═══════════════════════════════════════════════════════════════════════
def section_security():
    s = []
    s.append(h1("9. Security, Governance &amp; Compliance Posture"))
    s.append(p(
        "Security is engineered into every layer of the stack rather than bolted on as an afterthought. The RFP mandates Multi-Factor Authentication for B2B sub-center logins, SSL/TLS encryption in transit, encrypted document storage, and continuous automated backups. This section details how each mandate is satisfied, plus the additional controls required for DPDP Act 2023 compliance and ISO 27001 alignment."
    ))

    s.append(h2("9.1 Identity Control &amp; Token Flow"))
    s.append(p(
        "Keycloak serves as the central identity provider, issuing OAuth2/OIDC tokens with RS256 signatures (asymmetric, 2048-bit RSA). The token lifecycle is: (1) user authenticates at Keycloak login page with username+password+MFA OTP, (2) Keycloak issues a 15-minute access token and 7-day refresh token (both JWTs), (3) Django verifies the access token signature using Keycloak&rsquo;s public key (cached in Redis, refreshed hourly via JWKS endpoint), (4) on token expiry, the Appsmith frontend calls Keycloak&rsquo;s token endpoint with the refresh token to obtain a new access token without re-prompting for MFA."
    ))
    s.append(p(
        "The four RFP-defined roles map to Keycloak realm roles and are embedded as a <code>roles</code> claim in the JWT. DRF&rsquo;s permission classes consume this claim via a custom <code>IsRole('super_admin')</code> decorator. MFA is enforced at the Keycloak Authentication Flow level &mdash; the &lsquo;browser&rsquo; flow for sub-center realm requires OTP-over-WhatsApp (primary) or SMS (fallback) after password authentication. Super Admin accounts additionally require a TOTP authenticator app (Google Authenticator) as a second factor, providing defense-in-depth against SIM-swap attacks."
    ))

    s.append(h2("9.2 Data Protection Vectors"))
    s.append(p(
        "<b>Data in Transit:</b> TLS 1.3 enforced end-to-end. Nginx terminates TLS from clients; Django-to-PostgreSQL connections use SSL with full certificate verification; Django-to-Redis uses TLS within the VPC; Celery-to-MinIO uses HTTPS. HSTS header (max-age=31536000, includeSubDomains, preload) sent on all responses."
    ))
    s.append(p(
        "<b>Data at Rest:</b> PostgreSQL encrypted via RDS encryption (AES-256, KMS-managed keys). MinIO bucket encryption enabled (SSE-S3 algorithm, AES-256). Redis encryption at rest via ElastiCache. S3 backup bucket encrypted with separate KMS key. Backups (WAL archives, pg_dump) inherit source encryption."
    ))
    s.append(p(
        "<b>PII Handling:</b> Aadhar numbers stored as SHA-256 hashes (never plaintext, never reversible). Phone numbers and email addresses stored in plaintext (required for notifications) but masked in audit log displays. Student documents accessible only via short-lived (15-min) presigned URLs, never directly via the database. The <code>students</code> table has a <code>data_subject_consent</code> JSONB column tracking consent timestamp and scope for DPDP Act compliance."
    ))

    s.append(h2("9.3 Compliance Alignment Matrix"))
    s.append(spacer(4))
    compliance_table = [
        ["Regulation / Standard", "Requirement", "Architectural Control", "Audit Evidence"],
        ["DPDP Act 2023 (India)",
         "Lawful processing, consent, data-subject rights, breach notification",
         "Consent tracking column, data-erasure workflow, audit_logs (7yr), breach runbook",
         "audit_logs partitions, consent JSONB"],
        ["WCAG 2.1 AA",
         "Web accessibility for users with disabilities",
         "ARIA labels, 4.5:1 contrast, keyboard nav, screen-reader tables",
         "Axe-core automated test reports"],
        ["ISO 27001 Annex A",
         "Access control, cryptography, operations security",
         "RBAC + RLS, KMS-managed keys, structlog audit trail",
         "ISO 27001 SoA (Statement of Applicability)"],
        ["PCI-DSS (payment data)",
         "Cardholder data not stored on our systems",
         "Razorpay hosts payment page; we store only transaction_ref (token)",
         "Webhook signature verification logs"],
        ["RFP Security Protocols",
         "MFA, SSL/TLS, encrypted storage, automated backups",
         "Keycloak MFA, TLS 1.3, RDS+MinIO encryption, WAL archiving",
         "Backup logs, TLS scan reports"],
    ]
    s.append(make_table(compliance_table, col_weights=[1.4, 1.6, 2.0, 1.4], font_size=8.5))
    s.append(caption("Table 9.1 &mdash; Compliance alignment matrix mapping regulations to architectural controls and audit evidence."))

    s.append(h2("9.4 Audit Trail &amp; Forensic Readiness"))
    s.append(p(
        "Every state-changing operation (INSERT/UPDATE/DELETE) on tenant-scoped tables triggers a database-level trigger that writes a before/after snapshot to <code>audit_logs</code>. The trigger captures user_id (from <code>current_setting('app.current_user_id')</code>), action_type, table_name, row_id, old_data (JSONB), new_data (JSONB), and timestamp. The audit_logs table is partitioned monthly, with partitions older than 7 years exported to S3 Glacier and dropped from the primary database &mdash; this keeps the audit table queryable for recent activity while preserving the full historical trail for compliance audits."
    ))
    s.append(PageBreak())
    return s


# ═══════════════════════════════════════════════════════════════════════
# Section 10: Sprint-by-Sprint Development Plan
# ═══════════════════════════════════════════════════════════════════════
def section_sprint_plan():
    s = []
    s.append(h1("10. Sprint-by-Sprint Development Plan"))
    s.append(p(
        "The 20-week delivery plan aligns directly with the RFP&rsquo;s five-phase structure (Discovery, Alpha, Beta, UAT, Deployment). Each phase has clear entry criteria, deliverables, owner roles, and exit criteria. Sprints are 2 weeks long, with sprint demos to RIMIT stakeholders at the end of each sprint. The plan assumes a 5-engineer team: 2 Backend, 1 Frontend/Appsmith, 1 DevOps, 1 QA, plus a part-time Project Manager and UI/UX designer during Discovery."
    ))

    s.append(h2("10.1 Phase 1 &mdash; Discovery (Weeks 1&ndash;3)"))
    s.append(p(
        "Discovery produces three locked artifacts: UI/UX wireframes for all 15 screens, the final database schema (this document&rsquo;s Section 5 with any RIMIT feedback incorporated), and the system architecture design (this document&rsquo;s Section 3). Stakeholder feedback is gated to two rounds per module per the ui_ux_guidlines.md revision cap. The Locked Blueprint is signed off via Azure DevOps at the end of Week 3."
    ))
    sprint_table = [
        ["Sprint", "Week", "Deliverable", "Owner", "Exit Criteria"],
        ["1.1", "1", "Kickoff, env setup (Docker Compose dev), CI/CD skeleton, Keycloak realm config", "DevOps + PM", "Dev env runs; CI green on hello-world test"],
        ["1.2", "2", "Wireframes for Module 1 (5 screens) + Module 2 (5 screens), Round 1 feedback", "UI/UX", "Wireframes uploaded to Azure DevOps; Round 1 comments logged"],
        ["1.3", "3", "Wireframes for Module 3 (3 screens) + Module 4 (2 screens), Round 2 feedback, Locked Blueprint sign-off", "UI/UX + PM", "Locked Blueprint PDF signed by Abdul Bari; CR process documented"],
    ]
    s.append(make_table(sprint_table, col_weights=[0.4, 0.4, 3.0, 1.2, 2.0], font_size=8.5))
    s.append(caption("Table 10.1 &mdash; Discovery phase sprints."))

    s.append(h2("10.2 Phase 2 &mdash; Alpha: Aggregator Hub (Weeks 4&ndash;9)"))
    s.append(p(
        "Alpha delivers the Centralized University Aggregator Hub &mdash; the database goes live, the Admin CMS becomes operational, and Super Admins can manage university content. The Django Admin is the primary CMS for this phase, with Appsmith screens for read-only directory views. Search is implemented with PostgreSQL tsvector + GIN, validated against a 10K-record seed dataset for sub-200ms p95 latency."
    ))
    sprint_table = [
        ["Sprint", "Week", "Deliverable", "Owner", "Exit Criteria"],
        ["2.1", "4-5", "DB migrations for Module 1 (4 tables); DRF ViewSets for universities + courses + fees; django-admin registered", "Backend", "All 9 Module 1 endpoints pass integration tests"],
        ["2.2", "6-7", "Search implementation (tsvector + GIN); Appsmith University Directory + Profile + Search screens; prospectus upload to MinIO", "Backend + Frontend", "Search p95 &lt; 200ms on 10K seed; Appsmith screens demo-ready"],
        ["2.3", "8-9", "Digital Prospectus Library screen; Admin CMS screens (Appsmith); Keycloak RBAC configured for super_admin role; staging deployment", "Frontend + DevOps", "Staging URL accessible; super_admin can CRUD universities end-to-end"],
    ]
    s.append(make_table(sprint_table, col_weights=[0.4, 0.5, 3.0, 1.2, 2.0], font_size=8.5))
    s.append(caption("Table 10.2 &mdash; Alpha phase sprints."))

    s.append(h2("10.3 Phase 3 &mdash; Beta: B2B Sub-Center Portal (Weeks 10&ndash;15)"))
    s.append(p(
        "Beta is the most complex phase &mdash; it delivers the B2B sub-center portal with student registration, document upload vault, real-time enrollment tracking, and the Session Enforcement Matrix rules engine. RLS policies are implemented and tested with cross-tenant integration tests. MFA is enforced for sub-center logins. Two pilot sub-centers are onboarded at Week 14 for early feedback before full UAT."
    ))
    sprint_table = [
        ["Sprint", "Week", "Deliverable", "Owner", "Exit Criteria"],
        ["3.1", "10-11", "DB migrations for Module 2 + 3 (10 tables); RLS policies + tests; DRF ViewSets for students, academic_histories, docs, enrollments, intake_sessions", "Backend", "Cross-tenant RLS tests pass; 10 endpoints functional"],
        ["3.2", "12-13", "Multi-step Student Registration Form (Appsmith); Document Upload Vault (drag-drop + progress); enrollment tracking table", "Frontend", "Counselor can register student end-to-end in &lt; 3 min"],
        ["3.3", "14-15", "Session Enforcement Matrix rules engine; rules_configurations CRUD; /rules/validate/ endpoint; 2 pilot sub-centers onboarded", "Backend + PM", "Pilot sub-centers complete 5 enrollments each; rules block invalid sessions correctly"],
    ]
    s.append(make_table(sprint_table, col_weights=[0.4, 0.5, 3.0, 1.2, 2.0], font_size=8.5))
    s.append(caption("Table 10.3 &mdash; Beta phase sprints."))

    s.append(h2("10.4 Phase 4 &mdash; Testing &amp; UAT (Weeks 16&ndash;18)"))
    s.append(p(
        "UAT executes the full test pyramid: unit (pytest-django, 80% coverage), integration (DRF API tests), load (Locust simulating 10x baseline), security (OWASP ZAP, RLS audit), and user acceptance (RIMIT staff in 3 role groups). All P0/P1 bugs are fixed before Phase 5. The Meta Lead Ads and WhatsApp integrations are tested against sandbox accounts; Razorpay is tested against the test environment."
    ))
    sprint_table = [
        ["Sprint", "Week", "Deliverable", "Owner", "Exit Criteria"],
        ["4.1", "16", "Load testing (Locust 10x = 1000 concurrent); security scan (OWASP ZAP + RLS audit); bug triage", "QA + DevOps", "p95 &lt; 500ms at 1000 concurrent; 0 critical CVEs; 0 RLS bypass findings"],
        ["4.2", "17", "Meta Lead Ads integration (sandbox); WhatsApp Business API integration (test number); Razorpay integration (test mode); SMTP via SES", "Backend + DevOps", "All 4 integrations pass end-to-end test scenarios"],
        ["4.3", "18", "RIMIT UAT: Super Admin group (2 days), Counselor group (2 days), Finance group (2 days); bug fixes; UAT sign-off", "PM + RIMIT staff", "UAT sign-off document signed by Abdul Bari; all P0/P1 bugs fixed"],
    ]
    s.append(make_table(sprint_table, col_weights=[0.4, 0.4, 3.0, 1.2, 2.0], font_size=8.5))
    s.append(caption("Table 10.4 &mdash; Testing &amp; UAT phase sprints."))

    s.append(h2("10.5 Phase 5 &mdash; Deployment &amp; Training (Weeks 19&ndash;20)"))
    s.append(p(
        "Production deployment uses a blue-green strategy via ALB target group swap, with a 1-hour rollback window. Data migration from any existing RIMIT spreadsheets is scripted via a one-time Django management command. Sub-center training workshops are conducted in two batches (Kochi hub + Malappuram hub) covering registration, document upload, enrollment tracking, and reporting."
    ))
    sprint_table = [
        ["Sprint", "Week", "Deliverable", "Owner", "Exit Criteria"],
        ["5.1", "19", "Production deployment (blue-green); data migration script run; smoke tests; 1-hour rollback drill", "DevOps", "Production URL live; smoke tests pass; rollback drill &lt; 60 min"],
        ["5.2", "20", "Sub-center training workshops (Kochi + Malappuram); user documentation handover; 30-day hypercare SLA activation", "PM + RIMIT staff", "100% sub-centers trained; documentation delivered; hypercare channel active"],
    ]
    s.append(make_table(sprint_table, col_weights=[0.4, 0.4, 3.0, 1.2, 2.0], font_size=8.5))
    s.append(caption("Table 10.5 &mdash; Deployment &amp; training phase sprints."))
    s.append(PageBreak())
    return s


# ═══════════════════════════════════════════════════════════════════════
# Section 11: Cost & Effort Estimation
# ═══════════════════════════════════════════════════════════════════════
def section_cost():
    s = []
    s.append(h1("11. Cost &amp; Effort Estimation"))
    s.append(p(
        "This section provides an itemized cost breakdown covering all five RFP-mandated commercial categories: UI/UX phase, development cycles, cloud setup, API integration expenses, and annual maintenance contract (AMC). All figures are in Indian Rupees (INR) with USD equivalents at an exchange rate of INR 83/USD. Effort estimates assume a 5-engineer team working at standard productivity (40 productive hours/week)."
    ))

    s.append(h2("11.1 Effort Estimate by Role (Person-Months)"))
    effort_table = [
        ["Role", "Discovery (3wk)", "Alpha (6wk)", "Beta (6wk)", "UAT (3wk)", "Deploy (2wk)", "Total PM"],
        ["Backend Engineer x2", "0.4", "3.0", "3.0", "1.5", "0.5", "8.4"],
        ["Frontend/Appsmith", "0.4", "1.5", "3.0", "0.75", "0.25", "5.9"],
        ["DevOps Engineer", "0.4", "1.0", "1.0", "0.75", "1.0", "4.15"],
        ["QA Engineer", "0.2", "0.5", "1.0", "1.5", "0.25", "3.45"],
        ["Project Manager", "0.45", "0.9", "0.9", "0.45", "0.3", "3.0"],
        ["UI/UX Designer", "0.9", "0.0", "0.0", "0.0", "0.0", "0.9"],
        ["Total", "2.75", "6.9", "8.9", "4.95", "2.3", "25.8 PM"],
    ]
    s.append(make_table(effort_table, col_weights=[1.6, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0], font_size=8.5))
    s.append(caption("Table 11.1 &mdash; Effort by role and phase. Total: ~26 person-months over 20 calendar weeks."))

    s.append(h2("11.2 Itemized Cost Breakdown &mdash; Year 1"))
    cost_table = [
        ["Cost Category", "Description", "INR", "USD (approx)"],
        ["UI/UX Phase", "3 weeks Discovery: wireframes, design system, Locked Blueprint", "4,00,000", "$4,800"],
        ["Development Cycles", "17 weeks engineering (Alpha+Beta+UAT+Deploy), 5-engineer team", "28,00,000", "$33,700"],
        ["Cloud Setup", "AWS account setup, IaC (Terraform), CI/CD pipelines, Keycloak config", "3,00,000", "$3,600"],
        ["API Integrations", "Meta Lead Ads setup, WhatsApp Business API approval, Razorpay integration, SES domain verification", "5,00,000", "$6,000"],
        ["Training Workshops", "2 workshops (Kochi + Malappuram), materials, travel", "1,50,000", "$1,800"],
        ["Subtotal (Year 1 Build)", "", "41,50,000", "$49,900"],
        ["AMC (18% of build, Year 1)", "Annual maintenance: bug fixes, minor enhancements, cloud ops, 8x5 SLA", "7,47,000", "$9,000"],
        ["Total Year 1", "", "48,97,000", "~$59,000"],
    ]
    s.append(make_table(cost_table, col_weights=[1.6, 3.0, 1.2, 1.0], font_size=8.5))
    s.append(caption("Table 11.2 &mdash; Itemized Year-1 cost. AMC covers Year 1 post-launch; subsequent years are 18% of build cost."))

    s.append(h2("11.3 Recurring Cloud Run-Cost (Monthly)"))
    cloud_table = [
        ["AWS Resource", "Specification", "Monthly INR", "Notes"],
        ["ECS Fargate (App)", "2 x 2vCPU/4GB", "12,000", "Autoscale to 6"],
        ["ECS Fargate (Celery)", "2 x 1vCPU/2GB", "6,000", "Autoscale to 8"],
        ["RDS PostgreSQL 16", "db.t3.medium Multi-AZ", "14,000", "2 vCPU, 4GB RAM"],
        ["ElastiCache Redis", "cache.t3.small Multi-AZ", "4,500", "1.37 GB"],
        ["MinIO on ECS", "3 x 1vCPU/2GB + 200GB EBS", "9,000", "Erasure-coded"],
        ["ALB + Data Transfer", "ALB + 200GB egress", "3,500", "Mostly inbound"],
        ["Cloudflare + Route53", "DNS + CDN", "1,500", "Pro plan"],
        ["SES + S3 Backup", "Email + WAL archive bucket", "1,500", "Variable"],
        ["Total Monthly", "", "51,000", "~$615/month"],
    ]
    s.append(make_table(cloud_table, col_weights=[1.8, 2.2, 1.2, 1.8], font_size=8.5))
    s.append(caption("Table 11.3 &mdash; Recurring monthly cloud run-cost (single-region, Mumbai). Scales ~linearly with traffic."))

    s.append(h2("11.4 Cost Competitiveness &amp; Scalability Value"))
    s.append(p(
        "The minimalist stack delivers significant cost advantages over a comparable microservices+OpenSearch architecture: (1) no OpenSearch cluster (~INR 20K/month saved), (2) no AWS WAF (~INR 5K/month saved), (3) no EventBridge/Kinesis (~INR 3K/month saved), (4) no Kong API Gateway (~INR 8K/month saved). Total monthly savings: ~INR 36K, or ~INR 4.3L/year &mdash; recouping the AMC cost. The architecture scales horizontally by adding ECS Fargate containers (sub-minute autoscale), and the database scales via RDS read replicas (sub-minute promotion). The documented migration path to OpenSearch (if course catalogue exceeds 500K) and to AWS managed services (if ops becomes burdensome) preserves long-term flexibility without forcing premature optimization."
    ))
    s.append(PageBreak())
    return s


# ═══════════════════════════════════════════════════════════════════════
# Section 12: Risk Register & Mitigation Matrix
# ═══════════════════════════════════════════════════════════════════════
def section_risk():
    s = []
    s.append(h1("12. Risk Register &amp; Mitigation Matrix"))
    s.append(p(
        "The risk register below identifies the 10 most significant risks to project success, scored by probability (Low/Medium/High) and impact (Low/Medium/High). Each risk has a designated owner and a concrete mitigation strategy. The register is reviewed at the end of every sprint during the sprint retrospective, and new risks discovered during execution are added with appropriate mitigations."
    ))
    s.append(spacer(4))
    risk_table = [
        ["ID", "Risk", "Prob", "Impact", "Mitigation", "Owner"],
        ["R1", "PostgreSQL search perf degrades &gt; 500K courses (tsvector/GIN limits)",
         "L", "M",
         "Documented OpenSearch migration path; quarterly benchmark on production data; GIN index maintenance (REINDEX) scheduled weekly",
         "Backend Lead"],
        ["R2", "RLS misconfiguration causes cross-tenant data leak",
         "L", "H",
         "Integration tests asserting isolation per endpoint (2 tenants &times; all endpoints); pre-deploy RLS audit SQL script; Super Admin BYPASSRLS only via explicit role grant",
         "Backend Lead"],
        ["R3", "Meta webhook payload schema drift (Meta changes lead format)",
         "M", "M",
         "Defensive parsing (only required fields, ignore extras); version pinning on Graph API v18.0; weekly lead_ingestion_logs error rate dashboard with alert at &gt; 5%",
         "Backend Lead"],
        ["R4", "WhatsApp API rate limits during broadcast campaigns",
         "M", "M",
         "Celery task rate_limit=&lsquo;75/s&rsquo;; daily quota check in broadcast UI; pre-approved template library; tier upgrade request submitted to Meta at 10K/day threshold",
         "Backend Lead"],
        ["R5", "Keycloak single point of failure (auth outage = total platform outage)",
         "L", "H",
         "Keycloak HA mode with 2+ instances; DB-backed sessions (PostgreSQL, Multi-AZ); JWT validation cache in Redis (60s TTL) survives 60s Keycloak outage; fallback TOTP for super_admin",
         "DevOps"],
        ["R6", "Document upload timeouts on slow sub-center connections (rural India, 2G/3G)",
         "M", "M",
         "S3 multipart upload via presigned URLs (resumable); client-side chunking (5MB chunks); upload progress UI with retry; 30-min timeout per chunk",
         "Frontend Lead"],
        ["R7", "Payment gateway downtime (Razorpay outage during fee window)",
         "L", "H",
         "Dual-gateway failover (Razorpay primary, PayU fallback); automatic failover on 3 consecutive 5xx; payment_link expiry 24h so students can retry later",
         "Backend Lead"],
        ["R8", "Scope creep post-Locked Blueprint (RIMIT requests new features mid-Beta)",
         "H", "M",
         "Formal Change Request (CR) process; CR review board (PM + Tech Lead + RIMIT MD); CR cost &amp; timeline impact documented before approval; backlog grooming bi-weekly",
         "PM"],
        ["R9", "Sub-center adoption resistance (staff prefer paper-based or WhatsApp workflows)",
         "M", "M",
         "Training workshops with hands-on practice; mobile-first UI optimized for tablet; 30-day hypercare with dedicated WhatsApp support; phased rollout (5 pilot centers first)",
         "PM + RIMIT"],
        ["R10", "Data loss (DB corruption, accidental deletion, ransomware)",
         "L", "H",
         "RPO 15 min via WAL archiving to S3; RTO 1 hour via PITR (Point-in-Time Recovery); nightly full pg_dump to cross-region S3; quarterly DR drill with restore verification",
         "DevOps"],
    ]
    s.append(make_table(risk_table, col_weights=[0.3, 2.0, 0.4, 0.4, 2.8, 0.8], font_size=8.0))
    s.append(caption("Table 12.1 &mdash; Top 10 risks with probability, impact, mitigation, and owner. Reviewed every sprint."))
    s.append(PageBreak())
    return s


# ═══════════════════════════════════════════════════════════════════════
# Section 13: Test & UAT Strategy
# ═══════════════════════════════════════════════════════════════════════
def section_test_strategy():
    s = []
    s.append(h1("13. Test &amp; UAT Strategy"))
    s.append(p(
        "The test strategy follows the standard pyramid: a broad base of fast unit tests, a narrower middle of integration tests, and a small apex of end-to-end / UAT tests. The RFP&rsquo;s Phase 4 (Testing &amp; UAT) explicitly requires &lsquo;rigorous stress testing, role-permission verification, and end-to-end workflow evaluation by RIMIT staff.&rsquo; This section details each test layer, the CI/CD pipeline integration, and the UAT acceptance criteria."
    ))

    s.append(h2("13.1 Test Pyramid"))
    pyramid_table = [
        ["Layer", "Tooling", "Coverage Target", "Examples"],
        ["Unit", "pytest-django, factory_boy", "80% line coverage on business logic",
         "Session Enforcement Matrix rule evaluation; fee calculation; RLS policy SQL; serializer validation"],
        ["Integration", "pytest-django + requests, DRF APITestCase", "All endpoints (60+) covered",
         "POST /students/ creates student + academic_history; RLS test: tenant A cannot read tenant B&rsquo;s student; webhook signature verification"],
        ["Load", "Locust, distributed workers", "10x baseline = 1000 concurrent users",
         "Sub-center staff concurrent login burst; search query flood; document upload during peak enrollment"],
        ["Security", "OWASP ZAP, bandit, pip-audit, custom RLS audit script", "0 critical CVEs, 0 RLS bypass",
         "SQL injection on search params; JWT tampering; IDOR on student endpoints; RLS policy enumeration via SQL introspection"],
        ["UAT", "Manual, RIMIT staff in 3 role groups", "All acceptance criteria from RFP Module specs",
         "Super Admin: university CRUD, rules config, RBAC. Counselor: student registration, doc upload, enrollment. Finance: payment ledger, receipt gen"],
    ]
    s.append(make_table(pyramid_table, col_weights=[0.8, 1.8, 1.6, 2.4], font_size=8.5))
    s.append(caption("Table 13.1 &mdash; Five-layer test pyramid with tooling and coverage targets."))

    s.append(h2("13.2 CI/CD Pipeline"))
    s.append(p(
        "The CI/CD pipeline runs on GitHub Actions and is triggered on every push to <code>main</code> and on pull requests. The pipeline has 6 stages: (1) Lint (flake8, black --check, isort --check), (2) Unit tests (pytest, coverage report), (3) Integration tests (pytest-django with test PostgreSQL + Redis), (4) Security scan (bandit, pip-audit, OWASP ZAP baseline), (5) Build (Docker image build + push to ECR), (6) Deploy to staging (ECS Fargate rolling deploy). Production deploys are gated behind a manual approval from the PM after smoke tests pass on staging."
    ))
    s.append(spacer(4))
    s.append(code(
        "# .github/workflows/ci.yml (excerpt)\n"
        "jobs:\n"
        "  test:\n"
        "    runs-on: ubuntu-latest\n"
        "    services:\n"
        "      postgres: { image: postgres:16, env: { POSTGRES_PASSWORD: test } }\n"
        "      redis: { image: redis:7 }\n"
        "    steps:\n"
        "      - uses: actions/checkout@v4\n"
        "      - uses: actions/setup-python@v5\n"
        "        with: { python-version: '3.12' }\n"
        "      - run: pip install -r requirements.txt\n"
        "      - run: black --check . && flake8 . && isort --check .\n"
        "      - run: pytest --cov=. --cov-report=xml --cov-fail-under=80\n"
        "      - run: bandit -r . -ll\n"
        "      - run: pip-audit\n"
        "  build-deploy:\n"
        "    needs: test\n"
        "    if: github.ref == 'refs/heads/main'\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - uses: aws-actions/configure-aws-credentials@v4\n"
        "      - run: docker build -t rimit-app .\n"
        "      - run: aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_URI\n"
        "      - run: docker push $ECR_URI/rimit-app:latest\n"
        "      - run: aws ecs update-service --cluster rimit-prod --service rimit-app --force-new-deployment"
    ))

    s.append(h2("13.3 UAT Acceptance Criteria"))
    s.append(p(
        "UAT is conducted by RIMIT staff organized into three role-based groups, each spending 2 days executing scripted test scenarios derived from the RFP module specifications. A scenario passes only if the user can complete the workflow end-to-end without encountering any P0 or P1 bug. P2 bugs (cosmetic, minor UX friction) are logged but do not block sign-off. UAT sign-off is required from Abdul Bari (MD) before production deployment in Week 19."
    ))
    s.append(spacer(4))
    uat_table = [
        ["Role Group", "Testers", "Day 1 Scenarios", "Day 2 Scenarios", "Pass Threshold"],
        ["Super Admin", "Abdul Bari + 1 RIMIT manager",
         "University CRUD; course+fee management; prospectus upload; rules config; RBAC matrix edit",
         "Cross-tenant visibility check; audit log query; broadcast notification; financial dashboard",
         "100% scenarios pass, 0 P0/P1 bugs"],
        ["Counselor / Sub-Center", "3 sub-center staff from pilot",
         "Login + MFA; student registration (3 students); document upload (5 docs); enrollment creation with session check",
         "Enrollment status tracking; document re-upload on rejection; partner dashboard KPI verification",
         "100% scenarios pass, 0 P0/P1 bugs"],
        ["Finance Officer", "1 RIMIT finance staff",
         "Payment ledger view; receipt PDF generation; fee reconciliation report; status transition Fee Paid&rarr;Enrolled",
         "Daily collection report; sub-center-wise revenue; failed payment retry; refund workflow",
         "100% scenarios pass, 0 P0/P1 bugs"],
    ]
    s.append(make_table(uat_table, col_weights=[1.4, 1.2, 2.2, 2.2, 1.4], font_size=8.0))
    s.append(caption("Table 13.2 &mdash; UAT scenario matrix by role group. 2 days per group, 6 UAT days total."))
    s.append(PageBreak())
    return s


# ═══════════════════════════════════════════════════════════════════════
# Section 14: Deployment & DevOps Strategy
# ═══════════════════════════════════════════════════════════════════════
def section_devops():
    s = []
    s.append(h1("14. Deployment &amp; DevOps Strategy"))
    s.append(p(
        "The deployment strategy emphasizes environment parity, automated rollback, and comprehensive observability. Docker Compose provides local development parity with production; the same Docker image runs in dev, staging, and production with only environment variables differing. Infrastructure-as-Code (Terraform) provisions all AWS resources, enabling one-command environment rebuild. Observability is built on three pillars: structured logs (structlog &rarr; Loki &rarr; Grafana), metrics (django-prometheus &rarr; Prometheus &rarr; Grafana), and error tracking (Sentry)."
    ))

    s.append(h2("14.1 Environment Parity"))
    env_table = [
        ["Environment", "Purpose", "Stack", "Data"],
        ["Local (dev)", "Engineer laptop", "Docker Compose (5 services)", "Synthetic seed (100 rows/table)"],
        ["CI", "Automated tests", "GitHub Actions services (Postgres+Redis)", "Factory-generated fixtures"],
        ["Staging", "Pre-prod validation, UAT", "ECS Fargate + RDS (db.t3.small)", "Anonymized prod snapshot (weekly)"],
        ["Production", "Live system", "ECS Fargate + RDS Multi-AZ (db.t3.medium)", "Real data, encrypted backups"],
    ]
    s.append(make_table(env_table, col_weights=[1.2, 1.6, 2.2, 2.0], font_size=8.5))
    s.append(caption("Table 14.1 &mdash; Four environments with parity. Same Docker image runs in all environments."))

    s.append(h2("14.2 Docker Compose (Development)"))
    s.append(code(
        "# docker-compose.yml (excerpt - 5 dev services)\n"
        "services:\n"
        "  app:\n"
        "    build: .\n"
        "    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4\n"
        "    volumes: [./app:/app]\n"
        "    env_file: .env\n"
        "    depends_on: [db, redis, keycloak]\n"
        "    ports: ['8000:8000']\n"
        "  celery:\n"
        "    build: .\n"
        "    command: celery -A config worker -l info --concurrency=4\n"
        "    env_file: .env\n"
        "    depends_on: [redis, db]\n"
        "  celerybeat:\n"
        "    build: .\n"
        "    command: celery -A config beat -l info\n"
        "    env_file: .env\n"
        "  db:\n"
        "    image: postgres:16\n"
        "    environment: { POSTGRES_DB: rimit, POSTGRES_PASSWORD: dev }\n"
        "    volumes: [pgdata:/var/lib/postgresql/data]\n"
        "  redis:\n"
        "    image: redis:7\n"
        "  keycloak:\n"
        "    image: quay.io/keycloak/keycloak:24.0\n"
        "    environment: { KEYCLOAK_ADMIN: admin, KEYCLOAK_ADMIN_PASSWORD: admin }\n"
        "    command: start-dev\n"
        "volumes: { pgdata: {} }"
    ))

    s.append(h2("14.3 Observability Stack"))
    s.append(p(
        "<b>Logging:</b> All application logs are emitted in JSON via structlog, including request_id (UUID per request, propagated via Celery task headers), user_id, sub_center_id, and latency_ms. Logs ship to Loki via Promtail, queryable in Grafana with LogQL. Sensitive fields (Aadhar, phone) are scrubbed via structlog processors."
    ))
    s.append(p(
        "<b>Metrics:</b> django-prometheus exposes a <code>/metrics</code> endpoint scraped by Prometheus every 15 seconds. Tracked metrics include: HTTP request count/latency by endpoint, DB query count/latency, Celery task count/latency/failure rate, RLS policy hit count, cache hit ratio. Grafana dashboards display these metrics with alerts at: p95 latency &gt; 500ms, error rate &gt; 1%, Celery queue depth &gt; 100, DB connection pool &gt; 80%."
    ))
    s.append(p(
        "<b>Error Tracking:</b> Sentry captures unhandled exceptions with full stack trace, request context, and user context. Alerts route to a dedicated Slack channel (#rimit-alerts) via PagerDuty for P0 issues (production down, RLS bypass attempt). Sentry release tracking correlates deploys with error spikes, enabling fast rollback decisions."
    ))

    s.append(h2("14.4 Backup &amp; Disaster Recovery"))
    s.append(p(
        "<b>Backup Strategy:</b> RDS automated backups with 15-minute WAL archiving to a cross-region S3 bucket (ap-south-1 &rarr; ap-south-2). Nightly full pg_dump (encrypted) to the same S3 bucket with 30-day retention. MinIO bucket versioning enabled (indefinite retention for deleted/overwritten docs, with lifecycle rule tiering to S3 IA after 90 days). Keycloak realm export (JSON) nightly to S3."
    ))
    s.append(p(
        "<b>Disaster Recovery:</b> RPO = 15 minutes (worst-case data loss from WAL archive interval). RTO = 1 hour (Point-in-Time Recovery from RDS snapshot + MinIO restoration from cross-region replica). A quarterly DR drill restores the full stack to a separate AWS account and runs the smoke test suite, verifying the RTO/RPO targets. The DR runbook (15-step checklist) is version-controlled in the repo and tested by a junior engineer (not the DR author) to surface hidden assumptions."
    ))

    s.append(h2("14.5 Deployment Runbook"))
    s.append(p(
        "Production deploys follow a blue-green pattern via ALB target group swap. The pre-deploy checklist: (1) CI green on main, (2) smoke tests pass on staging, (3) database migrations reviewed (especially ALTER TABLE on large tables), (4) rollback plan documented. The deploy itself: (1) push new task definition to ECS, (2) ECS performs rolling deploy (1 container at a time, health check 60s), (3) post-deploy smoke tests on production, (4) monitor Sentry + Grafana for 30 minutes. Rollback: revert the task definition to the previous revision (1 command, &lt; 5 minutes). Database migrations are forward-compatible (additive only); backward-incompatible migrations require a 2-phase deploy (Phase 1: deploy code that reads both old+new schema; Phase 2: deploy migration + code that uses new schema only)."
    ))
    s.append(PageBreak())
    return s


# ═══════════════════════════════════════════════════════════════════════
# Section 15: Assumptions, Guardrails & Architecture RFIs
# ═══════════════════════════════════════════════════════════════════════
def section_assumptions():
    s = []
    s.append(h1("15. Assumptions, Guardrails &amp; Architecture RFIs"))
    s.append(p(
        "Every architectural proposal rests on assumptions that, if invalid, would require rework. This section makes all assumptions explicit, documents the hard constraints imposed by the RIMIT guidelines, and lists the strategic Requests for Information (RFIs) that RIMIT should answer before development starts. Each assumption is tagged with an ID for traceability in subsequent CR discussions."
    ))

    s.append(h2("15.1 Explicit Assumptions (A-001 to A-008)"))
    assumptions_table = [
        ["ID", "Assumption", "Impact if Invalid"],
        ["A-001", "RIMIT has or will provision a Meta Developer account with Lead Gen API access before Phase 4 (Week 17)", "WhatsApp + Meta Lead Ads integration delayed; Week 17 sprint slips by 2-3 weeks"],
        ["A-002", "RIMIT has or will register a WhatsApp Business Account and submit message templates for Meta approval (24-48h lead time) before Phase 4",
         "WhatsApp notifications unavailable; SMTP fallback used; broadcast campaigns delayed"],
        ["A-003", "Total sub-center count is &lt; 500 with peak concurrent users &lt; 2000",
         "Single-region RDS + ECS sufficient; if higher, need Multi-AZ read replicas + ECS autoscale ceiling raised"],
        ["A-004", "Existing student data (if any) is in spreadsheet format (CSV/XLSX) and &lt; 100K records",
         "One-time Django management command handles import; if &gt; 100K, need staged import + dedup reconciliation"],
        ["A-005", "RIMIT staff have basic computer literacy (browser, email) &mdash; training workshops cover platform-specific workflows only",
         "Training extends from 2 days to 4-5 days per batch; 20-week timeline impacted"],
        ["A-006", "AWS Mumbai region (ap-south-1) satisfies India data residency requirements under DPDP Act 2023",
         "If not, need to evaluate alternative Indian cloud regions or on-prem deployment; cost + timeline impact"],
        ["A-007", "Razorpay will approve the RIMIT merchant account within 5 business days of application",
         "Payment integration testing uses Razorpay test mode; production go-live may slip by 3-5 days"],
        ["A-008", "All sub-center staff have WhatsApp installed on their primary mobile number (for MFA OTP delivery)",
         "If not, fall back to SMS-based OTP (INR 0.20/OTP, adds ~INR 5K/month at 25K logins)"],
    ]
    s.append(make_table(assumptions_table, col_weights=[0.5, 3.5, 2.5], font_size=8.5))
    s.append(caption("Table 15.1 &mdash; Eight explicit assumptions. Each has a clear impact statement if invalidated."))

    s.append(h2("15.2 Hard Constraints (C-001 to C-005)"))
    constraints_table = [
        ["ID", "Constraint", "Source"],
        ["C-001", "Minimalist stack: no Elasticsearch/OpenSearch, no AWS WAF, no EventBridge &mdash; PostgreSQL + Nginx handle these concerns natively",
         "backend_architecture.md, Backend_Development_Guidelines.md"],
        ["C-002", "UI revision cap: maximum 2 iterative rounds per module during Discovery; Locked Blueprint enforced via Azure DevOps sign-off",
         "ui_ux_guidlines.md Section 3"],
        ["C-003", "Appsmith Community Edition only for all internal admin screens; no React/Vue/Angular custom code",
         "ui_development_guid.md Section 2 Rule 1"],
        ["C-004", "PostgreSQL is the only database; Row-Level Security is the only acceptable multi-tenancy mechanism",
         "Backend_Development_Guidelines.md Section 3 Rule 5"],
        ["C-005", "No external event buses; Django Signals + Celery handle all event-driven logic",
         "Backend_Development_Guidelines.md Section 3 Rule 2"],
    ]
    s.append(make_table(constraints_table, col_weights=[0.5, 4.0, 2.0], font_size=8.5))
    s.append(caption("Table 15.2 &mdash; Five hard constraints imposed by the RIMIT development guidelines."))

    s.append(h2("15.3 Architecture Clarification Queries (Strategic RFIs)"))
    s.append(p(
        "The following six RFIs target ambiguities in the RFP that, if resolved before Phase 1 Discovery begins, will significantly reduce rework risk. Each query is technical, specific, and structured to elicit a definitive answer rather than a subjective preference."
    ))
    s.append(spacer(4))
    rfi_table = [
        ["ID", "RFI", "Why It Matters"],
        ["Q-001",
         "What is RIMIT&rsquo;s contractual RTO/RPO target? The architecture defaults to RPO 15min / RTO 1hr (PostgreSQL WAL archiving + PITR). If a stricter target (e.g., RPO 0 / RTO 5min) is required, we need synchronous cross-region replication (RDS Cross-Region Read Replica with promoted standby) which adds ~30% to monthly cloud cost.",
         "Affects backup strategy, DR runbook, and cloud cost estimate"],
        ["Q-002",
         "What is the expected inbound lead ingestion rate from Meta Lead Ads? Peak burst rate (leads/minute) and daily total. This drives Celery worker autoscale thresholds and the dedup strategy (in-memory Redis vs. DB-level UPSERT).",
         "Affects Celery capacity planning and Redis memory sizing"],
        ["Q-003",
         "Is Razorpay the preferred payment gateway, or should we evaluate PayU/Cashfree as primary? Razorpay has the cleanest API but PayU has lower MDR on UPI (0.5% vs 1.0%). Dual-gateway failover is supported either way.",
         "Affects payment integration cost and failure handling design"],
        ["Q-004",
         "What is the preferred MFA channel for sub-center logins: WhatsApp OTP (free, requires WhatsApp installed) or SMS OTP (INR 0.20/OTP, universal)? Hybrid model: WhatsApp primary, SMS fallback is the default.",
         "Affects MFA cost (INR 0 vs INR 5K/month) and user onboarding friction"],
        ["Q-005",
         "Does RIMIT have an existing Keycloak realm or Active Directory that we should integrate with, or will we provision a fresh Keycloak realm? Existing AD would require LDAP federation setup (~1 sprint) but reduces ongoing user management burden.",
         "Affects Phase 1 sprint scope and Keycloak configuration effort"],
        ["Q-006",
         "Are there India-only data residency requirements (e.g., DPDP Act mandates) that prohibit using AWS Mumbai for any specific data category? Specifically: should Aadhar hashes ever leave India? Our default keeps all data in ap-south-1 (Mumbai).",
         "Affects cloud region selection and cross-region backup strategy"],
    ]
    s.append(make_table(rfi_table, col_weights=[0.4, 4.0, 2.0], font_size=8.5))
    s.append(caption("Table 15.3 &mdash; Six strategic RFIs for RIMIT to answer before Discovery begins."))
    s.append(PageBreak())
    return s


# ═══════════════════════════════════════════════════════════════════════
# Section 16: Architectural Validation & Verification Ledger
# ═══════════════════════════════════════════════════════════════════════
def section_validation():
    s = []
    s.append(h1("16. Architectural Validation &amp; Verification Ledger"))
    s.append(p(
        "Per the architect_agent_prompt.md Section 4 protocol, every architectural proposal must be subjected to a comprehensive Technical Stress-Test Simulation before finalization. This section documents the four-part verification: 10x Elastic Scalability Assessment, High Availability &amp; SPOF Mitigation, RFP Matrix Coverage Verification, and Structural Feasibility Affirmation. The verification is signed off by the Principal Architect."
    ))

    s.append(h2("16.1 10x Elastic Scalability Assessment"))
    s.append(p(
        "<b>Scenario:</b> Simulated traffic volume 10x the stated baseline &mdash; 20,000 concurrent users (vs 2,000 baseline), 2,000 RPS sustained (vs 200), 10,000 search queries/minute (vs 1,000). The simulation identifies bottlenecks and the remediations applied to the design."
    ))
    s.append(spacer(4))
    bottleneck_table = [
        ["Bottleneck", "Detection Method", "Remediation Applied"],
        ["PostgreSQL connection pool exhaustion (max_connections=100)",
         "PgBouncer logs show queue depth &gt; 50",
         "PgBouncer transaction-mode pooling (max_client=1000, pool=50); Gunicorn workers reduced from 8 to 4 per container"],
        ["DB CPU saturation on search queries (tsvector + GIN)",
         "RDS Enhanced Monitoring shows CPU &gt; 90% for 5+ min",
         "Read replica promoted for read-only endpoints (/api/v1/courses/ search routes to read replica via django-read-replica)"],
        ["Celery worker starvation on broadcast campaigns",
         "Redis queue depth &gt; 1000 for 10+ min",
         "Separate queues: &lsquo;notifications&rsquo; (high volume, low latency), &lsquo;broadcasts&rsquo; (low volume, high throughput), &lsquo;default&rsquo; (everything else). Workers dedicated per queue."],
        ["MinIO disk I/O on concurrent uploads",
         "MinIO server logs show 429 responses",
         "MinIO cluster scaled to 5 nodes; client-side multipart chunk size reduced from 5MB to 2MB (more parallel chunks)"],
        ["Keycloak userinfo endpoint throttling (60s cache TTL)",
         "Sentry shows 429 from Keycloak",
         "JWT validation cache TTL raised from 60s to 300s; jwk rotation handled via background refresh"],
    ]
    s.append(make_table(bottleneck_table, col_weights=[1.8, 2.0, 3.0], font_size=8.5))
    s.append(caption("Table 16.1 &mdash; 10x load bottlenecks identified and remediations applied to the design."))

    s.append(h2("16.2 High Availability &amp; SPOF Mitigation"))
    s.append(p(
        "Every communication path was traced for single points of failure. The architecture has no single-AZ dependencies and no single-instance services in the critical path. The table below documents each SPOF identified and the HA mechanism applied."
    ))
    s.append(spacer(4))
    spof_table = [
        ["Potential SPOF", "HA Mechanism", "Failover Time"],
        ["RDS PostgreSQL primary", "Multi-AZ synchronous standby (auto-failover)", "60-120 seconds"],
        ["Keycloak primary", "2+ ECS containers behind ALB, DB-backed sessions", "Instant (ALB health check)"],
        ["Redis primary", "ElastiCache Multi-AZ with automatic failover", "30-60 seconds"],
        ["MinIO primary node", "3-node erasure-coded cluster, any 1 node can fail", "Instant (client retries)"],
        ["ECS Fargate app container", "ALB health check, 2+ containers minimum", "Instant (ALB routing)"],
        ["ALB itself", "AWS-managed, inherently HA across AZs", "N/A"],
        ["Cloudflare DNS", "Anycast network, inherently HA globally", "N/A"],
        ["Single AWS region (Mumbai)", "Cross-region S3 backup + RDS read replica (ap-south-2)", "Manual DR invocation, &lt; 1 hour"],
    ]
    s.append(make_table(spof_table, col_weights=[1.8, 2.8, 1.6], font_size=8.5))
    s.append(caption("Table 16.2 &mdash; SPOF audit. Every critical component has a documented HA mechanism."))

    s.append(h2("16.3 RFP Matrix Coverage Verification"))
    s.append(p(
        "Every functional requirement in the RFP is cross-referenced against the architectural component that delivers it. The table below confirms 100% coverage &mdash; no RFP requirement is unaddressed, and no unnecessary technical debt has been introduced."
    ))
    s.append(spacer(4))
    coverage_table = [
        ["RFP Requirement", "Architectural Component", "Section"],
        ["Module 1: Unified University Directory", "aggregator app + Django Admin + universities table", "&sect;5.1, &sect;6.1"],
        ["Module 1: Course &amp; Fee Repository (searchable)", "DRF courses endpoint + PostgreSQL tsvector/GIN", "&sect;5.1, &sect;6.1"],
        ["Module 1: Prospectus &amp; Document Library", "university_doc_vault table + MinIO + presigned URLs", "&sect;5.1, &sect;8.5"],
        ["Module 2: Direct Student Registration", "admissions app + multi-step Appsmith form + students table (RLS)", "&sect;5.3, &sect;6.2, &sect;7.1"],
        ["Module 2: Document Upload Vault (drag-drop)", "Appsmith file widget + TemporaryFileUploadHandler + MinIO multipart", "&sect;8.5"],
        ["Module 2: Real-time Status Tracking", "enrollments.status field + audit_logs + Appsmith timeline widget", "&sect;5.4, &sect;6.2"],
        ["Module 3: Session Enforcement Matrix", "rules_configurations JSONB + Django rules engine + /rules/validate/ endpoint", "&sect;5.5, &sect;6.3"],
        ["Module 3: Multi-tier Access Hierarchy (4 roles)", "Keycloak RBAC + DRF permission classes + RLS policies", "&sect;5.6, &sect;9.1"],
        ["Module 4: Lead Ingestion from Meta Ads", "Meta webhook + lead_ingestion_logs + HMAC verification", "&sect;8.1"],
        ["Module 4: WhatsApp + SMTP Notifications", "Celery tasks + WhatsApp Cloud API + django-celery-email + SES", "&sect;8.2, &sect;8.4"],
        ["Technical: Cloud-native, mobile-responsive", "AWS ECS + Appsmith responsive layouts", "&sect;3.3, &sect;7.4"],
        ["Technical: Enterprise search (Elasticsearch mentioned)", "PostgreSQL tsvector + GIN (sufficient to 500K); OpenSearch migration path documented", "&sect;5.1, &sect;4.3"],
        ["Technical: Secure cloud storage (S3 + encryption)", "MinIO cluster + AES-256 bucket encryption + presigned URLs", "&sect;4.6, &sect;8.5"],
        ["Technical: MFA for B2B logins", "Keycloak Authentication Flow with OTP-over-WhatsApp/SMS", "&sect;4.5, &sect;9.1"],
        ["Technical: SSL/TLS encryption in transit", "Nginx TLS 1.3 + HSTS + DB SSL + Redis TLS", "&sect;9.2"],
        ["Technical: RESTful API architecture", "DRF + drf-spectacular OpenAPI 3.1 + Appsmith OpenAPI connector", "&sect;6.5"],
        ["Technical: Automated fallback backups", "RDS WAL archiving (15min) + nightly pg_dump + MinIO versioning", "&sect;14.4"],
        ["Timeline: 5-phase delivery", "20-week sprint plan (3+6+6+3+2) mapped to RFP phases", "&sect;10"],
    ]
    s.append(make_table(coverage_table, col_weights=[2.4, 3.0, 1.0], font_size=8.0))
    s.append(caption("Table 16.3 &mdash; RFP requirements &rarr; architectural component traceability. 100% coverage."))

    s.append(h2("16.4 Structural Feasibility Affirmation"))
    s.append(p(
        "I affirm that the architecture described in this document is structurally feasible and can be successfully constructed by a standard 5-engineer team within the 20-week timeline without requiring bleeding-edge or unproven research R&amp;D. Every technology selected (Django 5.x, PostgreSQL 16, Celery 5.4, Redis 7, Keycloak 24, Nginx 1.26, MinIO, Appsmith Community) is a mature, production-grade, enterprise-deployed open-source project with documented best practices and active community support. No component is at &lt; v1.0; no component is end-of-life; no component requires custom patches or forks. The 8 explicit assumptions and 5 hard constraints are documented in Section 15 and surfaced as 6 strategic RFIs for RIMIT to resolve before Discovery begins."
    ))
    s.append(spacer(8))
    s.append(p(
        "The 10x scalability assessment (Section 16.1) demonstrates that the architecture degrades gracefully under stress with documented remediations. The SPOF audit (Section 16.2) confirms no single point of failure exists in the critical path. The RFP coverage matrix (Section 16.3) confirms 100% functional requirement coverage with no orphan requirements and no unnecessary technical debt. The architecture is hereby certified as production-ready pending the resolution of the 6 RFIs and the standard Discovery-phase wireframe and schema sign-off."
    ))
    s.append(spacer(20))
    s.append(p("<b>Principal Architect &mdash; Sign-off</b>"))
    s.append(p("Date: July 2026"))
    return s
