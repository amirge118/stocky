# Error Handling Rules: Frontend & Backend

## Error Handling Principles

### 1. Error Categories
- **Client Errors (4xx)**: User input errors, authentication, authorization
- **Server Errors (5xx)**: Server-side failures, database errors, external API failures
- **Network Errors**: Connection failures, timeouts
- **Validation Errors**: Input validation failures

### 2. Error Handling Strategy
- **Fail Fast**: Detect errors as early as possible
- **Fail Explicitly**: Use explicit error handling, not silent failures
- **User-Friendly**: Show user-friendly error messages
- **Logging**: Log all errors with context for debugging

## Backend Error Handling

### 3. FastAPI Error Handling Pattern
```python
from fastapi import HTTPException, status
from pydantic import ValidationError

# Custom exception classes
class StockNotFoundError(Exception):
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.message = f"Stock {symbol} not found"

class ValidationError(Exception):
    def __init__(self, errors: List[Dict]):
        self.errors = errors
        self.message = "Validation failed"
```

### 4. HTTP Exception Usage
```python
from fastapi import HTTPException, status

# Raise HTTPException with appropriate status code
if not stock:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "code": "STOCK_NOT_FOUND",
            "message": f"Stock {symbol} not found",
            "details": {"symbol": symbol}
        }
    )
```

### 5. Error Response Schema
```python
from pydantic import BaseModel
from typing import Optional, Dict, Any

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail
```

### 6. Global Exception Handler
```python
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

app = FastAPI()

@app.exception_handler(StockNotFoundError)
async def stock_not_found_handler(request: Request, exc: StockNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": {
                "code": "STOCK_NOT_FOUND",
                "message": exc.message,
                "details": {"symbol": exc.symbol}
            }
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": exc.errors()
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # Log the error
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred",
                "details": None  # Don't expose internal details
            }
        }
    )
```

### 7. Error Codes
**Standard Error Codes:**
- `VALIDATION_ERROR`: Input validation failed
- `RESOURCE_NOT_FOUND`: Resource doesn't exist
- `UNAUTHORIZED`: Authentication required
- `FORBIDDEN`: Insufficient permissions
- `DUPLICATE_RESOURCE`: Resource already exists
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `EXTERNAL_API_ERROR`: External API call failed
- `DATABASE_ERROR`: Database operation failed
- `INTERNAL_ERROR`: Unexpected server error

### 8. Validation Error Handling
```python
from pydantic import BaseModel, Field, validator
from typing import List

class StockCreateRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10)
    price: float = Field(..., gt=0)
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if not v.isalpha():
            raise ValueError('Symbol must contain only letters')
        return v.upper()
```

## Frontend Error Handling

### 9. API Error Types
```typescript
// types/errors.ts
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    public message: string,
    public details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export class NetworkError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'NetworkError';
  }
}

export class ValidationError extends Error {
  constructor(
    public errors: Record<string, string[]>
  ) {
    super('Validation failed');
    this.name = 'ValidationError';
  }
}
```

### 10. API Client Error Handling
```typescript
// lib/api/client.ts
export async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        response.status,
        errorData.error?.code || 'UNKNOWN_ERROR',
        errorData.error?.message || 'An error occurred',
        errorData.error?.details
      );
    }

    return response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    // Network error
    throw new NetworkError('Failed to connect to server');
  }
}
```

### 11. React Error Boundaries
```typescript
// components/ErrorBoundary.tsx
'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    // Log to error tracking service (e.g., Sentry)
  }

  public render() {
    if (this.state.hasError) {
      return this.props.fallback || <ErrorFallback error={this.state.error} />;
    }

    return this.props.children;
  }
}
```

### 12. React Query Error Handling
```typescript
// hooks/useStock.ts
import { useQuery } from '@tanstack/react-query';
import { getStock } from '@/lib/api/stock';
import { ApiError } from '@/types/errors';

export function useStock(symbol: string) {
  return useQuery({
    queryKey: ['stock', symbol],
    queryFn: () => getStock(symbol),
    retry: (failureCount, error) => {
      // Don't retry on 4xx errors
      if (error instanceof ApiError && error.status < 500) {
        return false;
      }
      return failureCount < 3;
    },
    onError: (error) => {
      // Log error to monitoring service
      if (error instanceof ApiError) {
        console.error('API Error:', error.code, error.message);
      }
    },
  });
}
```

### 13. Form Error Handling
```typescript
// Using React Hook Form
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const stockSchema = z.object({
  symbol: z.string().min(1).max(10),
  price: z.number().positive(),
});

export function StockForm() {
  const {
    register,
    handleSubmit,
    formState: { errors },
    setError,
  } = useForm({
    resolver: zodResolver(stockSchema),
  });

  const onSubmit = async (data: z.infer<typeof stockSchema>) => {
    try {
      await createStock(data);
    } catch (error) {
      if (error instanceof ValidationError) {
        // Set field-specific errors
        Object.entries(error.errors).forEach(([field, messages]) => {
          setError(field as keyof typeof data, {
            type: 'server',
            message: messages[0],
          });
        });
      }
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('symbol')} />
      {errors.symbol && <span>{errors.symbol.message}</span>}
      {/* ... */}
    </form>
  );
}
```

### 14. User-Friendly Error Messages
```typescript
// lib/utils/errorMessages.ts
export function getUserFriendlyMessage(error: ApiError): string {
  const errorMessages: Record<string, string> = {
    STOCK_NOT_FOUND: 'The stock you are looking for was not found.',
    VALIDATION_ERROR: 'Please check your input and try again.',
    UNAUTHORIZED: 'Please log in to continue.',
    FORBIDDEN: 'You do not have permission to perform this action.',
    RATE_LIMIT_EXCEEDED: 'Too many requests. Please try again later.',
    NETWORK_ERROR: 'Unable to connect to server. Please check your connection.',
  };

  return errorMessages[error.code] || 'Something went wrong. Please try again.';
}
```

### 15. Error Display Components
```typescript
// components/ErrorMessage.tsx
interface ErrorMessageProps {
  error: Error | ApiError | NetworkError;
  onRetry?: () => void;
}

export function ErrorMessage({ error, onRetry }: ErrorMessageProps) {
  const message = error instanceof ApiError
    ? getUserFriendlyMessage(error)
    : error.message;

  return (
    <div className="error-container">
      <p>{message}</p>
      {onRetry && (
        <button onClick={onRetry}>Try Again</button>
      )}
    </div>
  );
}
```

## Logging and Monitoring

### 16. Backend Logging
```python
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def log_error(
    error: Exception,
    context: Dict[str, Any],
    level: str = "ERROR"
):
    logger.log(
        getattr(logging, level),
        f"Error: {str(error)}",
        extra={
            "error_type": type(error).__name__,
            "error_message": str(error),
            **context
        },
        exc_info=True
    )
```

### 17. Frontend Error Logging
```typescript
// lib/utils/errorLogger.ts
export function logError(error: Error, context?: Record<string, unknown>) {
  // Log to console in development
  if (process.env.NODE_ENV === 'development') {
    console.error('Error:', error, context);
  }

  // Send to error tracking service (e.g., Sentry)
  if (typeof window !== 'undefined' && window.Sentry) {
    window.Sentry.captureException(error, {
      contexts: { custom: context },
    });
  }
}
```

### 18. Error Tracking
- **Backend**: Log all errors with context (request ID, user ID, etc.)
- **Frontend**: Track errors with user context (user ID, page, action)
- **Monitoring**: Set up alerts for critical errors
- **Dashboards**: Monitor error rates and types

## Error Recovery

### 19. Retry Logic
```typescript
// lib/utils/retry.ts
export async function retry<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, delay * (i + 1)));
    }
  }
  throw new Error('Retry failed');
}
```

### 20. Fallback Strategies
- **Default Values**: Provide default values when possible
- **Cached Data**: Use cached data when API fails
- **Offline Mode**: Support offline functionality
- **Graceful Degradation**: Show partial UI when data fails to load

## Key Rules Summary

1. **Always** handle errors explicitly (no silent failures)
2. **Use** consistent error response structure
3. **Log** all errors with context
4. **Show** user-friendly error messages
5. **Never** expose internal error details to users
6. **Use** appropriate HTTP status codes
7. **Implement** error boundaries in React
8. **Handle** network errors gracefully
9. **Retry** transient errors automatically
10. **Monitor** errors in production
