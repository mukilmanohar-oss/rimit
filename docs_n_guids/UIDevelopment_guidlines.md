To ensure Lavanya and Srilekshmi can execute the frontend at maximum velocity while maintaining the enterprise-grade ERP experience required for the RIMIT portal, these guidelines formalize the "Zero-Customization" and low-code strategy.

This document serves as the official UI/UX Standard Operating Procedure (SOP) for the Appsmith environment.

---

# UI Development Guidelines: Appsmith B2B Portal

## 1. Core Design Philosophy

* **Data Density Over Aesthetics:** The sub-center dashboard is an operational tool, not a marketing site. Prioritize information throughput (data tables, ledger balances, lead statuses) over large hero images or excessive whitespace.
* **Zero-Custom CSS:** Strictly utilize Appsmith’s native widget library. Do not inject custom HTML/CSS widgets unless absolutely critical for a missing feature.
* **Themed Consistency:** Before building the first screen, configure the Appsmith Global Theme parameters (Primary Color, Font Family, Border Radius) to match RIMIT’s brand guidelines. All subsequent widgets must inherit from this global theme.

## 2. Navigation & Layout Architecture

* **Left-Sidebar Standard:** Implement a fixed, collapsible left sidebar for the primary navigation (Dashboard, Leads, Accounts, Marketing Tools, Tickets).
* **Responsive Grid:** Ensure all dashboard widgets and data tables are configured to reflow gracefully for tablet users, as sub-center operators frequently use portable devices.
* **Modal Usage:** Use Appsmith Modals for localized actions (e.g., "Add Lead", "Create Ticket") to prevent unnecessary page routing and preserve the user's context on the main data tables.

## 3. Data Binding & API Integration (Django/DRF)

The UI must act strictly as a dumb presentation layer. All business logic belongs in the Django monolith managed by Jovin and Prithwiraj.

* **Server-Side Pagination:** Never load more than 50 records into the client browser at once. Configure Appsmith Table widgets to trigger API calls on page change, passing `?page=X` and `?limit=Y` parameters to the Django ViewSets.
* **Secure Token Management:** Upon successful MFA login, store the JWT securely in the Appsmith `appsmith.store`. All subsequent API queries must read from this store to inject the `Authorization: Bearer <token>` header.
* **Query Naming Convention:** Standardize API query names in Appsmith for readability (e.g., `get_Leads_List`, `post_Create_Ticket`, `patch_Batch_Checkout`).

## 4. Feature-Specific UI Patterns

* **Universal Lead Generator:**
* Implement client-side Regex validation for Mobile (10 digits) and Email before the API submit button becomes active. This saves unnecessary backend round-trips.
* Use dropdown widgets populated by live `GET /courses/` queries rather than hardcoding course options.


* **Batch Payment Checkouts:**
* The "Pending Payments" table must have row selection enabled.
* Bind a text widget to dynamically calculate and display the "Total Selected Amount: ₹X" based on the selected rows in real-time.


* **Document Downloads:**
* Bind download buttons to the asynchronous Celery S3 URLs. Show an intermediate "Generating..." loading state to manage user expectations while the backend zips the files.



## 5. State Management & Error Handling

* **Universal Feedback Loop:** Every single API mutation (POST, PUT, PATCH, DELETE) must be followed by a `showAlert()` action.
* *Success:* Green toast message (e.g., "Lead Successfully Added").
* *Error:* Red toast message extracting the exact error payload from the Django API response.


* **Prevent Double Submissions:** Configure all form submit buttons to bind their `Disabled` state to the `isExecuting` property of their respective API query.

## 6. Governance & Version Control

* **Git Sync:** Appsmith allows Git integration. The UI team must commit their UI states to an Azure DevOps repository branch (e.g., `feature/sub-center-dashboard`) at the end of each day.
* **Revision Locks:** Adhere strictly to the 2-round revision cap per module. Once RIMIT stakeholders approve a screen's functionality on the staging URL, lock the Appsmith page to prevent unauthorized "tweaks."

---

Would you like me to draft the specific JavaScript snippet templates that the UI team can copy-paste into Appsmith for handling the JWT authentication flow and standard API error mapping?