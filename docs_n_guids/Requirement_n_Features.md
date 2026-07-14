Here is the comprehensive breakdown of the requirements and features for the RIMIT Education B2B Aggregator, consolidated from the updated RFP and our finalized architectural blueprints.

### Module 1: Centralized University Aggregator Hub

This module acts as the core search and discovery engine for sub-centers.

* **Unified University Directory:** A visual grid interface displaying all partner universities (Online/ODL streams) across India.
* **Course & Fee Repository:** An exhaustive, searchable listing of courses filterable by stream, eligibility criteria, duration, and structured fee plans.
* **Prospectus & Document Library:** A secure, centralized digital vault allowing users to instantly view and download university prospectuses, academic calendars, and official notifications.

### Module 2: B2B Sub-Center Partner Portal (ERP)

This module acts as the isolated operational workspace for franchise partners, requiring a modern left-sidebar navigation architecture.

* **Main Dashboard:**
* Real-time statistics displaying Active vs. Total sub-centers.
* **Escalation Matrix:** Multi-level support contacts (Level 1, Level 2, Level 3) displaying names, emails, and mobile numbers for issue resolution.
* **University SPOCs:** A structured list displaying the Single Point of Contact mapped for each respective university.


* **Students & Leads Management:**
* **Universal Lead Generator:** A comprehensive form capturing Lead Owner, Full Name, Email, Mobile, Course, Sub-Course, Date of Birth, State, and District.
* **Data Views:** Toggle options to filter lists by "Leads", "Students (Confirmed Admissions)", and "Show All".


* **Accounts & Financials (Escrow/Clearinghouse Model):**
* **Bills & Ledgers:** Transparent tracking of center-wise ledger balances.
* **Batch Checkout:** Ability for sub-centers to select multiple pending students and execute a single bulk payment through the gateway.
* **Payments & Invoices:** Logging of payment gateway transactions and automated invoice generation.
* **Download Center:** A facility for bulk downloading financial receipts and admission confirmations via a zipped archive.


* **Marketing Tools Suite:**
* Access to pre-approved, university-specific landing pages.
* Direct API trigger capabilities for WhatsApp student communication.
* Access to career counseling Psychometric Tests for prospective leads.
* **Knowledge Base & Media Assets:** A repository for downloading promotional banners, social media assets, brochures, and benchmarking collateral.


* **Helpdesk & Support:**
* **Tickets System:** An internal ticketing application allowing sub-centers to raise operational, technical, or admission queries directly to RIMIT central administration.



### Module 3: Advanced Business Logic & Administration

This module governs the internal rules and platform access for RIMIT's core staff.

* **Session Enforcement Matrix:** Programmatic validation rules that map specific student eligibility to distinct intake cycles (e.g., blocking fresh candidates for July sessions if they only qualify for October).
* **Multi-Tier Access Hierarchy:** Granular Role-Based Access Control (RBAC) mapped to specific roles: Super Admin, Academic Head, Counselors, Finance, and Sub-Centers.
* **Dynamic Commission Engine:** A backend ledger ruleset allowing admins to configure RIMIT's commission per course (as a flat fee or percentage), automatically calculating the remaining payout owed to the university upon a successful sub-center payment.

### 4. Technical & Security Requirements

* **Deployment & UI Standard:** Cloud-native web application with a responsive design optimizing the grid-based content area and left-sidebar across Desktop, Tablet, and Mobile devices.
* **Data Isolation (RLS):** Strict enforcement of PostgreSQL Row-Level Security to ensure sub-centers can only query and view their own leads, tickets, and ledger data.
* **Authentication Security:** Multi-Factor Authentication (MFA) required for sub-center logins, utilizing TOTP (Authenticator Apps) as the primary method to reduce OPEX, with SMS/WhatsApp OTP as a fallback.
* **Data Encryption:** SSL/TLS data encryption in transit.
* **Storage Optimization:** Secure cloud storage (S3) optimized to handle high-volume PDF prospectus downloads and heavy student document uploads (Identity Proofs, Marklists) using asynchronous background workers.