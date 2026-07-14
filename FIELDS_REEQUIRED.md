# UI Definition Extraction for Admission Forms

## Screen 1: Leads Management Interface

### Layout Structure
- **Left Sidebar Navigation**
  - Dashboard
  - Users
  - Students
  - Leads (active)
    - Generate
    - Show
    - Show All
  - Accounts
    - Bills & Ledgers
    - Payments
    - Invoices
    - Download Center
  - Tickets
  - Marketing Tools (NEW)
    - Landing Pages
    - WhatsApp
  - Psychometric Test

### Main Content Area: Leads Form
**Fields:**
| Field | Type | Required | Default/Options |
|-------|------|----------|-----------------|
| Select Lead Owner | Dropdown | Yes | SPES EDUCATION (5518) |
| Email* | Text Input | Yes | jhon@example.com |
| Course* | Dropdown | Yes | BACHELOR OF BUSINESS ADMINISTRATION (BBA), BACHELOR OF COMPUTER APPLICATIONS (BCA), MASTER OF BUSINESS ADMINISTRATION (MBA), etc. |
| Date Of Birth* | Date Picker | Yes | dd-mm-yyyy format |
| Full Name* | Text Input | Yes | FULL NAME placeholder |
| Mobile* | Text Input with Country Code | Yes | +91 • 81234 56789 (India flag icon) |
| Sub-Course* | Dropdown | Yes | Choose → Professional Certificate in Business Analytics (KPMG) |
| State* | Dropdown | Yes | General, District, Data Analytics |

**Buttons:**
- Submit (blue primary button)
- Universal Lead Generator
- Show Leads

---

## Screen 2: Admission Form - Basic Details Section

### Layout Structure
- **Top Navigation Bar**: Home, Admission, Accounts, Documents, Settings, On Campus Referral, Others
- **Header**: "Fill up the Basic Details for Admission" with instructions (mandatory fields marked with *, document upload requirements)

**Fields:**
| Field | Type | Required | Default/Options |
|-------|------|----------|-----------------|
| Admission Session* | Dropdown | Yes | Jan 2026, July 2026 |
| Admission Type* | Dropdown | Yes | Fresh, Lateral |
| Faculty* | Dropdown | Yes | Business & Management - 503, Science, Arts |
| Course Type* | Dropdown | Yes | Undergraduate, Postgraduate, Diploma, Certificate |
| Course Name* | Dropdown | Yes | BACHELOR OF BUSINESS ADMINISTRATION (BBA), MASTER OF BUSINESS ADMINISTRATION (MBA) |
| Stream Name* | Dropdown | Yes | Operations Management, Finance Management, Marketing Management, Human Resource Management |
| Admission Semester* | Text Input | Yes | 1 |

**Basic Details Section:**
| Field | Type | Required | Default/Options |
|-------|------|----------|-----------------|
| Full Name* | Text Input | Yes | - |
| Father Name* | Text Input | Yes | - |
| Mother Name* | Text Input | Yes | - |
| DOB* | Date Picker | Yes | - |
| Gender* | Dropdown | Yes | Select, Male, Female, Other |
| Category* | Dropdown | Yes | General, OBC, SC, ST, EWS |
| Employment Status* | Dropdown | Yes | Employed, Unemployed, Student, Retired |
| Marital Status* | Dropdown | Yes | Single, Married, Divorced, Widowed |
| Religion* | Text Input | Yes | - |

**Buttons:**
- Apply Admission (blue primary button)
- Previous / Next navigation buttons

---

## Screen 3: Address Details Section

### Layout Structure
- **Permanent Address Details** section with document upload area
- **Correspondence Address Details** section below

**Permanent Address Fields:**
| Field | Type | Required | Default/Options |
|-------|------|----------|-----------------|
| RESIDENCE (DOMICILE)* | Checkbox | Yes | Sikkim, Other |
| Domicile State* | Text Input | Yes | - |
| COMPLETE ADDRESS* | Text Area | Yes | - |
| COUNTRY | Dropdown | Yes | INDIA |
| STATE | Dropdown | Yes | --SELECT ONE-- |
| DISTRICT | Dropdown | Yes | --SELECT ONE-- |
| CITY | Dropdown | Yes | --SELECT ONE-- |
| PIN CODE | Text Input | Yes | - |

**Correspondence Address Fields:**
| Field | Type | Required | Default/Options |
|-------|------|----------|-----------------|
| COMPLETE ADDRESS* SAME AS PERMANENT | Checkbox | Yes | - |
| COUNTRY | Dropdown | Yes | INDIA |
| STATE | Dropdown | Yes | --SELECT ONE-- |
| DISTRICT | Dropdown | Yes | --SELECT ONE-- |
| CITY | Dropdown | Yes | --SELECT ONE-- |
| PIN CODE | Text Input | Yes | - |

**Document Upload Area:**
- Aadhar (checkbox selected)
- Driving Licence
- Voter ID
- Passport

---

## Screen 4: Academic Details Section

### Layout Structure
- **Address Information Block**: Address, Pin, City, District, State, Email, Alternate Email, Mobile
- **Academic Details Table** with columns: Examination, Board/University, Year of Passing, % Marks, Result
- **Your Documents** section with downloadable files

**Academic Details Table:**
| Row | Examination | Board/University | Year of Passing | % Marks | Result |
|-----|-------------|------------------|-----------------|---------|--------|
| 1 | 10th | KERALA BOARD | 1998 | 85 | Pass |
| 2 | 12th | KERALA BOARD | 2000 | 90 | Pass |
| 3 | Graduation | CALORX TEACHERS UNIVERSITY | 2016 | 90 | Pass |

**Your Documents Section:**
- DEB ID (download icon)
- ABC ID (download icon)
- Address Id Proof - Front (download icon)
- 10th Mark-Sheet (Final) (download icon)
- Graduation Mark-Sheet (Final) (download icon)
- Student Signature (download icon)

---

## Screen 5: Form Continuation with Additional Fields

### Layout Structure
Continues from previous screen with additional fields revealed

**Additional Fields:**
| Field | Type | Required | Default/Options |
|-------|------|----------|-----------------|
| Course ID* | Text Input | Yes | - |
| Admission Semester* | Text Input | Yes | 1 |
| Personal Details section header | - | - | - |

**Address Fields (continued):**
| Field | Type | Required | Default/Options |
|-------|------|----------|-----------------|
| City* | Dropdown | Yes | --SELECT ONE-- |
| District* | Dropdown | Yes | --SELECT ONE-- |
| DOB* | Date Picker | Yes | - |
| Mobile | Text Input | Yes | - |
| Employment Status* | Dropdown | Yes | Employed, Unemployed, Student, Retired |
| Marital Status* | Dropdown | Yes | Single, Married, Divorced, Widowed |
| Alternate Email | Text Input | No | - |
| Category* | Dropdown | Yes | General, OBC, SC, ST, EWS |
| Alternate Mobile | Text Input | No | - |

---

## Screen 6: Document Upload Section

### Layout Structure
- **Permanent Address Details** with document upload area
- **Correspondence Address Details** section below

**Document Upload Area:**
- Aadhar (dropdown selected)
- Driving Licence
- Voter ID
- Passport

**Additional Fields in this screen:**
| Field | Type | Required | Default/Options |
|-------|------|----------|-----------------|
| Country* | Dropdown | Yes | INDIA |
| State* | Dropdown | Yes | --SELECT ONE-- |
| Pin Code* | Text Input | Yes | - |

---

## Screen 7: Correspondence Address Details (Expanded)

### Layout Structure
Shows detailed correspondence address form with all fields visible

**Correspondence Address Fields:**
| Field | Type | Required | Default/Options |
|-------|------|----------|-----------------|
| COMPLETE ADDRESS* SAME AS PERMANENT | Checkbox | Yes | - |
| COUNTRY | Dropdown | Yes | INDIA |
| STATE | Dropdown | Yes | --SELECT ONE-- |
| DISTRICT | Dropdown | Yes | --SELECT ONE-- |
| CITY | Dropdown | Yes | --SELECT ONE-- |
| PIN CODE | Text Input | Yes | - |

**Note text:** "NOTE: IF THE CORRESPONSE ADDRESS IS DIFFERENT FROM THE PERMANENT ADDRESS, SUBMIT ANY ONE SUPPORTING DOCUMENT SUCH AS RENT AGREEMENT OR ELECTRICITY BILL OR ANY OTHER VALID OFFICIAL DOCUMENT."

---

## Summary of UI Elements Across All Screens

### Common Patterns
- **Mandatory fields** marked with red asterisk (*)
- **Dropdowns** use "--SELECT ONE--" as default placeholder
- **Date pickers** follow dd-mm-yyyy format
- **Text inputs** have appropriate placeholders (e.g., "FULL NAME", "+91 • 81234 56789")
- **Primary action buttons** are blue with white text

### Field Types Used
| Type | Examples |
|------|----------|
| Text Input | Full Name, Email, Mobile, Address fields |
| Dropdown | Course, Faculty, State, Country selections |
| Date Picker | DOB field |
| Checkbox | Residence domicile options, Same as permanent address |

### Document Upload Areas
- Aadhar (with dropdown selection)
- Driving Licence
- Voter ID
- Passport
- Marksheet, Certificate, and Aadhaar Card (mentioned in instructions)