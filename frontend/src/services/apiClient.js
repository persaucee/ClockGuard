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
        throw new Error(errorData.message || 'Login failed');
      }
      
      return await response.json();
    },
    logout: async () => {
      return { success: false, message: 'Not implemented' };
    },
  },

  users: {
    getAll: async () => {
      return [];
    },
  },
  
  attendance: {
    getStatus: async () => {
      const url = `${API_BASE_URL}/attendance/status`;

      const response = await fetch(url, {
        method: 'GET',
        headers: { ...defaultHeaders },
        credentials: 'include',
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Failed to fetch attendance status' }));
        throw new Error(errorData.message || 'Failed to fetch attendance status');
      }

      return await response.json();
    },

    getRecentLogs: async (pageSize = 50) => {
      const url = `${API_BASE_URL}/attendance/clock-logs?page_size=${pageSize}`;

      const response = await fetch(url, {
        method: 'GET',
        headers: { ...defaultHeaders },
        credentials: 'include',
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Failed to fetch recent logs' }));
        throw new Error(errorData.message || 'Failed to fetch recent logs');
      }

      const result = await response.json();
      return Array.isArray(result) ? result : (result.data || []);
    },

    getLogs: async () => {
      const url = `${API_BASE_URL}/attendance/clock-logs`;
      
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

    getAllLogs: async () => {
      const PAGE_SIZE = 100;
      const allLogs = [];
      let page = 1;

      while (true) {
        const url = `${API_BASE_URL}/attendance/clock-logs?page=${page}&limit=${PAGE_SIZE}`;

        const response = await fetch(url, {
          method: 'GET',
          headers: { ...defaultHeaders },
          credentials: 'include',
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ message: 'Failed to fetch attendance logs' }));
          throw new Error(errorData.message || 'Failed to fetch attendance logs');
        }

        const result = await response.json();
        const pageData = Array.isArray(result) ? result : (result.data || []);

        allLogs.push(...pageData);

        // Stop when the page is short or we've hit the declared total.
        const total = result.total ?? result.count ?? null;
        if (total !== null ? allLogs.length >= total : pageData.length < PAGE_SIZE) {
          break;
        }

        page++;
      }

      return allLogs;
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

    getAllEmployeeSessions: async (employeeId) => {
      const PAGE_SIZE = 100;
      const allSessions = [];
      let page = 1;

      while (true) {
        const url = `${API_BASE_URL}/payroll/${employeeId}?page=${page}&limit=${PAGE_SIZE}`;

        const response = await fetch(url, {
          method: 'GET',
          headers: { ...defaultHeaders },
          credentials: 'include',
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ message: 'Failed to fetch payroll sessions' }));
          throw new Error(errorData.message || 'Failed to fetch payroll sessions');
        }

        const result = await response.json();
        const pageData = Array.isArray(result) ? result : (result.data || []);

        allSessions.push(...pageData);

        const total = result.total ?? result.count ?? null;
        if (total !== null ? allSessions.length >= total : pageData.length < PAGE_SIZE) {
          break;
        }

        page++;
      }

      return allSessions;
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
