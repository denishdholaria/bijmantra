# Critical Backend TODOs

This file lists critical "TODO" items identified in `backend/app/api/v2/` that require attention. They are categorized by priority and type.

## High Priority: Security & Integrity

### 1. Hardcoded Organization ID and Missing Granular Auth
**File:** `backend/app/api/v2/import_api.py`

- **Issue:** The import process hardcodes `DEFAULT_ORG_ID = 1`. This effectively ignores the user's actual organization context for imported data, which is a major data integrity and security risk in a multi-tenant environment.
- **TODOs:**
    - `# TODO: Scope query by Organization ID once authentication is fully granular`
    - `# TODO: Get from current_user` (referring to `organization_id`)
- **Action Required:** Update `process_germplasm_import` and other import functions to accept `organization_id` as an argument (passed from `current_user` in the router) and use it for all database inserts and checks.

## High Priority: Missing Features

### 2. Data Visualization Module is a Stub
**File:** `backend/app/api/v2/data_visualization.py`

- **Issue:** The entire Data Visualization API is non-functional. Endpoints for creating, updating, and retrieving charts return errors or stubs because the underlying `charts` table does not exist.
- **TODOs:**
    - `# TODO: Query charts table when created`
    - `# TODO: Insert into charts table when created`
    - `# TODO: Update charts table when created`
    - `# TODO: Delete from charts table when created`
    - `# TODO: Query chart config and generate data`
- **Action Required:** Create the `charts` table migration and implement the CRUD logic for charts.

## Medium Priority: Incomplete Features

### 3. Collaboration Statistics Missing
**File:** `backend/app/api/v2/collaboration.py`

- **Issue:** The `/stats` endpoint returns hardcoded zeros for several metrics, providing misleading information to the frontend dashboard.
- **TODOs:**
    - `# TODO: Count from sharing table` (for `shared_items`)
    - `# TODO: Count from activity_log` (for `today_activity`)
    - `# TODO: Count from messages table` (for `unread_messages`)
- **Action Required:** Implement the SQL queries to count these items based on the existing `SharedItem`, `CollaborationActivity`, and `Message` tables.

## Low Priority: Pending Integration

### 4. GRIN-Global & Genesys Integration
**File:** `backend/app/api/v2/grin.py`

- **Issue:** Import endpoints return failures because external APIs are not configured/integrated with the internal Seed Bank module.
- **TODOs:**
    - `# TODO: Integrate with Seed Bank module when GRIN-Global API is configured`
    - `# TODO: Integrate with Seed Bank module when Genesys API is configured`
- **Action Required:** Once external API credentials are set up, implement the logic to map external accession data to internal `Germplasm` records.
