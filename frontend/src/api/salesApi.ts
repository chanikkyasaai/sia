import { API_CONFIG, API_ENDPOINTS, createApiUrl } from './config';
import { TransactionResponse } from './types';
import { ApiError } from './config';

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
        if (errorJson.detail) {
          if (Array.isArray(errorJson.detail)) {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            errorMessage = errorJson.detail.map((err: any) => 
              `${err.loc?.join('.')} - ${err.msg}`
            ).join(', ');
          } else if (typeof errorJson.detail === 'string') {
            errorMessage = errorJson.detail;
          } else {
            errorMessage = JSON.stringify(errorJson.detail);
          }
        } else {
          errorMessage = errorJson.message || errorText || errorMessage;
        }
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

export const salesApi = {
  async getAll(): Promise<TransactionResponse[]> {
    const url = `${API_ENDPOINTS.SALES}?business_id=${API_CONFIG.BUSINESS_ID}`;
    console.log('Fetching sales from:', createApiUrl(url));
    try {
      const result = await apiFetch<TransactionResponse[]>(url);
      console.log('Sales fetched successfully:', result);
      return result;
    } catch (error) {
      console.error('Error fetching sales:', error);
      throw error;
    }
  },
};