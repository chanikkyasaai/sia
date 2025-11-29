import { useState, useCallback } from 'react';

export interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export interface UseApiActions<T, TArgs extends any[] = any[]> {
  execute: (...args: TArgs) => Promise<T>;
  reset: () => void;
  setData: (data: T | null) => void;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function useApi<T, TArgs extends any[] = any[]>(
  apiFunction: (...args: TArgs) => Promise<T>
): UseApiState<T> & UseApiActions<T, TArgs> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async (...args: TArgs): Promise<T> => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiFunction(...args);
      setData(result);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [apiFunction]);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return {
    data,
    loading,
    error,
    execute,
    reset,
    setData,
  };
}