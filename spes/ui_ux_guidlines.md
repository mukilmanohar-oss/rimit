To ensure the RIMIT Education B2B Aggregator maintains a high-performance, professional, and consistent experience across all devices, the following UI/UX guidelines must be strictly adhered to by the design and development teams.
# UI/UX Development Guidelines: RIMIT Education B2B Aggregator
## 1. Design Philosophy: "Corporate Minimalist"
 * **Goal:** Maximize data density without sacrificing readability for Academic Counselors and Sub-Center partners.
 * **Aesthetic:** Flat UI style, clear information hierarchy, and ample whitespace to reduce cognitive load during high-volume student data entry.
 * **Typography:** Enforce clean, sans-serif typography (Helvetica, Arial, or Segoe UI) with proportional sizing to ensure legibility across Desktop, Tablet, and Mobile devices.
## 2. Component & Layout Standards
 * **Responsive Architecture:** Design layouts must be fluid, optimizing screen real estate across all devices. Mobile-first design principles should be applied for the Sub-Center Partner Portal.
 * **Standardized Widget Library:** Use pre-built, robust UI components (tables, multi-step forms, file uploaders) to ensure consistent user behavior and accelerate development cycles.
 * **Interactive Feedback:** Every data submission (e.g., student registration, document upload) must provide immediate, non-blocking feedback (e.g., success toast messages, loading spinners) to maintain a responsive feel.
## 3. UI/UX Workflow & Governance
 * **Time-Boxed Iterations:** UI/UX wireframes are strictly capped at **two iterative rounds** per module to prevent endless design churn and ensure the project timeline remains on track.
 * **Asynchronous Review:** All UI/UX feedback and stakeholder sign-offs must occur via auditable, asynchronous platforms (e.g., Azure DevOps). No open-ended, non-documented boardroom meetings are permitted for design review.
 * **The "Locked Blueprint":** Once the design is signed off during the 3-week Discovery Phase, it is considered locked. Any deviations requested after this phase will trigger a formal Change Request (CR).
## 4. B2B Portal & Data Entry Optimization
 * **Form Validation:** Implement immediate field-level validation (e.g., regex for phone numbers, date range validation for birth dates) to ensure only valid data hits the backend API.
 * **Accessibility:** Adhere to WCAG 2.1 AA standards to ensure the portal is usable for all staff members, regardless of their visual or motor abilities.
 * **Progressive Disclosure:** For complex modules (e.g., multi-tier enrollment workflows), use progressive disclosure to reveal information only as needed, preventing information overload for Counselors.
## 5. Visual Styling Specification
 * **Color Palette Scheme:**
   * **Actionable Elements (Primary/Buttons):** Soft Slate Blue (#6c8ebf) for primary actions.
   * **Data/Tables:** Muted Sage Green (#82b366) for positive indicators or financial confirmations.
   * **Security/Alerts:** Warm Amber/Yellow (#d6b656) for non-critical warnings or status alerts.
 * **Visual Consistency:** Avoid heavy gradients, 3D shadows, or neon colors. Maintain a uniform, professional, "board-ready" aesthetic that mirrors the enterprise nature of the RIMIT and SPES Education brands.
*Note: These guidelines are the definitive standard for UI/UX development. Any deviation must be proposed via a Change Request and reviewed against the project's technical and commercial constraints.*



Based on the functional modules specified in the RIMIT Education B2B RFP, the following screens are required to deliver an end-to-end admission and aggregation platform.
### 1. Module 1: Centralized University Aggregator Hub
 * **University Directory Dashboard:** A grid/list view displaying all partner universities, filterable by state, accreditation, and mode.
 * **University Profile View:** Detailed view of a single university, showing course listings, fee structures, and document download links.
 * **Course & Fee Search Engine:** An advanced, multi-attribute search interface allowing users to filter by stream, eligibility, duration, and budget.
 * **Digital Prospectus Library:** A searchable repository allowing instant viewing and downloading of university prospectuses and official notification PDFs.
 * **Admin CMS (University Management):** A secure dashboard for Super Admins to dynamically update course content, fees, and institution profiles.
### 2. Module 2: B2B Sub-Center Partner Portal
 * **Sub-Center Login/MFA Interface:** A secure login screen enforcing MFA (OTP) as required.
 * **Partner Dashboard:** A high-level overview for sub-centers showing lead counts, pending enrollments, and recent announcements.
 * **Direct Student Registration Form:** A multi-step form for inputting candidate demographic data and choosing academic pathways.
 * **Document Upload Vault:** A dedicated interface featuring drag-and-drop capability for uploading high-resolution identity proofs, marklists, and migration certificates.
 * **Real-time Enrollment Tracking:** A list/table view where partners can monitor the status of their candidates within the multi-stage admission workflow (e.g., Applied, Fee Paid, Enrolled).
### 3. Module 3: Business Logic & Access Control
 * **Admin Rules Configuration Panel:** The interface for the Super Admin to configure the Session Enforcement Matrix, mapping eligibility rules to intake cycles.
 * **Role-Based Access Management (RBAC):** A configuration screen to map organizational roles (Academic Head, Counselor, Finance) to specific visibility boundaries.
 * **Financial & Ledger Dashboard:** A specialized view for Finance/Accounts Officers to track fee confirmations, ledger movements, and receipt generation.
### 4. Module 4: Marketing & Communication
 * **Lead Ingestion Log:** A monitor screen displaying inbound leads captured from Meta advertising infrastructures for auditing.
 * **Notification Broadcast Interface:** A management screen for broadcasting automated notifications via WhatsApp or SMTP for key workflow updates.
**Architectural Note:** These screens must adhere to the **Corporate Minimalist** design philosophy, prioritizing data density for administration and ease-of-use for sub-center partners on both desktop and mobile devices.
