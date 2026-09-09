const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

async function fetchWithAuth(url: string, options: RequestInit = {}) {
  // TODO: Get token from session/local storage
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  
  const headers = new Headers(options.headers);
  headers.set('Content-Type', 'application/json');
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.detail || `HTTP error! status: ${response.status}`);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export const apiClient = {
  get: <T>(url: string) => fetchWithAuth(url, { method: 'GET' }) as Promise<T>,
  post: <T>(url: string, body: any) => fetchWithAuth(url, { method: 'POST', body: JSON.stringify(body) }) as Promise<T>,
  put: <T>(url: string, body: any) => fetchWithAuth(url, { method: 'PUT', body: JSON.stringify(body) }) as Promise<T>,
  delete: <T>(url: string) => fetchWithAuth(url, { method: 'DELETE' }) as Promise<T>,
};
