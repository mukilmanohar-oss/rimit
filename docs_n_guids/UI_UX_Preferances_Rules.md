
# UI/UX Standards & Best Practices: RIMIT B2B Portal

## 1. Form Design & Input Selection

The golden rule of B2B data entry is: **Never force the user to type if they can select.** Free-text fields are the primary source of database pollution and failed API payloads.

* **Radio Buttons vs. Dropdowns vs. Free-Text:**
* **1 to 4 Options:** Use **Radio Buttons** (or segmented control buttons). All options are visible at a glance, requiring only one click. *(Examples: Gender, Marital Status, Payment Mode).*
* **5 to 15 Options:** Use a **Standard Dropdown**. Keeps the UI clean while offering a manageable list. *(Examples: Lead Status, Ticket Category, State).*
* **15+ Options:** Use a **Searchable Dropdown (Combobox)**. Users must be able to type to filter the list. *(Examples: University Name, District, Course Name).*
* **Free-Text:** Strictly reserve this for highly variable data that cannot be predicted. *(Examples: Full Name, Ticket Subject, Address Line 1).*


* **Date Inputs:**
* Never use free-text for dates to avoid `DD-MM-YYYY` vs. `MM-DD-YYYY` conflicts. Always use the native **Date Picker** widget configured to return a standard ISO 8601 string (`YYYY-MM-DD`) to the Django backend.


* **Smart Defaults:**
* Pre-fill fields wherever logically possible. If a Sub-Center clicks "Add Lead," the `Lead Owner` field should default to the currently logged-in user.



## 2. Validation & Error Prevention

Errors must be caught in the browser (client-side) before they ever hit the Django API. This reduces server load and provides instant feedback to the user.

* **Real-Time Format Validation (Regex):**
* **Mobile Numbers:** Must enforce exactly 10 numeric digits. (Regex: `^[0-9]{10}$`).
* **Emails:** Must enforce standard email formatting before submission.


* **Mandatory Field Indicators:**
* All required fields must be clearly marked with a red asterisk (`*`).


* **The "Disabled Button" Rule (Crucial):**
* The primary action button (e.g., "Save Lead") must remain visually disabled (greyed out and unclickable) until **all** required fields are filled and **all** regex validations pass.


* **Preventing Double-Submits:**
* To prevent duplicate ledger entries or lead creations, all submit buttons must instantly switch to a "Loading" state (spinner) and disable themselves the millisecond they are clicked, binding to the API query's `isExecuting` property.



## 3. Visual Hierarchy & Layout Architecture

* **Data Density (Table Views):**
* B2B users need to see maximum information with minimum scrolling. Use compact table padding. A standard desktop view should comfortably display 15–20 rows per page.
* Always utilize **Server-Side Pagination** for tables. Never attempt to load thousands of leads into the Appsmith UI at once.


* **Progressive Disclosure:**
* Do not overwhelm the user with 15 filter options above a data table. Show the top 3 most used filters (e.g., Date Range, Status) and hide the rest behind a toggleable "More Filters" drawer or modal.


* **Action Button Hierarchy:**
* **Primary Action:** Solid background using the RIMIT brand color (e.g., "Submit", "Batch Checkout"). There should only be *one* primary button per screen/modal.
* **Secondary Action:** Outlined button or light grey (e.g., "Cancel", "Clear Filters").
* **Destructive Action:** Red text or red outline (e.g., "Delete", "Reject Lead"). **Must** trigger a secondary confirmation modal ("Are you sure?").



## 4. Feedback Loops & State Management

Never leave the user wondering if an action was successful.

* **Universal Toast Notifications:**
* **Success:** A brief green toast (e.g., "Ticket #1042 Created Successfully") triggered only when the API returns a `200` or `201` status.
* **Error:** A red toast that parses the exact error message from the Django backend. Do not use generic messages like "Something went wrong." Show the actual constraint failure (e.g., "Error: Student does not meet session eligibility criteria").


* **Empty States:**
* If a data table has no records (e.g., a new sub-center with zero leads), do not just show a blank grid. Display a friendly empty state illustration with a clear Call to Action (e.g., "No leads found. Click 'Add New Lead' to get started.").


* **Loading Skeletons:**
* When switching pages in a data table, use skeleton loaders (grey pulsing boxes) rather than freezing the screen, ensuring the UI feels responsive.



---
