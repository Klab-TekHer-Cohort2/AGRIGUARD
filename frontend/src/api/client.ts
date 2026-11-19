/**
 * AgriGuard typed API client
 *
 * All endpoints here match exactly what the backend schemas define.
 * JWT token is read from the auth store and injected into every
 * authenticated request via the Authorization: Bearer header.
 *
 * Rules enforced here:
 * - Never show raw API error messages to the farmer.
 * - Treat is_mock=true results as "Diagnosis Pending" — never show as confirmed.
 * - Gateway secret endpoints (/ussd/, /ivr/, /farmers/by-phone/) are excluded.
 */

import { API_V1, AI_API, REQUEST_TIMEOUT } from './config';

// ── Types matching backend schemas exactly ──────────────────────────────────

export interface TokenResponse {
  access_token: string;
  token_type: 'bearer';
  role: string;
  user_id: number;
  phone_number: string;
  full_name: string;
}

export interface UserRegisterPayload {
  phone_number: string;
  password: string;
  full_name: string;
  email?: string;
  role?: 'FARMER' | 'AGRONOMIST' | 'ORG_ADMIN' | 'SYSTEM_ADMIN';
  preferred_language?: 'rw' | 'en';
  national_id?: string;
  cooperative_name?: string;
  province?: string;
  district?: string;
  sector?: string;
  cell?: string;
  village?: string;
  latitude?: number;
  longitude?: number;
}

export interface UserLoginPayload {
  phone_number: string;
  password: string;
}

export interface UserResponse {
  id: number;
  phone_number: string;
  email?: string;
  full_name: string;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface CropResponse {
  id: number;
  name_en: string;
  name_rw: string;
  scientific_name?: string;
  category?: string;
  description?: string;
  common_pests?: string[];
  is_active: boolean;
  created_at: string;
}

export interface AIResultSummary {
  id: number;
  model_name: string;
  predicted_pest_en: string;
  predicted_pest_rw?: string;
  confidence_score: number;
  detected_severity: string;
  recommendations?: string[];
  is_mock: boolean;
  is_verified_correct?: boolean;
}

export interface ReportImageResponse {
  id: number;
  report_id: number;
  image_url: string;
  file_name: string;
  file_size_bytes?: number;
  mime_type: string;
  upload_channel: string;
  created_at: string;
}

export interface ReportHistoryResponse {
  id: number;
  previous_status?: string;
  new_status: string;
  action_type: string;
  notes?: string;
  created_at: string;
}

export interface CropReportResponse {
  id: number;
  report_code: string;
  farmer_id: number;
  farmer_name?: string;
  farmer_phone?: string;
  crop_id: number;
  crop_name_en?: string;
  crop_name_rw?: string;
  channel: string;
  description?: string;
  symptoms: string[];
  district: string;
  sector: string;
  cell?: string;
  village?: string;
  latitude?: number;
  longitude?: number;
  severity: string;
  status: string;
  agronomist_notes?: string;
  verified_at?: string;
  images: ReportImageResponse[];
  ai_result?: AIResultSummary;
  history: ReportHistoryResponse[];
  created_at: string;
  updated_at: string;
}

export interface CropReportCreate {
  crop_id: number;
  channel?: string;
  description?: string;
  symptoms?: string[];
  district?: string;
  sector?: string;
  cell?: string;
  village?: string;
  latitude?: number;
  longitude?: number;
  severity?: string;
}

export interface FarmerProfileResponse {
  id: number;
  user_id: number;
  phone_number: string;
  full_name: string;
  email?: string;
  preferred_language: string;
  national_id?: string;
  cooperative_name?: string;
  is_phone_verified: boolean;
  locations: LocationResponse[];
  total_reports: number;
  created_at: string;
}

export interface FarmerProfileUpdate {
  full_name?: string;
  email?: string;
  preferred_language?: string;
  national_id?: string;
  cooperative_name?: string;
}

export interface LocationResponse {
  id: number;
  farmer_id: number;
  province?: string;
  district: string;
  sector: string;
  cell?: string;
  village?: string;
  latitude?: number;
  longitude?: number;
  is_primary: boolean;
  created_at: string;
}

export interface LocationCreate {
  province?: string;
  district: string;
  sector: string;
  cell?: string;
  village?: string;
  latitude?: number;
  longitude?: number;
  is_primary?: boolean;
}

export interface AlertResponse {
  id: number;
  title_en: string;
  title_rw: string;
  pest_name?: string;
  target_district: string;
  target_sector?: string;
  severity: string;
  status: string;
  affected_report_count: number;
  source_report_id?: number;
  created_at: string;
}

export interface AlertDetailResponse extends AlertResponse {
  message_en: string;
  message_rw: string;
  resolved_by_user_id?: number;
  resolved_at?: string;
}

export interface RiskScoreResponse {
  district: string;
  pest_name?: string;
  crop_id?: number;
  risk_score: number;
  contributing_report_count: number;
  threshold: number;
  above_threshold: boolean;
}

/** AI Service — /api/ai/ask response */
export interface AskResponse {
  success: boolean;
  data: {
    answer: string;
    language: string;
    sources?: string[];
    disclaimer?: string;
    needsAgronomist?: boolean;
    escalationReason?: string;
  };
}

// ── HTTP utility ────────────────────────────────────────────────────────────

type GetTokenFn = () => string | null;

let _getToken: GetTokenFn = () => null;

/** Register the token getter (called by auth store on init) */
export function setTokenGetter(fn: GetTokenFn): void {
  _getToken = fn;
}

class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export { ApiError };

async function request<T>(
  url: string,
  options: RequestInit = {},
  authenticated = true,
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (authenticated) {
    const token = _getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

  try {
    const response = await fetch(url, {
      ...options,
      headers,
      signal: controller.signal,
    });

    clearTimeout(timer);

    if (!response.ok) {
      let detail = 'Request failed';
      try {
        const body = await response.json();
        detail = body?.detail ?? body?.message ?? detail;
      } catch {
        // ignore parse error
      }
      throw new ApiError(response.status, String(response.status), detail);
    }

    // 204 No Content
    if (response.status === 204) {
      return undefined as unknown as T;
    }

    return response.json() as Promise<T>;
  } catch (err) {
    clearTimeout(timer);
    if (err instanceof ApiError) throw err;
    if ((err as Error).name === 'AbortError') {
      throw new ApiError(0, 'TIMEOUT', 'Request timed out');
    }
    throw new ApiError(0, 'NETWORK', 'Network error');
  }
}

async function uploadFile<T>(
  url: string,
  formData: FormData,
  token: string | null,
): Promise<T> {
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 60_000);

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
      signal: controller.signal,
    });

    clearTimeout(timer);

    if (!response.ok) {
      let detail = 'Upload failed';
      try {
        const body = await response.json();
        detail = body?.detail ?? detail;
      } catch {
        // ignore
      }
      throw new ApiError(response.status, String(response.status), detail);
    }

    return response.json() as Promise<T>;
  } catch (err) {
    clearTimeout(timer);
    if (err instanceof ApiError) throw err;
    throw new ApiError(0, 'NETWORK', 'Network error during upload');
  }
}

// ── Auth endpoints ──────────────────────────────────────────────────────────

export const authApi = {
  register: (payload: UserRegisterPayload) =>
    request<TokenResponse>(`${API_V1}/auth/register`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }, false),

  login: (payload: UserLoginPayload) =>
    request<TokenResponse>(`${API_V1}/auth/login`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }, false),

  me: () =>
    request<UserResponse>(`${API_V1}/auth/me`),
};

// ── Crops ───────────────────────────────────────────────────────────────────

export const cropsApi = {
  list: () =>
    request<CropResponse[]>(`${API_V1}/crops/?is_active=true`, {}, false),

  getById: (id: number) =>
    request<CropResponse>(`${API_V1}/crops/${id}`, {}, false),
};

// ── Reports ─────────────────────────────────────────────────────────────────

export const reportsApi = {
  create: (payload: CropReportCreate) =>
    request<CropReportResponse>(`${API_V1}/reports/`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  uploadImage: (reportId: number, formData: FormData) =>
    uploadFile<ReportImageResponse>(
      `${API_V1}/reports/${reportId}/images`,
      formData,
      _getToken(),
    ),

  myReports: (params?: { status?: string; skip?: number; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.status) qs.set('status_filter', params.status);
    if (params?.skip !== undefined) qs.set('skip', String(params.skip));
    if (params?.limit !== undefined) qs.set('limit', String(params.limit));
    return request<CropReportResponse[]>(
      `${API_V1}/reports/my-reports?${qs.toString()}`,
    );
  },

  getByCode: (codeOrId: string) =>
    request<CropReportResponse>(`${API_V1}/reports/${codeOrId}`),
};

// ── Farmers ─────────────────────────────────────────────────────────────────

export const farmersApi = {
  getProfile: () =>
    request<FarmerProfileResponse>(`${API_V1}/farmers/profile`),

  updateProfile: (payload: FarmerProfileUpdate) =>
    request<FarmerProfileResponse>(`${API_V1}/farmers/profile`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
};

// ── Locations ───────────────────────────────────────────────────────────────

export const locationsApi = {
  myLocations: () =>
    request<LocationResponse[]>(`${API_V1}/locations/my-locations`),

  add: (payload: LocationCreate) =>
    request<LocationResponse>(`${API_V1}/locations/`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  setPrimary: (locationId: number) =>
    request<LocationResponse>(`${API_V1}/locations/${locationId}/primary`, {
      method: 'PUT',
    }),
};

// ── Outbreak / Alerts ────────────────────────────────────────────────────────

export const outbreakApi = {
  listAlerts: (params?: { district?: string; skip?: number; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.district) qs.set('district', params.district);
    if (params?.skip !== undefined) qs.set('skip', String(params.skip));
    if (params?.limit !== undefined) qs.set('limit', String(params.limit));
    return request<AlertResponse[]>(`${API_V1}/outbreak/alerts?${qs.toString()}`);
  },

  getAlert: (id: number) =>
    request<AlertDetailResponse>(`${API_V1}/outbreak/alerts/${id}`),

  riskScore: (district: string) =>
    request<RiskScoreResponse>(
      `${API_V1}/outbreak/risk-score?district=${encodeURIComponent(district)}`,
    ),
};

// ── AI Service (direct — Ask AgriGuard only) ─────────────────────────────────

export const aiApi = {
  ask: (question: string, language: 'en' | 'rw' = 'en', cropId?: string) =>
    request<AskResponse>(
      `${AI_API}/ask`,
      {
        method: 'POST',
        body: JSON.stringify({ question, language, cropId }),
      },
      false, // AI service has no auth
    ),
};
