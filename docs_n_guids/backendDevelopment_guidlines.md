Here is the comprehensive backend engineering standard for the RIMIT B2B Aggregator, expanded to incorporate the new financial escrow logic and ticketing workflows. This serves as the definitive rulebook for Jovin, Prithwiraj, and the rest of the backend team at Bytestrone to ensure high-velocity, secure development.

---

# Backend Development Guidelines: RIMIT B2B Aggregator

## 1. Core Engineering Philosophy

* **The "No-Custom-Code" Mandate:** If Django, Django REST Framework (DRF), or PostgreSQL has a built-in feature, use it. Do not reinvent authentication, search, or data validation.
* **Database as the Enforcer:** Application-layer security is fragile. Security, multi-tenancy, and financial integrity must be enforced at the database kernel level.
* **Asynchronous by Default:** The main Django application thread is strictly for handling HTTP requests and fast DB reads/writes. Anything that takes longer than 200ms (PDF generation, commission calculations, email/WhatsApp triggers) belongs in a Celery background task.

## 2. Database & Security Standards (PostgreSQL)

* **Row-Level Security (RLS) is Mandatory:** Multi-tenancy for sub-centers must be handled via PostgreSQL RLS.
* *Rule:* Never rely solely on `Lead.objects.filter(sub_center=request.user.sub_center)`. RLS policies must be applied to the `leads`, `tickets`, and `invoices` tables to guarantee isolation at the query level.


* **Native Search Engine:**
* *Rule:* Use PostgreSQL `tsvector` and `GIN` indexes for the University Course directory search. Do not provision or integrate Elasticsearch/OpenSearch.


* **Multi-Factor Authentication (MFA):**
* Implement Time-based One-Time Passwords (TOTP) as the primary MFA standard. Keep SMS/WhatsApp OTP logic isolated strictly as a fallback mechanism to minimize recurring telecom OPEX.



## 3. Financial Logic & Ledger Standards

* **Double-Entry Immutable Ledger:** The platform operates on a B2B clearinghouse/escrow model.
* *Rule:* Never use a simple `is_paid=True` boolean flag on a student record. All financial movements must be recorded in the `transactions` and `center_ledgers` tables.


* **Batch Checkout Processing:**
* *Rule:* The payment API must accept an array of `student_ids`. Ensure the payload validation checks that all selected students belong to the requesting sub-center (via RLS) and are in a "Pending Payment" state before generating the bulk invoice.


* **Decoupled Commission Calculation:**
* *Rule:* Commission math must not block the payment gateway webhook response. The webhook must immediately return a `200 OK` to the gateway, logging the raw transaction. The calculation of RIMIT's cut and the university payout must be handed off to a Celery worker.



## 4. API & Framework Standards (Django/DRF)

* **Rapid API Generation:**
* *Rule:* Use DRF `ModelViewSet` for all CRUD operations. Manual API Views (`APIView` or `@api_view`) are only permitted for complex, non-standard actions (e.g., the batch checkout endpoint or webhook listeners).


* **Validation:** All incoming payload validation must occur inside DRF Serializers. Do not write validation logic inside the View or the Model's `save()` method.
* **Documentation:**
* *Rule:* Do not manually write Postman collections or Swagger docs. All APIs must be documented automatically using `drf-spectacular`.



## 5. File Handling & Background Workers (Celery/Redis)

* **Memory-Safe File Uploads:**
* *Rule:* Sub-centers and admins will upload heavy marketing assets and documents. Use Django’s `TemporaryFileUploadHandler` to spool files (10MB+) directly to the OS disk, bypassing container RAM.


* **Storage Handoff:** A Celery task will stream the spooled files from the local disk to the AWS S3 (or GCP Cloud Storage) Document Vault, saving the resulting URL back to the PostgreSQL database.
* **Bulk Download Optimization:**
* *Rule:* Never generate PDFs dynamically upon user request. Generate the admission receipt asynchronously at the moment of enrollment. When a "Bulk Download" is requested, a Celery worker will zip the existing S3 files and return a pre-signed download URL.



## 6. Deployment & Environment Parity

* **Containerization:** The application must run flawlessly in Docker. Local development must mirror production using a unified `docker-compose.yml` that spins up Django, PostgreSQL, Redis, and Celery simultaneously.
* **Pipeline Integration:** Ensure all backend code is pushed through the Azure DevOps pipelines for automated unit testing (specifically testing the RLS constraints and Ledger math) before the container image is tagged and pushed to the registry.