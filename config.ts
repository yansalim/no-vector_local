// API Configuration
const getApiBaseUrl = () => {
  // Use environment variable or default to localhost
  const viteApi = (import.meta as any).env?.VITE_API_BASE_URL as string | undefined;
  // Fallback to Next env for compatibility if present (guard access in browser)
  const nextApi = typeof process !== 'undefined' && (process as any)?.env
    ? ((process as any).env.NEXT_PUBLIC_API_BASE_URL as string | undefined)
    : undefined;
  return viteApi || nextApi || 'http://localhost:8000';
};

const apiBaseUrl = getApiBaseUrl();

// Debug logging in development
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  console.log('API Base URL:', apiBaseUrl);
}

const config = {
  apiBaseUrl,
};

export default config;