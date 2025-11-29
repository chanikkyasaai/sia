// Type definitions for API requests and responses

// Customer Types
export interface CustomerCreate {
  name: string;
  phone: string;
  info?: string | null;
  risk_level: string;
  credit?: number | null;
  avg_delay_days?: number | null;
  business_id: number;
}

export interface CustomerResponse {
  name: string;
  phone: string;
  info?: string | null;
  risk_level: string;
  credit?: number | null;
  avg_delay_days?: number | null;
  id: number;
  created_at: string;
}

// Credit Type for UI
export interface CreditInput {
  type: 'owes_business' | 'business_owes'; // owes_business = negative, business_owes = positive
  amount: number;
}

// API Response wrapper
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}

// Error response
export interface ApiError {
  message: string;
  status?: number;
  details?: any;
}

// Expense Types
export interface ExpenseCreate {
  amount: number;
  type: string;
  note: string;
  occurred_at: string;
  id?: number;
  business_id: number;
  source: string;
}

export interface ExpenseResponse {
  amount: string;
  type: string;
  note: string | null;
  occurred_at: string;
  id: number;
  business_id: number;
  created_at: string;
  source: string;
}

// Transaction/Sales Types
export interface TransactionResponse {
  type: string;
  amount: number;
  quantity: number;
  note: string;
  source: string;
  id: number;
  created_at: string;
  customer: CustomerResponse;
  product: {
    name: string;
    unit: string;
    low_stock_threshold: number;
    avg_cost_price: number;
    avg_sale_price: number;
    is_active: boolean;
    id: number;
    business_id: number;
    created_at: string;
  };
}