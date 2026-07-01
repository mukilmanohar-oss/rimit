"""
Sections 5-10 of the RIMIT Development Plan.
Imported by sections_content.py via re-export pattern.
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
# Section 5: Database Schema Walkthrough & Multi-Tenancy
# ═══════════════════════════════════════════════════════════════════════
def section_db_schema():
    s = []
    s.append(h1("5. Database Schema Walkthrough &amp; Multi-Tenancy"))
    s.append(p(
        "The database schema defined in dbschema.md comprises 17 tables organized into 5 modules. This section walks through each module, identifies the indexes required for the RFP&rsquo;s search and filtering requirements, and then details the Row-Level Security (RLS) policies that enforce multi-tenant isolation at the database layer &mdash; the single most important security control in the entire architecture."
    ))

    s.append(h2("5.1 Module 1 &mdash; Aggregator Hub Tables"))
    s.append(p(
        "The aggregator hub stores university profiles, course offerings, fee structures, and prospectus documents. The <code>universities</code> table uses a UUID primary key (vs auto-increment integer) to enable safe cross-system references without ID collision. The <code>courses</code> table carries a <code>search_vector</code> tsvector column (auto-maintained by a PostgreSQL trigger) combining name, stream, and eligibility text; a GIN index on this column powers the multi-attribute search required by RFP Module 1. The <code>fee_structures</code> table supports multiple fee types per course (admission, tuition, exam, library) via a one-to-many relationship. The <code>university_doc_vault</code> table stores S3 object URIs rather than binary blobs, keeping the database lean."
    ))
    s.append(spacer(4))
    s.append(code(
        "-- Search vector + GIN index on courses table\n"
        "ALTER TABLE courses ADD COLUMN search_vector tsvector\n"
        "  GENERATED ALWAYS AS (\n"
        "    setweight(to_tsvector('english', coalesce(name, '')), 'A') ||\n"
        "    setweight(to_tsvector('english', coalesce(stream, '')), 'B') ||\n"
        "    setweight(to_tsvector('english', coalesce(eligibility_text, '')), 'C')\n"
        "  ) STORED;\n"
        "CREATE INDEX idx_courses_search_gin ON courses USING GIN (search_vector);\n"
        "CREATE INDEX idx_courses_university ON courses (university_id);\n"
        "CREATE INDEX idx_courses_stream ON courses (stream) WHERE is_active = true;"
    ))
    s.append(spacer(4))
    s.append(p(
        "The <code>fee_structures</code> table uses DECIMAL(12,2) &mdash; not FLOAT &mdash; to prevent rounding errors in financial calculations, a non-negotiable rule for any system handling payment ledgers. All monetary amounts are stored in INR with 2 decimal places."
    ))

    s.append(h2("5.2 Module 2 &mdash; Partner &amp; User Governance"))
    s.append(p(
        "The <code>sub_centers</code> table is the root tenant entity &mdash; every student, enrollment, and document is scoped to exactly one sub_center_id. The <code>center_code</code> field (e.g., <code>KL-KOC-001</code>) is the human-readable identifier used in communications and audit logs; the UUID <code>id</code> is used in foreign keys. The <code>status</code> field supports values <code>active</code>, <code>suspended</code>, <code>terminated</code> &mdash; suspended centers can log in read-only but cannot register new students. The <code>system_users</code> table links Django/Keycloak user accounts to sub_centers, with the <code>role</code> field duplicating Keycloak&rsquo;s role claim for application-layer optimization (avoids a Keycloak API call per request)."
    ))

    s.append(h2("5.3 Module 3 &mdash; Student Registration &amp; Academics"))
    s.append(p(
        "The <code>students</code> table is the central entity of the B2B portal. The <code>aadhar_number</code> column is stored as a SHA-256 hash (not plaintext) using pgcrypto, with a uniqueness constraint to prevent duplicate registrations. The <code>address_data</code> JSONB column stores structured address components (line1, line2, city, district, state, pincode) without requiring schema migration when fields evolve. The <code>student_academic_histories</code> table supports multiple qualifications per student (10th, 12th, UG, PG) with a polymorphic <code>score_type</code> field (percentage, CGPA, grade) and corresponding <code>score_value</code>. The <code>student_docs</code> table links documents to either the student (identity proofs) or a specific academic history (marklists) via the nullable <code>academic_id</code> foreign key."
    ))

    s.append(h2("5.4 Module 4 &mdash; Admissions &amp; Finance"))
    s.append(p(
        "The <code>intake_sessions</code> table defines the enrollment windows (e.g., <code>July 2026</code>, <code>October 2026</code>) with start/end dates and active flags. The <code>enrollments</code> table is the workflow entity &mdash; its <code>status</code> field transitions through <code>Applied</code> &rarr; <code>Document Verified</code> &rarr; <code>Fee Pending</code> &rarr; <code>Fee Paid</code> &rarr; <code>Enrolled</code> &rarr; <code>Enrollment Generated</code>, with each transition logged to <code>audit_logs</code>. The <code>payment_ledgers</code> table enforces idempotency via the <code>transaction_ref</code> unique constraint &mdash; duplicate payment gateway callbacks cannot create duplicate ledger entries."
    ))

    s.append(h2("5.5 Module 5 &mdash; Compliance &amp; Observability"))
    s.append(p(
        "Four tables form the operational backbone: <code>audit_logs</code>, <code>lead_ingestion_logs</code>, <code>rules_configurations</code>, and <code>notification_logs</code>. All log tables are declaratively partitioned by <code>created_at</code> (monthly partitions) using PostgreSQL&rsquo;s native range partitioning &mdash; this keeps individual partitions small (1 month &asymp; 50K rows), enables fast partition pruning for date-range queries, and supports partition drop-off for retention policies (e.g., drop partitions older than 7 years). The <code>rules_configurations</code> table stores the Session Enforcement Matrix as JSONB conditions, evaluated by a Django service layer."
    ))
    s.append(spacer(4))
    s.append(code(
        "-- Declarative partitioning for audit_logs (monthly)\n"
        "CREATE TABLE audit_logs (\n"
        "  id UUID DEFAULT gen_random_uuid(),\n"
        "  user_id UUID REFERENCES system_users(id),\n"
        "  action_type VARCHAR(50) NOT NULL,\n"
        "  table_name VARCHAR(100) NOT NULL,\n"
        "  row_id UUID,\n"
        "  old_data JSONB,\n"
        "  new_data JSONB,\n"
        "  created_at TIMESTAMP NOT NULL DEFAULT NOW()\n"
        ") PARTITION BY RANGE (created_at);\n"
        "\n"
        "CREATE TABLE audit_logs_2026_07 PARTITION OF audit_logs\n"
        "  FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');\n"
        "CREATE TABLE audit_logs_2026_08 PARTITION OF audit_logs\n"
        "  FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');\n"
        "-- ... automate via pg_partman extension"
    ))

    s.append(h2("5.6 Multi-Tenancy via Row-Level Security (RLS)"))
    s.append(p(
        "The RFP&rsquo;s Module 2 requires that sub-centers operate autonomously but within rigid validation protocols set by central management. This translates to a hard security requirement: a sub-center staff member must <b>never</b> be able to read, modify, or even enumerate another sub-center&rsquo;s students, enrollments, or documents. Backend_Development_Guidelines.md mandates PostgreSQL Row-Level Security as the only acceptable mechanism: &lsquo;Never trust application-layer ORM filter(sub_center_id=...) alone for security-critical data.&rsquo;"
    ))
    s.append(p(
        "The RLS implementation uses a per-request session variable <code>app.current_sub_center_id</code>, set by Django middleware immediately after JWT verification. The database then transparently filters all queries on RLS-protected tables. The Super Admin role bypasses RLS via the <code>BYPASSRLS</code> PostgreSQL attribute, allowing cross-tenant visibility for the MD and Academic Heads."
    ))
    s.append(spacer(4))
    s.append(code(
        "-- Enable RLS on all tenant-scoped tables\n"
        "ALTER TABLE students ENABLE ROW LEVEL SECURITY;\n"
        "ALTER TABLE student_academic_histories ENABLE ROW LEVEL SECURITY;\n"
        "ALTER TABLE student_docs ENABLE ROW LEVEL SECURITY;\n"
        "ALTER TABLE enrollments ENABLE ROW LEVEL SECURITY;\n"
        "ALTER TABLE payment_ledgers ENABLE ROW LEVEL SECURITY;\n"
        "\n"
        "-- Sub-center staff: can only see their own tenant's rows\n"
        "CREATE POLICY tenant_isolation ON students\n"
        "  FOR ALL\n"
        "  USING (\n"
        "    sub_center_id = current_setting('app.current_sub_center_id')::uuid\n"
        "  )\n"
        "  WITH CHECK (\n"
        "    sub_center_id = current_setting('app.current_sub_center_id')::uuid\n"
        "  );\n"
        "\n"
        "-- Super Admin role bypasses RLS entirely\n"
        "ALTER ROLE rimit_super_admin BYPASSRLS;\n"
        "\n"
        "-- Academic Head role: read-only across all tenants\n"
        "GRANT SELECT ON students TO rimit_academic_head;\n"
        "-- (no BYPASSRLS; instead create a SELECT-only policy)\n"
        "CREATE POLICY academic_head_read ON students\n"
        "  FOR SELECT\n"
        "  USING (true);  -- visible to academic_head role only\n"
        "\n"
        "-- Django middleware sets the session variable per request:\n"
        "-- SET LOCAL app.current_sub_center_id = '<uuid-from-jwt-claim>';"
    ))
    s.append(spacer(4))
    s.append(p(
        "Critical safety net: integration tests must assert RLS isolation for <b>every</b> tenant-scoped endpoint. The test suite creates two sub-centers, registers a student under each, then attempts cross-tenant reads via the API and asserts 404 (not 200) &mdash; this catches any future code path that bypasses RLS via raw SQL or a missed <code>SET LOCAL</code>."
    ))
    s.append(PageBreak())
    return s


# ═══════════════════════════════════════════════════════════════════════
# Section 6: REST API Specifications by Module
# ═══════════════════════════════════════════════════════════════════════
def section_api_specs():
    s = []
    s.append(h1("6. REST API Specifications by Module"))
    s.append(p(
        "All endpoints follow RESTful conventions and are auto-documented via drf-spectacular (OpenAPI 3.1). The base URL is <code>/api/v1/</code> for stable endpoints and <code>/webhooks/</code> for external system callbacks. Every endpoint except webhooks requires a Bearer JWT in the Authorization header; webhooks use HMAC signature verification instead. The four RFP-defined roles (super_admin, academic_head, counselor, finance) are mapped to permission classes via DRF&rsquo;s <code>DjangoModelPermissions</code> with a custom <code>role_permissions</code> lookup."
    ))

    s.append(h2("6.1 Module 1 &mdash; Aggregator Hub Endpoints"))
    api_table = [
        ["Method", "Path", "Description", "Roles"],
        ["GET", "/api/v1/universities/", "List universities (filterable by state, accreditation)", "All"],
        ["POST", "/api/v1/universities/", "Create university", "super_admin"],
        ["GET", "/api/v1/universities/{id}/", "Get university detail with courses + fees", "All"],
        ["PATCH", "/api/v1/universities/{id}/", "Update university metadata", "super_admin"],
        ["GET", "/api/v1/courses/?search=&stream=&duration=", "Search courses (tsvector + filters)", "All"],
        ["POST", "/api/v1/courses/", "Create course under a university", "super_admin"],
        ["GET", "/api/v1/courses/{id}/fees/", "List fee structures for a course", "All"],
        ["GET", "/api/v1/prospectus/{doc_id}/download", "Generate presigned URL for prospectus PDF", "All"],
        ["POST", "/api/v1/prospectus/", "Upload new prospectus (admin only)", "super_admin"],
    ]
    s.append(make_table(api_table, col_weights=[0.6, 2.2, 2.2, 0.8], font_size=8.5))
    s.append(caption("Table 6.1 &mdash; Aggregator Hub API endpoints. &lsquo;All&rsquo; means all authenticated roles have read access."))

    s.append(h2("6.2 Module 2 &mdash; B2B Sub-Center Portal Endpoints"))
    api_table = [
        ["Method", "Path", "Description", "Roles"],
        ["GET", "/api/v1/students/", "List students (RLS-scoped to caller's sub_center)", "counselor, academic_head, super_admin"],
        ["POST", "/api/v1/students/", "Register new student (multi-step form backend)", "counselor"],
        ["GET", "/api/v1/students/{id}/", "Get student detail with academic history + docs", "counselor (own), academic_head, super_admin"],
        ["PATCH", "/api/v1/students/{id}/", "Update student demographic data", "counselor (own)"],
        ["POST", "/api/v1/students/{id}/documents/", "Upload student document (multipart, 100MB max)", "counselor (own)"],
        ["GET", "/api/v1/students/{id}/documents/", "List documents for a student", "counselor (own), academic_head"],
        ["GET", "/api/v1/enrollments/", "List enrollments (filterable by status, session)", "counselor, academic_head, finance"],
        ["POST", "/api/v1/enrollments/", "Create enrollment (validates session matrix)", "counselor"],
        ["PATCH", "/api/v1/enrollments/{id}/status", "Transition status (Applied&rarr;Verified&rarr;Fee Paid)", "counselor, finance, super_admin"],
        ["GET", "/api/v1/enrollments/{id}/timeline", "Audit trail for a specific enrollment", "counselor, academic_head"],
    ]
    s.append(make_table(api_table, col_weights=[0.6, 2.2, 2.5, 1.3], font_size=8.5))
    s.append(caption("Table 6.2 &mdash; B2B Portal API endpoints. RLS enforces sub_center scoping transparently."))

    s.append(h2("6.3 Module 3 &mdash; Business Logic &amp; Rules Endpoints"))
    api_table = [
        ["Method", "Path", "Description", "Roles"],
        ["GET", "/api/v1/intake-sessions/", "List intake sessions (active + historical)", "All"],
        ["POST", "/api/v1/intake-sessions/", "Create new intake session", "super_admin"],
        ["GET", "/api/v1/rules/session-matrix/", "List active session enforcement rules", "super_admin, academic_head"],
        ["POST", "/api/v1/rules/session-matrix/", "Create or update rule (JSONB conditions)", "super_admin"],
        ["POST", "/api/v1/rules/validate/", "Pre-validate an enrollment against active rules", "counselor"],
    ]
    s.append(make_table(api_table, col_weights=[0.6, 2.2, 2.5, 1.3], font_size=8.5))
    s.append(caption("Table 6.3 &mdash; Business logic endpoints. The /validate/ endpoint allows pre-flight checks before submission."))

    s.append(h2("6.4 Module 4 &mdash; Marketing &amp; Communication Endpoints"))
    api_table = [
        ["Method", "Path", "Description", "Auth"],
        ["POST", "/webhooks/meta/leads/", "Inbound Meta Lead Ads webhook (HMAC verified)", "HMAC sig"],
        ["POST", "/webhooks/razorpay/payments/", "Inbound payment callback (signature verified)", "RZP sig"],
        ["GET", "/api/v1/leads/", "List ingested leads (with source, status, error)", "academic_head, super_admin"],
        ["POST", "/api/v1/notifications/broadcast/", "Queue broadcast message (WhatsApp/SMTP)", "super_admin, academic_head"],
        ["GET", "/api/v1/notifications/logs/", "List notification delivery logs", "academic_head, super_admin"],
        ["POST", "/api/v1/notifications/templates/", "Create or update notification template", "super_admin"],
    ]
    s.append(make_table(api_table, col_weights=[0.6, 2.2, 2.5, 1.0], font_size=8.5))
    s.append(caption("Table 6.4 &mdash; Marketing &amp; communication endpoints. Webhooks use signature-based auth; management endpoints use JWT."))

    s.append(h2("6.5 OpenAPI Documentation &amp; SDK Generation"))
    s.append(p(
        "drf-spectacular auto-generates an OpenAPI 3.1 schema at <code>/api/v1/schema/</code> and a Swagger UI at <code>/api/v1/schema/swagger-ui/</code>. The schema is consumed by Appsmith&rsquo;s OpenAPI connector to bind UI widgets to endpoints without manual configuration &mdash; this satisfies the UI development guideline that &lsquo;the UI must be entirely driven by drf-spectacular generated OpenAPI schemas.&rsquo; The same schema can be used to generate TypeScript SDKs for any future mobile app or third-party integration via <code>openapi-generator-cli</code>."
    ))
    s.append(PageBreak())
    return s


# ═══════════════════════════════════════════════════════════════════════
# Section 7: UI/UX Screen Inventory & Design System
# ═══════════════════════════════════════════════════════════════════════
def section_ui_inventory():
    s = []
    s.append(h1("7. UI/UX Screen Inventory &amp; Design System"))
    s.append(p(
        "The UI/UX guidelines define a &lsquo;Corporate Minimalist&rsquo; design philosophy prioritizing data density for B2B administrative users and ease-of-use for sub-center partners on mobile devices. Per the ui_development_guid.md mandate, all internal administrative screens are built on <b>Appsmith Community Edition</b> using drag-and-drop connectors bound to DRF endpoints &mdash; no React/Vue/Angular code is written for internal screens. This section enumerates all 15 required screens, their primary user roles, key components, and the Appsmith template pattern each maps to."
    ))

    s.append(h2("7.1 Screen Inventory by Module"))
    screens_table = [
        ["#", "Screen", "Module", "Primary Role", "Appsmith Pattern"],
        ["1", "University Directory Dashboard", "1", "All", "List + Filter"],
        ["2", "University Profile View", "1", "All", "Detail + Tabbed Sub-lists"],
        ["3", "Course &amp; Fee Search Engine", "1", "All", "Search + Faceted Filter"],
        ["4", "Digital Prospectus Library", "1", "All", "Document Grid + Preview"],
        ["5", "Admin CMS (University Mgmt)", "1", "super_admin", "CRUD + Bulk Import"],
        ["6", "Sub-Center Login + MFA", "2", "sub_center_staff", "Custom (Keycloak OIDC)"],
        ["7", "Partner Dashboard", "2", "sub_center_staff", "KPI Cards + Task List"],
        ["8", "Direct Student Registration Form", "2", "counselor", "Multi-step Form Wizard"],
        ["9", "Document Upload Vault", "2", "counselor", "Drag-drop + Progress"],
        ["10", "Real-time Enrollment Tracking", "2", "counselor, academic_head", "Status Table + Timeline"],
        ["11", "Admin Rules Configuration Panel", "3", "super_admin", "JSONB Editor + Preview"],
        ["12", "Role-Based Access Management (RBAC)", "3", "super_admin", "Matrix Grid"],
        ["13", "Financial &amp; Ledger Dashboard", "3", "finance", "Pivot Table + Charts"],
        ["14", "Lead Ingestion Log Monitor", "4", "academic_head", "Log Stream + Filter"],
        ["15", "Notification Broadcast Interface", "4", "academic_head, super_admin", "Compose + Audience Picker"],
    ]
    s.append(make_table(screens_table, col_weights=[0.3, 2.2, 0.5, 1.6, 1.8], font_size=8.5))
    s.append(caption("Table 7.1 &mdash; Complete screen inventory (15 screens) mapped to RFP modules and Appsmith template patterns."))

    s.append(h2("7.2 Design System &amp; Tokens"))
    s.append(p(
        "The design system enforces visual consistency across all 15 screens via a restricted set of design tokens. The color palette derives directly from the RFP UI/UX guidelines&rsquo; three-color scheme (Soft Slate Blue, Muted Sage Green, Warm Amber) extended with neutral text and surface tones. Typography mandates sans-serif (Helvetica/Arial/Segoe UI) for cross-device consistency &mdash; no decorative fonts are permitted in the B2B interface."
    ))
    s.append(spacer(4))
    tokens_table = [
        ["Token Category", "Token Name", "Value", "Usage"],
        ["Color &mdash; Primary", "action-primary", "#6c8ebf", "Primary buttons, active nav, links"],
        ["Color &mdash; Positive", "indicator-positive", "#82b366", "Success toasts, fee-paid status"],
        ["Color &mdash; Warning", "indicator-warning", "#d6b656", "Non-critical alerts, pending status"],
        ["Color &mdash; Text", "text-primary", "#131515", "Body text, headings"],
        ["Color &mdash; Text Muted", "text-muted", "#747b7e", "Captions, meta info"],
        ["Color &mdash; Surface", "surface-card", "#e8eaeb", "Card backgrounds, table stripes"],
        ["Color &mdash; Border", "border-default", "#acbdc5", "Card borders, dividers"],
        ["Typography &mdash; Heading", "font-heading", "Helvetica, Arial, sans-serif (700)", "Screen titles, section headers"],
        ["Typography &mdash; Body", "font-body", "Helvetica, Arial, sans-serif (400)", "Paragraphs, table cells"],
        ["Spacing &mdash; Base Unit", "space-base", "8px", "All margins/padding multiples of 8"],
        ["Spacing &mdash; Section Gap", "space-section", "32px", "Between H2 sections"],
        ["Radius &mdash; Default", "radius-default", "4px", "Buttons, inputs, cards"],
    ]
    s.append(make_table(tokens_table, col_weights=[1.4, 1.4, 1.8, 2.0], font_size=8.5))
    s.append(caption("Table 7.2 &mdash; Design system tokens. All values are derived from the RIMIT UI/UX guidelines."))

    s.append(h2("7.3 Workflow Governance &amp; Revision Cap"))
    s.append(p(
        "Per ui_ux_guidlines.md Section 3, all wireframing is time-boxed to the 3-week Discovery Phase, with stakeholder feedback strictly gated to <b>two iterative rounds per module</b>. After sign-off via Azure DevOps, the design becomes a &lsquo;Locked Blueprint&rsquo; &mdash; any subsequent deviation requires a formal Change Request (CR) reviewed against the project&rsquo;s technical and commercial constraints. This governance model eliminates the design churn that typically stalls rapid development projects and protects the 20-week delivery timeline."
    ))
    s.append(h2("7.4 Performance &amp; Accessibility Rules"))
    s.append(p(
        "All data tables implement server-side pagination (page size 25) with skeleton loading states to handle the 50K+ course catalogue without client-side data manipulation. Form inputs implement client-side regex validation mirroring the backend serializer logic (email, phone, Aadhar, pincode) to minimize API round-trips. All screens adhere to <b>WCAG 2.1 AA</b> &mdash; color contrast ratio &ge; 4.5:1, keyboard navigable, ARIA labels on icon-only buttons, and screen-reader-compatible table headers. Mobile-first responsive grids ensure the Sub-Center Portal is usable on tablet-sized viewports (768px+), as partners often operate on portable hardware."
    ))
    s.append(PageBreak())
    return s


# ═══════════════════════════════════════════════════════════════════════
# Section 8: External Integrations Design
# ═══════════════════════════════════════════════════════════════════════
def section_integrations():
    s = []
    s.append(h1("8. External Integrations Design"))
    s.append(p(
        "The RFP specifies four external integrations (Meta Lead Ads, WhatsApp Business API, payment gateways, SMTP) and the document vault. This section details each integration&rsquo;s data flow, failure handling, and security model. All integrations follow the same architectural pattern: external system &rarr; Django webhook receiver (signature-verified) or Celery task &rarr; database write &rarr; Django Signal &rarr; downstream Celery task chain. This pattern ensures that no inbound payload is ever lost, no outbound notification is ever sent twice (idempotency keys), and every step is auditable via the <code>audit_logs</code> and <code>notification_logs</code> tables."
    ))

    s.append(h2("8.1 Meta Lead Ads Webhook Integration"))
    s.append(p(
        "Meta publishes lead data to a webhook URL configured in the Facebook App Dashboard. The webhook receives a JSON payload containing the lead form ID, leadgen_id, page ID, and timestamp. The full lead detail (name, phone, email, course of interest) is fetched via the Graph API using the page access token. The flow is: (1) Django webhook receiver verifies HMAC-SHA256 signature using App Secret, (2) dedup check against <code>lead_ingestion_logs.raw_payload ->&gt; 'leadgen_id'</code>, (3) Graph API call to fetch lead detail, (4) write to <code>lead_ingestion_logs</code> with status <code>ingested</code>, (5) Celery task creates a placeholder student record and links it to the originating sub_center based on campaign-to-center mapping."
    ))
    s.append(spacer(4))
    s.append(code(
        "# Webhook receiver with HMAC verification (Django view)\n"
        "@csrf_exempt\n"
        "@require_POST\n"
        "def meta_lead_webhook(request):\n"
        "    sig = request.headers.get('X-Hub-Signature-256', '')\n"
        "    expected = 'sha256=' + hmac.new(\n"
        "        settings.META_APP_SECRET.encode(),\n"
        "        request.body,\n"
        "        hashlib.sha256\n"
        "    ).hexdigest()\n"
        "    if not hmac.compare_digest(sig, expected):\n"
        "        return HttpResponse(403)\n"
        "    payload = json.loads(request.body)\n"
        "    if payload.get('object') == 'page':\n"
        "        for entry in payload['entry']:\n"
        "            for lead in entry.get('changes', []):\n"
        "                process_lead.delay(lead['value'])  # idempotent Celery task\n"
        "    return HttpResponse(200)"
    ))
    s.append(spacer(4))
    s.append(p(
        "Failure handling: if the Graph API call fails, the lead is logged with status <code>fetch_failed</code> and retried via Celery with exponential backoff (3 attempts: 1min, 5min, 30min). After 3 failures, the lead is marked <code>dead_letter</code> and an alert is raised to the Academic Head via WhatsApp. Meta&rsquo;s webhook retry policy (3 retries over 5 minutes) means our webhook must return 200 within 5 seconds &mdash; hence the async delegation to Celery."
    ))

    s.append(h2("8.2 WhatsApp Business API Integration"))
    s.append(p(
        "WhatsApp is used for two distinct purposes: (1) outbound notifications on enrollment status changes (template messages), and (2) MFA OTP delivery for sub-center logins. The integration uses the Cloud API (Meta Graph API v18.0) with a verified business account and approved message templates. Outbound messages are sent via Celery tasks with idempotency keys (the <code>message_id</code> returned by WhatsApp) stored in <code>notification_logs</code> &mdash; if a Celery task retries after a network timeout, the idempotency check prevents duplicate sends."
    ))
    s.append(p(
        "Rate limiting: WhatsApp enforces 80 messages/second per phone number, with tier-based daily limits (Tier 1: 1K/day, Tier 2: 10K/day, Tier 3: 100K/day). For broadcast campaigns (e.g., announcing a new intake session), the Celery task uses <code>rate_limit=&lsquo;75/s&rsquo;</code> to stay under the per-second cap, and the broadcast UI enforces a daily quota check before submission. Template messages require pre-approval by Meta (24&ndash;48 hours lead time) &mdash; the design reserves 6 pre-approved templates covering: enrollment confirmation, fee pending, fee paid, document pending, enrollment generated, and broadcast announcement."
    ))

    s.append(h2("8.3 Payment Gateway &mdash; Razorpay Integration"))
    s.append(p(
        "Razorpay is the recommended payment gateway for the Indian market (UPI, NetBanking, Cards, Wallets). The flow: (1) sub-center staff clicks &lsquo;Generate Fee Link&rsquo; on an enrollment, (2) Celery task calls Razorpay API to create a payment link with amount and student details, (3) link is sent to student via WhatsApp/SMS, (4) student pays via Razorpay-hosted page, (5) Razorpay webhook hits <code>/webhooks/razorpay/payments/</code> with signature, (6) webhook verifies signature using webhook secret, (7) writes to <code>payment_ledgers</code> with status <code>captured</code>, (8) Django Signal triggers enrollment status update to <code>Fee Paid</code> and dispatches receipt PDF via WhatsApp."
    ))
    s.append(p(
        "Idempotency is critical: Razorpay retries webhooks up to 5 times on non-2xx responses. The <code>transaction_ref</code> unique constraint on <code>payment_ledgers</code> ensures that a retried webhook for the same payment cannot create a duplicate ledger entry &mdash; the second insert raises IntegrityError, which the webhook handler catches and returns 200 (treating it as a successful idempotent replay). Receipt PDFs are generated via WeasyPrint from a Django template and uploaded to MinIO; the presigned URL is sent to the student via WhatsApp."
    ))

    s.append(h2("8.4 SMTP / Email Notifications"))
    s.append(p(
        "Transactional emails are sent via Amazon SES (Mumbai region) with Django&rsquo;s <code>django-celery-email</code> package, which routes all <code>send_mail()</code> calls through a Celery queue. This decouples email sending from the request-response cycle &mdash; if SES is temporarily unavailable, emails queue in Redis and retry automatically. SES configuration includes a verified domain (SPF, DKIM, DMARC) and a dedicated IP for higher reputation. Email templates are stored in the database (not code) so marketing staff can edit copy without a deployment."
    ))

    s.append(h2("8.5 Document Vault &mdash; MinIO/S3 Integration"))
    s.append(p(
        "All file uploads use Django&rsquo;s <code>TemporaryFileUploadHandler</code> which spools files larger than 2.5MB to disk (in <code>/tmp</code>) rather than holding them in memory &mdash; this is critical for the 100MB upper limit on student documents. The upload flow: (1) file received by Django, spooled to disk, (2) Celery task uploads to MinIO via the S3-compatible API using multipart upload for files &gt; 5MB (resumable on failure), (3) MinIO returns the object URI, (4) the URI is stored in <code>student_docs.s3_object_uri</code> or <code>university_doc_vault.s3_object_uri</code>, (5) the local temp file is deleted."
    ))
    s.append(p(
        "Downloads use presigned URLs valid for 15 minutes, generated on-demand by the API. The URL is returned to the Appsmith UI, which opens it in a new tab or triggers a download. This pattern keeps document access auditable (every download request passes through the API and is logged to <code>audit_logs</code>) without streaming binary content through Django. MinIO bucket encryption (AES-256) is enabled at the bucket level, satisfying the RFP&rsquo;s &lsquo;encryption at rest&rsquo; requirement without per-object encryption overhead."
    ))
    s.append(PageBreak())
    return s
