// API configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001/api';

// HTTP client class
class HTTPClient {
  constructor(baseURL) {
    this.baseURL = baseURL;
    this.defaultHeaders = {
      'Content-Type': 'application/json'
    };
  }

  // Get authorization header
  getAuthHeader() {
    const token = localStorage.getItem('accessToken');
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  // Make HTTP request
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        ...this.defaultHeaders,
        ...this.getAuthHeader(),
        ...options.headers
      },
      ...options
    };

    try {
      const response = await fetch(url, config);
      
      // Handle different response types
      const contentType = response.headers.get('content-type');
      let data;
      
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        data = await response.text();
      }

      // Handle HTTP errors
      if (!response.ok) {
        const error = new Error(data.message || data.error || `HTTP ${response.status}`);
        error.status = response.status;
        error.code = data.code;
        error.details = data.details;
        throw error;
      }

      return data;
    } catch (error) {
      // Handle network errors
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new Error('Network error: Unable to connect to server');
      }
      
      // Handle token expiration
      if (error.status === 401 && error.code === 'TOKEN_EXPIRED') {
        try {
          await this.refreshToken();
          // Retry the original request
          return this.request(endpoint, options);
        } catch (refreshError) {
          // Refresh failed, redirect to login
          this.handleAuthError();
          throw refreshError;
        }
      }

      throw error;
    }
  }

  // Refresh access token
  async refreshToken() {
    const refreshToken = localStorage.getItem('refreshToken');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const response = await fetch(`${this.baseURL}/auth/refresh`, {
        method: 'POST',
        headers: this.defaultHeaders,
        body: JSON.stringify({ refreshToken })
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const data = await response.json();
      localStorage.setItem('accessToken', data.tokens.accessToken);
      
      return data.tokens.accessToken;
    } catch (error) {
      this.handleAuthError();
      throw error;
    }
  }

  // Handle authentication errors
  handleAuthError() {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('currentOrganizationId');
    
    // Redirect to login if not already there
    if (window.location.pathname !== '/login') {
      window.location.href = '/login';
    }
  }

  // HTTP methods
  async get(endpoint, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const url = queryString ? `${endpoint}?${queryString}` : endpoint;
    return this.request(url, { method: 'GET' });
  }

  async post(endpoint, data = {}) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async put(endpoint, data = {}) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  async patch(endpoint, data = {}) {
    return this.request(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(data)
    });
  }

  async delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }

  // Upload file
  async upload(endpoint, file, additionalData = {}) {
    const formData = new FormData();
    formData.append('file', file);
    
    Object.keys(additionalData).forEach(key => {
      formData.append(key, additionalData[key]);
    });

    return this.request(endpoint, {
      method: 'POST',
      headers: {
        ...this.getAuthHeader()
        // Don't set Content-Type for FormData, let browser set it
      },
      body: formData
    });
  }
}

// Create HTTP client instance
const httpClient = new HTTPClient(API_BASE_URL);

// Authentication API
export const authAPI = {
  login: (email, password, rememberMe = false) =>
    httpClient.post('/auth/login', { email, password, rememberMe }),

  register: (userData) =>
    httpClient.post('/auth/register', userData),

  logout: () =>
    httpClient.post('/auth/logout'),

  refreshToken: (refreshToken) =>
    httpClient.post('/auth/refresh', { refreshToken }),

  getMe: () =>
    httpClient.get('/auth/me'),

  forgotPassword: (email) =>
    httpClient.post('/auth/forgot-password', { email }),

  resetPassword: (token, password) =>
    httpClient.post('/auth/reset-password', { token, password }),

  verifyEmail: (token) =>
    httpClient.get(`/auth/verify-email?token=${token}`),

  updateProfile: (userData) =>
    httpClient.put('/auth/profile', userData)
};

// Organization API
export const organizationAPI = {
  getUserOrganizations: () =>
    httpClient.get('/auth/me'),

  getOrganization: (organizationId) =>
    httpClient.get(`/organizations/${organizationId}`),

  updateOrganization: (organizationId, updates) =>
    httpClient.put(`/organizations/${organizationId}`, updates),

  createOrganization: (organizationData) =>
    httpClient.post('/organizations', organizationData),

  inviteUser: (organizationId, email, role) =>
    httpClient.post(`/organizations/${organizationId}/invite`, { email, role }),

  getOrganizationMembers: (organizationId) =>
    httpClient.get(`/organizations/${organizationId}/members`),

  updateMemberRole: (organizationId, userId, role) =>
    httpClient.put(`/organizations/${organizationId}/members/${userId}`, { role }),

  removeMember: (organizationId, userId) =>
    httpClient.delete(`/organizations/${organizationId}/members/${userId}`)
};

// Dashboard API
export const dashboardAPI = {
  getOverview: (organizationId) =>
    httpClient.get(`/dashboard/${organizationId}/overview`),

  getMetrics: (organizationId, params = {}) =>
    httpClient.get(`/dashboard/${organizationId}/metrics`, params),

  createMetric: (organizationId, metricData) =>
    httpClient.post(`/dashboard/${organizationId}/metrics`, metricData),

  getWidgets: (organizationId) =>
    httpClient.get(`/dashboard/${organizationId}/widgets`),

  createWidget: (organizationId, widgetData) =>
    httpClient.post(`/dashboard/${organizationId}/widgets`, widgetData),

  updateWidget: (organizationId, widgetId, updates) =>
    httpClient.put(`/dashboard/${organizationId}/widgets/${widgetId}`, updates),

  deleteWidget: (organizationId, widgetId) =>
    httpClient.delete(`/dashboard/${organizationId}/widgets/${widgetId}`)
};

// A.M. Consulting API
export const amConsultingAPI = {
  getConflicts: (organizationId, params = {}) =>
    httpClient.get(`/am-consulting/${organizationId}/conflicts`, params),

  getConflict: (organizationId, conflictId) =>
    httpClient.get(`/am-consulting/${organizationId}/conflicts/${conflictId}`),

  createConflict: (organizationId, conflictData) =>
    httpClient.post(`/am-consulting/${organizationId}/conflicts`, conflictData),

  updateConflict: (organizationId, conflictId, updates) =>
    httpClient.put(`/am-consulting/${organizationId}/conflicts/${conflictId}`, updates),

  getPractitioners: (organizationId) =>
    httpClient.get(`/am-consulting/${organizationId}/practitioners`),

  getRevenue: (organizationId, params = {}) =>
    httpClient.get(`/am-consulting/${organizationId}/revenue`, params)
};

// The 7 Space API
export const sevenSpaceAPI = {
  getExhibitions: (organizationId, params = {}) =>
    httpClient.get(`/seven-space/${organizationId}/exhibitions`, params),

  getExhibition: (organizationId, exhibitionId) =>
    httpClient.get(`/seven-space/${organizationId}/exhibitions/${exhibitionId}`),

  createExhibition: (organizationId, exhibitionData) =>
    httpClient.post(`/seven-space/${organizationId}/exhibitions`, exhibitionData),

  getWellnessPrograms: (organizationId) =>
    httpClient.get(`/seven-space/${organizationId}/wellness-programs`),

  getEvents: (organizationId, params = {}) =>
    httpClient.get(`/seven-space/${organizationId}/events`, params),

  getVisitorAnalytics: (organizationId, params = {}) =>
    httpClient.get(`/seven-space/${organizationId}/visitors`, params)
};

// HigherSelf Network API
export const higherSelfAPI = {
  getCommunityMembers: (organizationId, params = {}) =>
    httpClient.get(`/higherself/${organizationId}/members`, params),

  getPlatformUsage: (organizationId, params = {}) =>
    httpClient.get(`/higherself/${organizationId}/usage`, params),

  getNetworkMetrics: (organizationId, params = {}) =>
    httpClient.get(`/higherself/${organizationId}/metrics`, params),

  getIntegrationHealth: (organizationId) =>
    httpClient.get(`/higherself/${organizationId}/integrations/health`)
};

// Integrations API
export const integrationsAPI = {
  getIntegrations: (organizationId) =>
    httpClient.get(`/integrations/${organizationId}`),

  getIntegration: (organizationId, integrationId) =>
    httpClient.get(`/integrations/${organizationId}/${integrationId}`),

  createIntegration: (organizationId, integrationData) =>
    httpClient.post(`/integrations/${organizationId}`, integrationData),

  updateIntegration: (organizationId, integrationId, updates) =>
    httpClient.put(`/integrations/${organizationId}/${integrationId}`, updates),

  deleteIntegration: (organizationId, integrationId) =>
    httpClient.delete(`/integrations/${organizationId}/${integrationId}`),

  testIntegration: (organizationId, integrationId) =>
    httpClient.post(`/integrations/${organizationId}/${integrationId}/test`),

  syncIntegration: (organizationId, integrationId) =>
    httpClient.post(`/integrations/${organizationId}/${integrationId}/sync`)
};

// Monitoring API
export const monitoringAPI = {
  getSystemHealth: () =>
    httpClient.get('/monitoring/health'),

  getMetrics: (params = {}) =>
    httpClient.get('/monitoring/metrics', params),

  getAlerts: (organizationId, params = {}) =>
    httpClient.get(`/monitoring/${organizationId}/alerts`, params),

  createAlert: (organizationId, alertData) =>
    httpClient.post(`/monitoring/${organizationId}/alerts`, alertData),

  updateAlert: (organizationId, alertId, updates) =>
    httpClient.put(`/monitoring/${organizationId}/alerts/${alertId}`, updates),

  deleteAlert: (organizationId, alertId) =>
    httpClient.delete(`/monitoring/${organizationId}/alerts/${alertId}`)
};

// Utility functions
export const apiUtils = {
  // Format error message for display
  formatError: (error) => {
    if (typeof error === 'string') return error;
    if (error.message) return error.message;
    if (error.error) return error.error;
    return 'An unexpected error occurred';
  },

  // Check if error is network related
  isNetworkError: (error) => {
    return error.message && error.message.includes('Network error');
  },

  // Check if error is authentication related
  isAuthError: (error) => {
    return error.status === 401 || error.code === 'TOKEN_EXPIRED' || error.code === 'INVALID_TOKEN';
  },

  // Check if error is permission related
  isPermissionError: (error) => {
    return error.status === 403;
  },

  // Check if error is validation related
  isValidationError: (error) => {
    return error.status === 400 && error.details;
  }
};

export default httpClient;

