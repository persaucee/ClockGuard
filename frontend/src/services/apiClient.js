const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || '';
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

const defaultHeaders = {
  'Content-Type': 'application/json',
};

export const apiRequest = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };
  
  try {
    const response = await fetch(url, config);
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API Request Failed:', error);
    throw error;
  }
};

export const api = {
  auth: {
    login: async (credentials) => {
      const url = `${API_BASE_URL}/auth/login`;
      
      const config = {
        method: 'POST',
        headers: {
          ...defaultHeaders,
        },
        credentials: 'include',
        body: JSON.stringify(credentials),
      };
      
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Login failed' }));
        throw new Error(errorData.message || errorData.detail || 'Login failed');
      }
      
      return await response.json();
    },


    verify2FA: async (temp_token, code) => {
      const url = `${API_BASE_URL}/auth/verify-2fa`;

      const config = {
        method: 'POST',
        headers: {
          ...defaultHeaders,
        },
        credentials: 'include',
        body: JSON.stringify({ temp_token, code }),
      };

      const response = await fetch(url, config);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: '2FA verification failed' }));
        throw new Error(errorData.message || errorData.detail || '2FA verification failed');
      }

      return await response.json();
    },


    initiate2FASetup: async () => {
      const url = `${API_BASE_URL}/auth/2fa/setup/initiate`;

      const config = {
        method: 'POST',
        headers: {
          ...defaultHeaders,
        },
        credentials: 'include',
      };

      const response = await fetch(url, config);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Failed to initiate 2FA setup' }));
        throw new Error(errorData.message || errorData.detail || 'Failed to initiate 2FA setup');
      }

      return await response.json();
    },

    confirm2FASetup: async (code) => {
      const url = `${API_BASE_URL}/auth/2fa/setup/confirm`;

      const config = {
        method: 'POST',
        headers: {
          ...defaultHeaders,
        },
        credentials: 'include',
        body: JSON.stringify({ code }),
      };

      const response = await fetch(url, config);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Failed to confirm 2FA setup' }));
        throw new Error(errorData.message || errorData.detail || 'Failed to confirm 2FA setup');
      }

      return await response.json();
    },

    disable2FA: async () => {
      const url = `${API_BASE_URL}/auth/2fa/disable`;

      const config = {
        method: 'POST',
        headers: {
          ...defaultHeaders,
        },
        credentials: 'include',
      };

      const response = await fetch(url, config);

      if (!response.ok) {
        const errorData = await response
          .json()
          .catch(() => ({ message: 'Failed to disable 2FA' }));
        throw new Error(
          errorData.message || errorData.detail || 'Failed to disable 2FA'
        );
      }

      return await response.json();
    },

    getMe: async () => {
      const url = `${API_BASE_URL}/auth/me`;

      const config = {
        method: 'GET',
        headers: {
          ...defaultHeaders,
        },
        credentials: 'include',
      };

      const response = await fetch(url, config);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Failed to fetch user info' }));
        throw new Error(errorData.message || errorData.detail || 'Failed to fetch user info');
      }

      return await response.json();
    },

    logout: async () => {
      console.log('Logout endpoint not yet implemented');
      return { success: false, message: 'Not implemented' };
    },
  },
  
  users: {
    getAll: async () => {
      console.log('Get users endpoint not yet implemented');
      return [];
    },
  },
  
  attendance: {
    getLogs: async () => {
      const url = `${API_BASE_URL}/attendance/logs`;
      
      const config = {
        method: 'GET',
        headers: {
          ...defaultHeaders,
        },
        credentials: 'include',
      };
      
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Failed to fetch attendance logs' }));
        throw new Error(errorData.message || 'Failed to fetch attendance logs');
      }
      
      return await response.json();
    },
  },
  
  employees: {
    getAll: async () => {
      const url = `${API_BASE_URL}/employees`;
      
      const config = {
        method: 'GET',
        headers: {
          ...defaultHeaders,
        },
        credentials: 'include',
      };
      
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Failed to fetch employees' }));
        throw new Error(errorData.message || 'Failed to fetch employees');
      }
      
      const result = await response.json();
      
      if (Array.isArray(result)) {
        return result;
      }
      
      if (result.data && Array.isArray(result.data)) {
        return result.data;
      }
      
      if (result.employees && Array.isArray(result.employees)) {
        return result.employees;
      }
      
      console.warn('Unexpected response shape from GET /employees:', result);
      return [];
    },
    update: async (employeeId, data) => {
      const url = `${API_BASE_URL}/employees/${employeeId}`;
      
      const config = {
        method: 'PUT',
        headers: {
          ...defaultHeaders,
        },
        credentials: 'include',
        body: JSON.stringify(data),
      };
      
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Failed to update employee' }));
        throw new Error(errorData.message || 'Failed to update employee');
      }
      
      return await response.json();
    },
  },
  
  payroll: {
    getEmployeeSessions: async (employeeId) => {
      const url = `${API_BASE_URL}/payroll/${employeeId}`;
      
      const config = {
        method: 'GET',
        headers: {
          ...defaultHeaders,
        },
        credentials: 'include',
      };
      
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Failed to fetch payroll sessions' }));
        throw new Error(errorData.message || 'Failed to fetch payroll sessions');
      }
      
      const result = await response.json();
      return result.data || [];
    },
    updateSession: async (sessionId, data) => {
      const url = `${API_BASE_URL}/payroll/${sessionId}`;
      
      const config = {
        method: 'PUT',
        headers: {
          ...defaultHeaders,
        },
        credentials: 'include',
        body: JSON.stringify(data),
      };
      
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Failed to update payroll session' }));
        throw new Error(errorData.message || 'Failed to update payroll session');
      }
      
      const result = await response.json();
      return result.data || result;
    },
    processPayroll: async (startDate, endDate) => {
      const url = `${API_BASE_URL}/payroll/process?start_date=${startDate}&end_date=${endDate}`;
      
      const config = {
        method: 'POST',
        headers: {
          ...defaultHeaders,
        },
        credentials: 'include',
      };
      
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Failed to process payroll' }));
        throw new Error(errorData.message || 'Failed to process payroll');
      }
      
      return await response.json();
    },
  },
};

export const supabaseConfig = {
  url: SUPABASE_URL,
  anonKey: SUPABASE_ANON_KEY,
};

export default api;
