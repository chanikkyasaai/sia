import { API_CONFIG, API_ENDPOINTS, createApiUrl } from './config';

// Product Types
export interface ProductCreate {
  name: string;
  unit: string;
  low_stock_threshold?: number | null;
  avg_cost_price?: number | null;
  avg_sale_price?: number | null;
  is_active: boolean;
  business_id: number;
}

export interface ProductResponse {
  name: string;
  unit: string;
  low_stock_threshold?: number | null;
  avg_cost_price?: number | null;
  avg_sale_price?: number | null;
  is_active: boolean;
  id: number;
  created_at: string;
}

// Inventory Quantity Types
export interface InventoryQuantity {
  quantity_on_hand: number;
  id: number; // Record ID in inventory table
  product_id: number; // Foreign key to product
}

export interface InventoryCreate {
  quantity_on_hand: number;
  product_id: number;
  business_id: number;
}

export interface InventoryResponse {
  quantity_on_hand: number;
  id: number;
  product_id: number;
  created_at: string;
}

// Combined Product with Inventory
export interface ProductWithInventory extends ProductResponse {
  quantity_on_hand?: number;
}

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
        // Handle FastAPI validation errors
        if (errorJson.detail) {
          if (Array.isArray(errorJson.detail)) {
            // Validation errors array
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

      console.error('API Error:', errorMessage);
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

// Product and Inventory API functions
export const inventoryApi = {
  // Create a new product
  async create(productData: Omit<ProductCreate, 'business_id'>): Promise<ProductResponse> {
    const payload: ProductCreate = {
      ...productData,
      business_id: API_CONFIG.BUSINESS_ID,
    };

    return await apiFetch<ProductResponse>(API_ENDPOINTS.PRODUCTS, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // Get all products for the business
  async getAllProducts(): Promise<ProductResponse[]> {
    const url = `${API_ENDPOINTS.PRODUCTS}?business_id=${API_CONFIG.BUSINESS_ID}`;
    console.log('Fetching products from:', createApiUrl(url));
    try {
      const result = await apiFetch<ProductResponse[]>(url);
      console.log('Products fetched successfully:', result);
      return result;
    } catch (error) {
      console.error('Error fetching products:', error);
      throw error;
    }
  },

  // Get inventory quantities
  async getInventoryQuantities(): Promise<InventoryQuantity[]> {
    const url = `${API_ENDPOINTS.INVENTORY}?business_id=${API_CONFIG.BUSINESS_ID}`;
    console.log('Fetching inventory quantities from:', createApiUrl(url));
    try {
      const result = await apiFetch<InventoryQuantity[]>(url);
      console.log('Inventory quantities fetched:', result);
      console.log('Inventory IDs:', result.map(inv => inv.id));
      console.log('First inventory item structure:', JSON.stringify(result[0], null, 2));
      return result;
    } catch (error) {
      console.error('Error fetching inventory quantities:', error);
      throw error;
    }
  },

  // Create inventory entry for a product
  async createInventory(productId: number, quantityOnHand: number): Promise<InventoryResponse> {
    const payload: InventoryCreate = {
      quantity_on_hand: quantityOnHand,
      product_id: productId,
      business_id: API_CONFIG.BUSINESS_ID,
    };

    return await apiFetch<InventoryResponse>(API_ENDPOINTS.INVENTORY, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // Create product with inventory in sequence
  async createWithInventory(
    productData: Omit<ProductCreate, 'business_id'>,
    quantityOnHand: number
  ): Promise<ProductWithInventory> {
    try {
      // Step 1: Create the product
      const product = await inventoryApi.create(productData);
      
      // Step 2: Create the inventory entry
      const inventory = await inventoryApi.createInventory(product.id, quantityOnHand);
      
      // Return combined result
      return {
        ...product,
        quantity_on_hand: inventory.quantity_on_hand,
      };
    } catch (error) {
      console.error('Error creating product with inventory:', error);
      throw error;
    }
  },

  // Get all products with their inventory quantities combined
  async getAll(): Promise<ProductWithInventory[]> {
    try {
      const [products, inventories] = await Promise.all([
        inventoryApi.getAllProducts(),
        inventoryApi.getInventoryQuantities(),
      ]);

      // Merge products with their inventory quantities
      // Match using inventory.product_id with product.id
      const productsWithInventory = products.map(product => {
        const inventory = inventories.find(inv => inv.product_id === product.id);
        console.log(`Product ${product.id} (${product.name}):`, 
          'Found inventory:', inventory, 
          'Quantity:', inventory?.quantity_on_hand);
        return {
          ...product,
          quantity_on_hand: inventory?.quantity_on_hand || 0,
        };
      });

      console.log('Merged products with inventory:', productsWithInventory);
      return productsWithInventory;
    } catch (error) {
      console.error('Error fetching products with inventory:', error);
      throw error;
    }
  },
};

// Error class
export class ApiError extends Error {
  constructor(message: string, public status?: number, public details?: unknown) {
    super(message);
    this.name = 'ApiError';
  }
}
