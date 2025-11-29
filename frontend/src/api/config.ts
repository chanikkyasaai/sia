// API Configuration
export const API_CONFIG = {
  BASE_URL: '/api', // Use proxy instead of direct API URL
  BUSINESS_ID: 2, // Static business ID for now
  TIMEOUT: 30000, // 30 seconds timeout
};

export const API_ENDPOINTS = {
  // Customer endpoints
  CUSTOMERS: '/customers',
  
  // Products endpoints
  PRODUCTS: '/products',
  
  // Inventory (quantity tracking) endpoints
  INVENTORY: '/inventory',
  
  // Other endpoints (to be implemented)
  EXPENSES: '/expenses',
  SALES: '/transactions',
};

// Helper function to create full URL
export const createApiUrl = (endpoint: string): string => {
  return `${API_CONFIG.BASE_URL}${endpoint}`;
};

// Custom error class for API errors
export class ApiError extends Error {
  status?: number;
  
  constructor(message: string, status?: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}