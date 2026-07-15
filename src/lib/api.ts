/**
 * RIMIT B2B Aggregator — API client.
 *
 * All requests go through the Caddy gateway with XTransformPort=8000
 * to reach the Django backend (in sandbox preview), OR through Next.js
 * rewrites (in local dev on port 80).
 *
 * Note: Django routers use trailing_slash=False, so all paths are slash-free.
 */

const API_BASE = '/api/v1';
const TRANSFORM_PORT = '8000';

export const DEFAULT_PAGE_SIZE = 25;

export function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('rimit_token');
}

export function setAuthToken(token: string | null) {
  if (typeof window === 'undefined') return;
  if (token) localStorage.setItem('rimit_token', token);
  else localStorage.removeItem('rimit_token');
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getAuthToken();
  // Always append XTransformPort as a query param.
  const sep = path.includes('?') ? '&' : '?';
  const url = `${API_BASE}${path}${sep}XTransformPort=${TRANSFORM_PORT}`;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options.headers as Record<string, string>) || {}),
  };
  if (token) headers['Authorization'] = `Token ${token}`;

  const resp = await fetch(url, { ...options, headers });

  if (resp.status === 401) {
    setAuthToken(null);
    throw new Error('Unauthorized — please log in again.');
  }
  if (resp.status === 204) return undefined as T;

  const data = await resp.json().catch(() => ({ detail: resp.statusText }));
  if (!resp.ok) {
    const err = (typeof data === 'object' && data) ? data : { detail: String(data) };
    throw new Error(err.detail || JSON.stringify(err) || `HTTP ${resp.status}`);
  }
  return data as T;
}

/** Upload helper — sends FormData instead of JSON */
async function apiUpload<T>(path: string, formData: FormData, method: string = 'POST'): Promise<T> {
  const token = getAuthToken();
  const sep = path.includes('?') ? '&' : '?';
  const url = `${API_BASE}${path}${sep}XTransformPort=${TRANSFORM_PORT}`;

  const headers: HeadersInit = {};
  if (token) headers['Authorization'] = `Token ${token}`;
  // DO NOT set Content-Type; browser will set multipart/form-data with boundary

  const resp = await fetch(url, { method: method, headers, body: formData });

  if (resp.status === 401) {
    setAuthToken(null);
    throw new Error('Unauthorized — please log in again.');
  }
  if (resp.status === 204) return undefined as T;

  const data = await resp.json().catch(() => ({ detail: resp.statusText }));
  if (!resp.ok) {
    const err = (typeof data === 'object' && data) ? data : { detail: String(data) };
    throw new Error(err.detail || JSON.stringify(err) || `HTTP ${resp.status}`);
  }
  return data as T;
}

// ──────────────── Types ────────────────
export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export function withPaging(
  params: Record<string, string> | undefined,
  paging: { page?: number; pageSize?: number }
): Record<string, string> {
  const next: Record<string, string> = { ...(params || {}) };
  if (paging.page !== undefined) next.page = String(paging.page);
  if (paging.pageSize !== undefined) next.page_size = String(paging.pageSize);
  return next;
}

export function hasNextPage<T>(paginated: Paginated<T> | null | undefined): boolean {
  return Boolean(paginated?.next);
}

export function hasPrevPage<T>(paginated: Paginated<T> | null | undefined): boolean {
  return Boolean(paginated?.previous);
}

export interface University {
  id: string;
  name: string;
  state: string;
  accreditation?: string;
  description?: string;
  website?: string;
  is_active: boolean;
  default_university_share_percent?: string | number;
  course_count?: number;
  courses?: Course[];
  documents?: UniversityDoc[];
  created_at: string;
}

export interface Course {
  id: string;
  university: string;
  university_name?: string;
  university_state?: string;
  name: string;
  stream: string;
  duration_months: number;
  is_active: boolean;
  eligibility_text?: string;
  eligibility_criteria_json?: Record<string, unknown>;
  university_share_percent?: string | number | null;
  total_fee?: number;
  fees?: FeeStructure[];
  created_at: string;
}

export interface FeeStructure {
  id: string;
  course: string;
  course_name?: string;
  fee_type: string;
  amount: string;
  currency: string;
  is_active: boolean;
  notes?: string;
}

export interface UniversityDoc {
  id: string;
  university: string;
  university_name?: string;
  course?: string | null;
  course_name?: string | null;
  doc_type: string;
  title: string;
  s3_object_uri: string;
  file_size_bytes?: number;
  mime_type: string;
  is_public: boolean;
  uploaded_by?: string;
  created_at?: string;
}

export interface SubCenter {
  id: string;
  center_code: string;
  name: string;
  location: string;
  state?: string;
  status: string;
  contact_phone?: string;
  contact_email?: string;
  commission_percent?: string | number;
}

export interface SystemUser {
  id: string;
  user: number;
  username?: string;
  email: string;
  role: string;
  phone?: string;
  sub_center?: string;
  sub_center_code?: string;
  full_name?: string;
  is_active?: boolean;
  created_at?: string;
}

export interface NotificationLog {
  id: string;
  recipient: string;
  channel: string;
  template_id: string;
  delivery_status: string;
  retry_count: number;
  error_msg?: string;
  message_body?: string;
  context_data?: Record<string, unknown>;
  created_at: string;
}

export interface TicketMessage {
  id: string;
  sender_name: string;
  message: string;
  is_internal: boolean;
  created_at: string;
}

export interface Ticket {
  id: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  created_by_name: string;
  assigned_to_name: string;
  messages: TicketMessage[];
  created_at: string;
}

export interface StudentAddressBlock {
  perm_domicile_type?: string;
  domicile_state?: string;
  perm_address?: string;
  perm_country?: string;
  perm_state?: string;
  perm_district?: string;
  perm_city?: string;
  perm_pincode?: string;
  corr_address?: string;
  corr_country?: string;
  corr_state?: string;
  corr_district?: string;
  corr_city?: string;
  corr_pincode?: string;
}

export interface Student {
  id: string;
  sub_center: string;
  sub_center_code?: string;
  full_name: string;
  dob: string;
  gender?: string;
  primary_phone: string;
  email?: string;
  parent_name?: string;
  father_name?: string;
  mother_name?: string;
  parent_phone?: string;
  alternate_phone?: string;
  alternate_email?: string;
  address_data?: Record<string, any>;
  address_block?: StudentAddressBlock;
  is_active: boolean;
  enrollment_count?: number;
  lead_status?: string;
  lead_owner?: string;
  course?: string;
  course_name?: string;
  course_total_fee?: string | number | null;
  your_commission?: string | number | null;
  net_payable?: string | number | null;
  sub_course?: string;
  data_subject_consent?: Record<string, unknown>;
  academic_histories?: StudentAcademicHistory[];
  documents?: StudentDoc[];
  // Demographic fields
  category?: string;
  employment_status?: string;
  marital_status?: string;
  religion?: string;
  abc_id?: string;
  deb_id?: string;
  receipt_s3_url?: string;
  admission_type?: string;
  admission_semester?: string;
  created_at: string;
}

export interface StudentAcademicHistory {
  id: string;
  student: string;
  qualification: string;
  examination?: string;
  institution: string;
  board_university: string;
  year_of_passing: number;
  score_type: string;
  score_value: string;
  percentage_marks?: string;
  result?: string;
  subject_stream?: string;
  created_at?: string;
}

export interface StudentDoc {
  id: string;
  student: string;
  academic_history?: string;
  doc_category: string;
  title: string;
  s3_object_uri: string;
  file_size_bytes: number;
  mime_type: string;
  status: string;
  rejection_reason?: string;
  verified_by?: string;
  verified_at?: string;
  created_at?: string;
}

export interface Enrollment {
  id: string;
  sub_center: string;
  student: string;
  student_name?: string;
  course: string;
  course_name?: string;
  university_name?: string;
  session: string;
  session_name?: string;
  status: string;
  admission_type?: string;
  admission_number?: string;
  registration_number?: string;
  next_valid_statuses?: string[];
  enrollment_number?: string;
  notes?: string;
  created_at: string;
}

export interface IntakeSession {
  id: string;
  session_name: string;
  start_date: string;
  end_date?: string;
  is_active: boolean;
  is_fresh_allowed: boolean;
}

export interface RuleConfiguration {
  id: string;
  rule_name: string;
  description?: string;
  conditions: Record<string, unknown>;
  priority: number;
  is_active: boolean;
}

export interface PaymentLedger {
  id: string;
  enrollment: string;
  student_name?: string;
  course_name?: string;
  sub_center_code?: string;
  amount_paid: string;
  transaction_ref: string;
  status: string;
  gateway: string;
  created_at: string;
}

export interface LeadIngestionLog {
  id: string;
  source: string;
  leadgen_id: string;
  raw_payload: Record<string, unknown>;
  normalized_data: Record<string, unknown>;
  status: string;
  error_msg?: string;
  campaign_id?: string;
  assigned_sub_center?: string;
  converted_student?: string;
  created_at: string;
}

export interface UserProfile {
  user_id: number;
  username: string;
  email: string;
  role: 'super_admin' | 'academic_head' | 'counselor' | 'finance';
  sub_center_id: string | null;
  sub_center_code?: string;
}

function qs(params?: Record<string, string>): string {
  if (!params) return '';
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== '');
  if (entries.length === 0) return '';
  return '?' + new URLSearchParams(Object.fromEntries(entries)).toString();
}

// ──────────────── Auth ────────────────
export const auth = {
  login: (username: string, password: string, otp: string = '123456') =>
    apiFetch<{ token: string }>('/auth/token', {
      method: 'POST',
      body: JSON.stringify({ username, password, otp }),
    }),
  profile: () => apiFetch<UserProfile>('/auth/profile'),
  verifyMfa: (otp: string) =>
    apiFetch<{ status: string; method: string }>('/auth/mfa/verify', {
      method: 'POST',
      body: JSON.stringify({ otp }),
    }),
  changePassword: (old_password: string, new_password: string) =>
    apiFetch<{ detail: string }>('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify({ old_password, new_password }),
    }),
  logout: () => {
    setAuthToken(null);
    return Promise.resolve();
  },
};

// ──────────────── Module 1: Aggregator ────────────────
export const aggregator = {
  listUniversities: (params?: Record<string, string>) =>
    apiFetch<Paginated<University>>(`/universities${qs(params)}`),
  getUniversity: (id: string) => apiFetch<University>(`/universities/${id}`),
  createUniversity: (data: Partial<University>) =>
    apiFetch<University>('/universities', { method: 'POST', body: JSON.stringify(data) }),
  updateUniversity: (id: string, data: Partial<University>) =>
    apiFetch<University>(`/universities/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  listCourses: (params?: Record<string, string>) =>
    apiFetch<Paginated<Course>>(`/courses${qs(params)}`),
  getCourse: (id: string) => apiFetch<Course>(`/courses/${id}`),
  createCourse: (data: Partial<Course>) =>
    apiFetch<Course>('/courses', { method: 'POST', body: JSON.stringify(data) }),
  listFees: (courseId?: string) =>
    apiFetch<Paginated<FeeStructure>>(courseId ? `/fees?course=${courseId}` : '/fees'),
  createFee: (data: Partial<FeeStructure>) =>
    apiFetch<FeeStructure>('/fees', { method: 'POST', body: JSON.stringify(data) }),
  deleteUniversity: (id: string) =>
    apiFetch<void>(`/universities/${id}`, { method: 'DELETE' }),
  deleteCourse: (id: string) =>
    apiFetch<void>(`/courses/${id}`, { method: 'DELETE' }),
  deleteFee: (id: string) =>
    apiFetch<void>(`/fees/${id}`, { method: 'DELETE' }),
  // Digital Prospectus Library
  listProspectus: (params?: Record<string, string>) =>
    apiFetch<Paginated<UniversityDoc>>(`/prospectus${qs(params)}`),
  createProspectus: (formData: FormData) =>
    apiUpload<UniversityDoc>('/prospectus', formData),
  updateProspectus: (id: string, formData: FormData) =>
    apiUpload<UniversityDoc>(`/prospectus/${id}`, formData, 'PATCH'),
  deleteProspectus: (id: string) =>
    apiFetch<void>(`/prospectus/${id}`, { method: 'DELETE' }),
  downloadDoc: (id: string) =>
    apiFetch<{ url: string; ttl_seconds: number; filename: string }>(`/prospectus/${id}/download`),
};

// ──────────────── Module 2: B2B Portal ────────────────
export const partners = {
  listSubCenters: (params?: Record<string, string>) =>
    apiFetch<Paginated<SubCenter>>(`/sub-centers${qs(params)}`),
  createSubCenter: (data: Partial<SubCenter>) =>
    apiFetch<SubCenter>('/sub-centers', { method: 'POST', body: JSON.stringify(data) }),
  updateSubCenter: (id: string, data: Partial<SubCenter>) =>
    apiFetch<SubCenter>(`/sub-centers/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  listUsers: (params?: Record<string, string>) =>
    apiFetch<Paginated<SystemUser>>(`/users${qs(params)}`),
  deleteUser: (id: string) =>
    apiFetch<void>(`/users/${id}`, { method: 'DELETE' }),
};

export const admissions = {
  // Students
  listStudents: (params?: Record<string, string>) =>
    apiFetch<Paginated<Student>>(`/students${qs(params)}`),
  getStudent: (id: string) => apiFetch<Student>(`/students/${id}`),
  createStudent: (data: Record<string, unknown>) =>
    apiFetch<Student>('/students', { method: 'POST', body: JSON.stringify(data) }),
  updateStudent: (id: string, data: Record<string, unknown>) =>
    apiFetch<Student>(`/students/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  checkAadhar: (aadhar: string) =>
    apiFetch<{ exists: boolean }>(`/students/check-aadhar?aadhar=${aadhar}`),

  // Student Academic Histories
  listAcademicHistories: (params?: Record<string, string>) =>
    apiFetch<Paginated<StudentAcademicHistory>>(`/academic-histories${qs(params)}`),
  createAcademicHistory: (data: Partial<StudentAcademicHistory>) =>
    apiFetch<StudentAcademicHistory>('/academic-histories', { method: 'POST', body: JSON.stringify(data) }),
  updateAcademicHistory: (id: string, data: Partial<StudentAcademicHistory>) =>
    apiFetch<StudentAcademicHistory>(`/academic-histories/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteAcademicHistory: (id: string) =>
    apiFetch<void>(`/academic-histories/${id}`, { method: 'DELETE' }),
  // Shortcut: add academic history via student action endpoint
  createStudentAcademicHistory: (studentId: string, data: Partial<StudentAcademicHistory>) =>
    apiFetch<StudentAcademicHistory>(`/students/${studentId}/academic_histories`, { method: 'POST', body: JSON.stringify(data) }),

  // Student Documents
  listStudentDocs: (params?: Record<string, string>) =>
    apiFetch<Paginated<StudentDoc>>(`/students-docs${qs(params)}`),
  createStudentDoc: (data: Record<string, unknown>) =>
    apiFetch<StudentDoc>('/students-docs', { method: 'POST', body: JSON.stringify(data) }),
  uploadStudentDoc: (formData: FormData) =>
    apiUpload<StudentDoc>('/students-docs', formData),
  verifyStudentDoc: (id: string) =>
    apiFetch<StudentDoc>(`/students-docs/${id}/verify`, { method: 'POST' }),
  rejectStudentDoc: (id: string, reason: string) =>
    apiFetch<StudentDoc>(`/students-docs/${id}/reject`, { method: 'POST', body: JSON.stringify({ reason }) }),
  deleteStudentDoc: (id: string) =>
    apiFetch<void>(`/students-docs/${id}`, { method: 'DELETE' }),

  // System Users
  createSystemUser: (data: Record<string, unknown>) =>
    apiFetch<SystemUser>('/users', { method: 'POST', body: JSON.stringify(data) }),
  updateSystemUser: (id: string, data: Record<string, unknown>) =>
    apiFetch<SystemUser>(`/users/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),

  // Enrollments
  listEnrollments: (params?: Record<string, string>) =>
    apiFetch<Paginated<Enrollment>>(`/enrollments${qs(params)}`),
  getEnrollment: (id: string) => apiFetch<Enrollment>(`/enrollments/${id}`),
  createEnrollment: (data: Record<string, unknown>) =>
    apiFetch<Enrollment>('/enrollments', { method: 'POST', body: JSON.stringify(data) }),
  updateEnrollment: (id: string, data: Record<string, unknown>) =>
    apiFetch<Enrollment>(`/enrollments/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  transitionStatus: (id: string, status: string, extra?: Record<string, string>) =>
    apiFetch<Enrollment>(`/enrollments/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status, ...extra }),
    }),
  enrollmentTimeline: (id: string) =>
    apiFetch<Array<{ action_type: string; created_at: string; old_data: Record<string, unknown>; new_data: Record<string, unknown> }>>(`/enrollments/${id}/timeline`),
  getEnrollmentTimeline: (id: string) =>
    apiFetch<{ timeline: Array<{ action: string; timestamp: string; user_name?: string; old_data?: Record<string, any>; new_data?: Record<string, any>; notes?: string }> }>(`/enrollments/${id}/timeline`),

  // Lead Conversion
  convertLead: (leadId: string) =>
    apiFetch<Student>('/students/convert-lead', { method: 'POST', body: JSON.stringify({ lead_id: leadId }) }),
};

// ──────────────── Module 3: Business Logic ────────────────
export const rules = {
  listIntakeSessions: (params?: Record<string, string>) =>
    apiFetch<Paginated<IntakeSession>>(`/intake-sessions${qs(params)}`),
  createIntakeSession: (data: Partial<IntakeSession>) =>
    apiFetch<IntakeSession>('/intake-sessions', { method: 'POST', body: JSON.stringify(data) }),
  updateIntakeSession: (id: string, data: Partial<IntakeSession>) =>
    apiFetch<IntakeSession>(`/intake-sessions/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  listRulesConfigurations: (params?: Record<string, string>) =>
    apiFetch<Paginated<RuleConfiguration>>(`/rules/session-matrix${qs(params)}`),
  createRule: (data: any) =>
    apiFetch<RuleConfiguration>('/rules/session-matrix', { method: 'POST', body: JSON.stringify(data) }),
  updateRule: (id: string, data: any) =>
    apiFetch<RuleConfiguration>(`/rules/session-matrix/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteRule: (id: string) =>
    apiFetch<void>(`/rules/session-matrix/${id}`, { method: 'DELETE' }),
  validateEnrollment: (student: string, course: string, session: string) =>
    apiFetch<{ valid: boolean; reason?: string; suggested_session_id?: string | null; matched_rule?: string }>(
      '/rules/validate/',
      { method: 'POST', body: JSON.stringify({ student, course, session }) }
    ),
};

// ──────────────── Module 4: Finance ────────────────
export const finance = {
  listPayments: (params?: Record<string, string>) =>
    apiFetch<Paginated<PaymentLedger>>(`/payments${qs(params)}`),
  summary: () =>
    apiFetch<{ total_collected: string; total_pending: string; captured_count: number; pending_count: number }>('/payments/summary'),
  bySubCenter: () =>
    apiFetch<Array<{ sub_center__center_code: string; sub_center__name: string; total: string; count: number }>>('/payments/by_sub_center'),
  batchCheckout: (studentIds: string[]) =>
    apiFetch<{
      message: string;
      invoice_id: string;
      total_amount: string;
      gateway_redirect_url: string;
      line_items?: Array<{
        student_id: string;
        student_name: string;
        course_id: string;
        course_name: string;
        university_id: string;
        university_name: string;
        total_fee: string;
        university_share: string;
        sub_center_commission: string;
        rimit_commission: string;
        net_payable: string;
        university_share_percent: string;
        sub_center_commission_percent: string;
      }>;
    }>('/checkout/batch/', { method: 'POST', body: JSON.stringify({ student_ids: studentIds }) }),
  mockPayment: (enrollmentId: string, amount: string) =>
    apiFetch<{ message: string; ledger_id: string }>('/payments/mock_payment', { method: 'POST', body: JSON.stringify({ enrollment_id: enrollmentId, amount }) }),
};

// ──────────────── Support & Ticketing ────────────────
export const support = {
  listTickets: (params?: Record<string, string>) =>
    apiFetch<Paginated<Ticket>>(`/support/tickets${qs(params)}`),
  createTicket: (data: any) =>
    apiFetch<Ticket>('/support/tickets', { method: 'POST', body: JSON.stringify(data) }),
  addMessage: (id: string, message: string, is_internal: boolean = false) =>
    apiFetch<TicketMessage>(`/support/tickets/${id}/add_message`, {
      method: 'POST',
      body: JSON.stringify({ message, is_internal }),
    }),
};

// ──────────────── Notifications & Broadcast ────────────────
export const notifications = {
  listLogs: (params?: Record<string, string>) =>
    apiFetch<Paginated<NotificationLog>>(`/notifications/logs${qs(params)}`),
  broadcast: (data: { recipients: string[]; channel: string; template_id: string; context?: Record<string, string> }) =>
    apiFetch<{ task_id: string; queued: number }>('/notifications/broadcast/', { method: 'POST', body: JSON.stringify(data) }),
};

// ──────────────── Lead Ingestion Monitor ────────────────
export const leads = {
  list: (params?: Record<string, string>) =>
    apiFetch<Paginated<LeadIngestionLog>>(`/lead-ingestion-logs${qs(params)}`),
  get: (id: string) => apiFetch<LeadIngestionLog>(`/lead-ingestion-logs/${id}`),
};
