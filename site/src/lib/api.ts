const API_BASE = (import.meta.env.PUBLIC_API_URL ?? 'http://localhost:8000/api/v1').replace(/\/$/, '');

const ACCESS_KEY = 'bo_access';
const REFRESH_KEY = 'bo_refresh';

export function getToken(): string | null {
  return localStorage.getItem(ACCESS_KEY);
}

export function setTokens(access: string, refresh?: string): void {
  localStorage.setItem(ACCESS_KEY, access);
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

export function isAuthenticated(): boolean {
  return Boolean(getToken());
}

export function getCurrentUserEmail(): string | null {
  try {
    const payload = JSON.parse(atob(getToken()!.split('.')[1]));
    return payload.email ?? null;
  } catch {
    return null;
  }
}

async function refreshToken(): Promise<boolean> {
  const refresh = localStorage.getItem(REFRESH_KEY);
  if (!refresh) return false;
  try {
    const res = await fetch(`${API_BASE}/auth/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    setTokens(data.access);
    return true;
  } catch {
    return false;
  }
}

export async function apiFetch(
  path: string,
  opts: { method?: string; body?: unknown } = {}
): Promise<Response> {
  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (opts.body !== undefined) headers['Content-Type'] = 'application/json';

  let res = await fetch(`${API_BASE}${path}`, {
    method: opts.method ?? 'GET',
    headers,
    body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
  });

  if (res.status === 401 && getToken()) {
    const ok = await refreshToken();
    if (ok) {
      headers['Authorization'] = `Bearer ${getToken()}`;
      res = await fetch(`${API_BASE}${path}`, {
        method: opts.method ?? 'GET',
        headers,
        body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
      });
    } else {
      clearTokens();
    }
  }
  return res;
}

export async function login(email: string, password: string): Promise<void> {
  const res = await apiFetch('/auth/login/', {
    method: 'POST',
    body: { email, password },
  });
  if (!res.ok) {
    let detail = 'Autentificare eșuată.';
    try {
      const data = await res.json();
      detail = data.detail ?? data.message ?? JSON.stringify(data);
    } catch {
      /* keep default */
    }
    throw new Error(detail);
  }
  const data = await res.json();
  setTokens(data.access, data.refresh);
}

export async function signup(email: string, password: string): Promise<void> {
  const res = await apiFetch('/auth/signup/', {
    method: 'POST',
    body: { email, password, password2: password },
  });
  if (!res.ok) {
    let detail = 'Înregistrarea a eșuat.';
    try {
      const data = await res.json();
      detail = data.email?.[0] ?? data.password?.[0] ?? JSON.stringify(data);
    } catch {
      /* keep default */
    }
    throw new Error(detail);
  }
  const data = await res.json();
  if (data.access) setTokens(data.access, data.refresh);
}

export async function getLesson(slug: string): Promise<{ is_unlocked: boolean } | null> {
  const res = await apiFetch(`/lessons/${slug}/`);
  if (res.status === 403 || res.status === 401) return { is_unlocked: false };
  if (!res.ok) return null;
  return res.json();
}

export async function getLessonContent(slug: string): Promise<string | null> {
  const res = await apiFetch(`/lessons/${slug}/content/`);
  if (res.status === 403 || res.status === 401) return null;
  if (!res.ok) return null;
  const data = await res.json();
  return data.content ?? null;
}

export async function checkPaymentStatus(sessionId: string): Promise<boolean> {
  const res = await apiFetch(`/payments/status/?session_id=${encodeURIComponent(sessionId)}`);
  if (!res.ok) return false;
  const data = await res.json();
  return Boolean(data.paid);
}

export async function hasPurchased(): Promise<boolean> {
  const res = await apiFetch('/payments/');
  if (!res.ok) return false;
  const payments = await res.json();
  return Array.isArray(payments) && payments.some((p) => p.status === 'paid');
}

export async function requestPasswordReset(email: string): Promise<void> {
  const res = await apiFetch('/auth/password/reset/', {
    method: 'POST',
    body: { email },
  });
  if (!res.ok) {
    let detail = 'Nu am putut trimite link-ul de resetare.';
    try {
      const data = await res.json();
      detail = data.detail ?? data.email?.[0] ?? JSON.stringify(data);
    } catch {
      /* keep default */
    }
    throw new Error(detail);
  }
}

export async function confirmPasswordReset(token: string, password: string): Promise<void> {
  const res = await apiFetch('/auth/password/reset/confirm/', {
    method: 'POST',
    body: { token, new_password: password, new_password2: password },
  });
  if (!res.ok) {
    let detail = 'Resetarea a eșuat. Verifică link-ul și încearcă din nou.';
    try {
      const data = await res.json();
      detail = data.detail ?? data.token?.[0] ?? data.new_password?.[0] ?? JSON.stringify(data);
    } catch {
      /* keep default */
    }
    throw new Error(detail);
  }
}

export async function createCheckout(): Promise<string> {
  const res = await apiFetch('/payments/checkout/', {
    method: 'POST',
    body: { course: 'bani-online' },
  });
  if (!res.ok) {
    let detail = 'Nu am putut iniția plata.';
    try {
      const data = await res.json();
      detail = data.detail ?? JSON.stringify(data);
    } catch {
      /* keep default */
    }
    throw new Error(detail);
  }
  const data = await res.json();
  return data.checkout_url;
}

export async function startCheckout(): Promise<void> {
  if (!isAuthenticated()) {
    const next = encodeURIComponent(window.location.pathname + window.location.search);
    window.location.href = `/login?next=${next}`;
    return;
  }
  const url = await createCheckout();
  window.location.href = url;
}
