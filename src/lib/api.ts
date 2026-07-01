/**
 * RIMIT B2B Aggregator — API client.
 *
 * All requests go through the Caddy gateway with XTransformPort=8000
 * to reach the Django backend (in sandbox preview), OR through Next.js
 * rewrites (in local dev on port 3000).
 *
 * Note: Django routers use trailing_slash=False, so all paths are slash-free.
 */

const API_BASE = '/api/v1';
const TRANSFORM_PORT = '8000';

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
  // path may already contain query params (e.g., "?search=abc") — handle both cases.
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

// ──────────────── Types ────────────────
export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface University {
  id: string;
  name: string;
  state: string;
  accreditation?: string;
  description?: string;
  website?: string;
  is_active: boolean;
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
  total_fee?: number;
  fees?: FeeStructure[];
  created_at: string;
}

export interface FeeStructure {
  id: string;
  course: string;
  fee_type: string;
  amount: string;
  currency: string;
  is_active: boolean;
}

export interface UniversityDoc {
  id: string;
  university: string;
  doc_type: string;
  title: string;
  s3_object_uri: string;
  mime_type: string;
  is_public: boolean;
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
  parent_phone?: string;
  is_active: boolean;
  enrollment_count?: number;
  created_at: string;
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
  login: (username: string, password: string) =>
    apiFetch<{ token: string }>('/auth/token', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
  profile: () => apiFetch<UserProfile>('/auth/profile'),
  verifyMfa: (otp: string) =>
    apiFetch<{ status: string; method: string }>('/auth/mfa/verify', {
      method: 'POST',
      body: JSON.stringify({ otp }),
    }),
};

// ──────────────── Module 1: Aggregator ────────────────
export const aggregator = {
  listUniversities: (params?: Record<string, string>) =>
    apiFetch<Paginated<University>>(`/universities${qs(params)}`),
  getUniversity: (id: string) => apiFetch<University>(`/universities/${id}`),
  createUniversity: (data: Partial<University>) =>
    apiFetch<University>('/universities', { method: 'POST', body: JSON.stringify(data) }),
  listCourses: (params?: Record<string, string>) =>
    apiFetch<Paginated<Course>>(`/courses${qs(params)}`),
  getCourse: (id: string) => apiFetch<Course>(`/courses/${id}`),
  createCourse: (data: Partial<Course>) =>
    apiFetch<Course>('/courses', { method: 'POST', body: JSON.stringify(data) }),
  listFees: (courseId?: string) =>
    apiFetch<Paginated<FeeStructure>>(courseId ? `/fees?course=${courseId}` : '/fees'),
  createFee: (data: Partial<FeeStructure>) =>
    apiFetch<FeeStructure>('/fees', { method: 'POST', body: JSON.stringify(data) }),
  downloadDoc: (id: string) =>
    apiFetch<{ url: string; ttl_seconds: number; filename: string }>(`/prospectus/${id}/download`),
};

// ──────────────── Module 2: B2B Portal ────────────────
export const partners = {
  listSubCenters: (params?: Record<string, string>) =>
    apiFetch<Paginated<SubCenter>>(`/sub-centers${qs(params)}`),
  createSubCenter: (data: Partial<SubCenter>) =>
    apiFetch<SubCenter>('/sub-centers', { method: 'POST', body: JSON.stringify(data) }),
  listUsers: () => apiFetch<Paginated<unknown>>('/users'),
};

export const admissions = {
  listStudents: (params?: Record<string, string>) =>
    apiFetch<Paginated<Student>>(`/students${qs(params)}`),
  getStudent: (id: string) => apiFetch<Student>(`/students/${id}`),
  createStudent: (data: Record<string, unknown>) =>
    apiFetch<Student>('/students', { method: 'POST', body: JSON.stringify(data) }),
  listEnrollments: (params?: Record<string, string>) =>
    apiFetch<Paginated<Enrollment>>(`/enrollments${qs(params)}`),
  getEnrollment: (id: string) => apiFetch<Enrollment>(`/enrollments/${id}`),
  createEnrollment: (data: Record<string, unknown>) =>
    apiFetch<Enrollment>('/enrollments', { method: 'POST', body: JSON.stringify(data) }),
  transitionStatus: (id: string, status: string, notes?: string) =>
    apiFetch<Enrollment>(`/enrollments/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status, notes }),
    }),
};

// ──────────────── Module 3: Business Logic ────────────────
export const rules = {
  listIntakeSessions: (params?: Record<string, string>) =>
    apiFetch<Paginated<IntakeSession>>(`/intake-sessions${qs(params)}`),
  createIntakeSession: (data: Partial<IntakeSession>) =>
    apiFetch<IntakeSession>('/intake-sessions', { method: 'POST', body: JSON.stringify(data) }),
  validateEnrollment: (student: string, course: string, session: string) =>
    apiFetch<{ valid: boolean; reason?: string; suggested_session_id?: string | null; matched_rule?: string }>(
      '/rules/validate',
      { method: 'POST', body: JSON.stringify({ student, course, session }) }
    ),
};

// ──────────────── Module 4: Finance + Notifications ────────────────
export const finance = {
  listPayments: (params?: Record<string, string>) =>
    apiFetch<Paginated<PaymentLedger>>(`/payments${qs(params)}`),
  summary: () =>
    apiFetch<{ total_collected: string; total_pending: string; captured_count: number; pending_count: number }>('/payments/summary'),
};
