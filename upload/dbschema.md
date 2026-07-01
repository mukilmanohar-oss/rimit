# Comprehensive Database Schema: RIMIT Education B2B Aggregator

## 1. Module 1: Centralized University Aggregator
*   **universities**: `id` (UUID, PK), `name` (VARCHAR, UNIQUE), `state` (VARCHAR), `accreditation` (VARCHAR), `created_at` (TIMESTAMP)[span_1](start_span)[span_1](end_span)
*   **courses**: `id` (UUID, PK), `university_id` (FK), `name` (VARCHAR), `stream` (VARCHAR), `duration_months` (INT), `is_active` (BOOLEAN)[span_2](start_span)[span_2](end_span)
*   **fee_structures**: `id` (UUID, PK), `course_id` (FK), `fee_type` (VARCHAR), `amount` (DECIMAL)[span_3](start_span)[span_3](end_span)
*   **university_doc_vault**: `id` (UUID, PK), `university_id` (FK), `doc_type` (VARCHAR), `s3_object_uri` (TEXT)[span_4](start_span)[span_4](end_span)

## 2. Module 2: B2B Partner & User Governance
*   **sub_centers**: `id` (UUID, PK), `center_code` (VARCHAR, UNIQUE), `location` (VARCHAR), `status` (VARCHAR)[span_5](start_span)[span_5](end_span)
*   **system_users**: `id` (UUID, PK), `sub_center_id` (FK), `role` (VARCHAR), `email` (VARCHAR, UNIQUE)[span_6](start_span)[span_6](end_span)

## 3. Module 3: Student Registration & Academics
*   **students**: `id` (UUID, PK), `sub_center_id` (FK), `full_name` (VARCHAR), `dob` (DATE), `primary_phone` (VARCHAR), `email` (VARCHAR), `aadhar_number` (VARCHAR, UNIQUE), `address_data` (JSONB)[span_7](start_span)[span_7](end_span)
*   **student_academic_histories**: `id` (UUID, PK), `student_id` (FK), `qualification` (VARCHAR), `institution` (VARCHAR), `board_university` (VARCHAR), `year_of_passing` (INT), `score_type` (VARCHAR), `score_value` (DECIMAL)[span_8](start_span)[span_8](end_span)
*   **student_docs**: `id` (UUID, PK), `student_id` (FK), `academic_id` (FK, NULLABLE), `doc_category` (VARCHAR), `s3_object_uri` (TEXT), `status` (VARCHAR)[span_9](start_span)[span_9](end_span)

## 4. Module 4: Admissions & Finance
*   **intake_sessions**: `id` (UUID, PK), `session_name` (VARCHAR), `start_date` (DATE), `is_active` (BOOLEAN)[span_10](start_span)[span_10](end_span)
*   **enrollments**: `id` (UUID, PK), `student_id` (FK), `course_id` (FK), `session_id` (FK), `status` (VARCHAR), `created_at` (TIMESTAMP)[span_11](start_span)[span_11](end_span)
*   **payment_ledgers**: `id` (UUID, PK), `enrollment_id` (FK), `amount_paid` (DECIMAL), `transaction_ref` (VARCHAR, UNIQUE), `status` (VARCHAR)[span_12](start_span)[span_12](end_span)

## 5. Enterprise Compliance & Operational Observability
*   **audit_logs** (Partitioned by `created_at`): `id` (UUID, PK), `user_id` (FK), `action_type` (VARCHAR), `table_name` (VARCHAR), `row_id` (UUID), `old_data` (JSONB), `new_data` (JSONB), `created_at` (TIMESTAMP)[span_13](start_span)[span_13](end_span)
*   **lead_ingestion_logs** (Partitioned by `created_at`): `id` (UUID, PK), `source` (VARCHAR), `raw_payload` (JSONB), `status` (VARCHAR), `error_msg` (TEXT), `created_at` (TIMESTAMP)[span_14](start_span)[span_14](end_span)
*   **rules_configurations**: `id` (UUID, PK), `rule_name` (VARCHAR), `conditions` (JSONB), `is_active` (BOOLEAN)[span_15](start_span)[span_15](end_span)
*   **notification_logs** (Partitioned by `created_at`): `id` (UUID, PK), `recipient` (VARCHAR), `channel` (VARCHAR), `template_id` (VARCHAR), `delivery_status` (VARCHAR), `created_at` (TIMESTAMP)[span_16](start_span)[span_16](end_span)
