import { API_CONFIG, API_ENDPOINTS, createApiUrl } from './config';
import { CustomerCreate, CustomerResponse } from './types';

// Base fetch function with error handling
async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = createApiUrl(endpoint);
  
  const defaultOptions: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...options.headers,
    },
    mode: 'cors',
    ...options,
  };

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.TIMEOUT);

    const response = await fetch(url, {
      ...defaultOptions,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = `HTTP ${response.status}`;
      
      try {
        const errorJson = JSON.parse(errorText);
        errorMessage = errorJson.message || errorJson.detail || errorMessage;
      } catch {
        errorMessage = errorText || errorMessage;
      }

      throw new ApiError(errorMessage, response.status);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        throw new ApiError('Request timeout');
      }
      if (error.message.includes('fetch')) {
        throw new ApiError('Unable to connect to server. Please check your connection.');
      }
      throw new ApiError(error.message);
    }
    
    throw new ApiError('Unknown error occurred');
  }
}

// Customer API functions
export const customerApi = {
  // Create a new customer
  async create(customerData: Omit<CustomerCreate, 'business_id'>): Promise<CustomerResponse> {
    const payload: CustomerCreate = {
      ...customerData,
      business_id: API_CONFIG.BUSINESS_ID,
    };

    return await apiFetch<CustomerResponse>(API_ENDPOINTS.CUSTOMERS, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // Get all customers for the business
  async getAll(): Promise<CustomerResponse[]> {
    const url = `${API_ENDPOINTS.CUSTOMERS}?business_id=${API_CONFIG.BUSINESS_ID}`;
    console.log('Fetching customers from:', createApiUrl(url));
    try {
      const result = await apiFetch<CustomerResponse[]>(url);
      console.log('Customers fetched successfully:', result);
      return result;
    } catch (error) {
      console.error('Error fetching customers:', error);
      throw error;
    }
  },

  // Get a single customer by ID
  async getById(id: number): Promise<CustomerResponse> {
    return await apiFetch<CustomerResponse>(`${API_ENDPOINTS.CUSTOMERS}/${id}`);
  },

  // Update a customer (for future implementation)
  async update(id: number, customerData: Partial<CustomerCreate>): Promise<CustomerResponse> {
    return await apiFetch<CustomerResponse>(`${API_ENDPOINTS.CUSTOMERS}/${id}`, {
      method: 'PUT',
      body: JSON.stringify(customerData),
    });
  },

  // Delete a customer (for future implementation)
  async delete(id: number): Promise<void> {
    await apiFetch<void>(`${API_ENDPOINTS.CUSTOMERS}/${id}`, {
      method: 'DELETE',
    });
  },
};

// Error class
export class ApiError extends Error {
  constructor(message: string, public status?: number, public details?: any) {
    super(message);
    this.name = 'ApiError';
  }
}