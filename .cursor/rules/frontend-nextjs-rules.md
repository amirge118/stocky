# Frontend Rules: Next.js & React

> **Note**: Comprehensive frontend architecture, project structure, and detailed rules are documented in `frontend/.cursorrules`.
> 
> For complete frontend architecture, see: [frontend/.cursorrules](../../frontend/.cursorrules)
> 
> This file provides quick reference and specific patterns. For full details, refer to the main architecture file.

## Next.js 15 App Router Rules

### 1. File-Based Routing
- Use App Router (`app/` directory) exclusively
- Use route groups `(folder)` for organization without affecting URL structure
- Use `layout.tsx` for shared UI across routes
- Use `page.tsx` for route pages
- Use `loading.tsx` for loading states
- Use `error.tsx` for error boundaries
- Use `not-found.tsx` for 404 pages

### 2. Server vs Client Components
- **Default to Server Components**: Use Server Components by default for better performance
- **Use 'use client' only when needed**: 
  - Interactive components (onClick, useState, useEffect)
  - Browser-only APIs (localStorage, window)
  - Custom hooks that use React hooks
- **Pattern**: Keep Server Components at the top, Client Components as leaves

### 3. Data Fetching
- **Server Components**: Fetch data directly in Server Components
- **Client Components**: Use React Query/SWR for client-side data fetching
- **Never**: Fetch data in useEffect for initial render (use Server Components or React Query)

```typescript
// ✅ Good: Server Component
async function StockPage({ symbol }: { symbol: string }) {
  const data = await fetch(`${API_URL}/stocks/${symbol}`);
  return <StockDisplay data={data} />;
}

// ✅ Good: Client Component with React Query
'use client';
function StockPage({ symbol }: { symbol: string }) {
  const { data } = useQuery(['stock', symbol], () => fetchStock(symbol));
  return <StockDisplay data={data} />;
}
```

## React Component Rules

### 4. Component Structure
- **Functional Components Only**: Never use class components
- **Named Exports**: Use named exports for components
- **File Naming**: Use PascalCase for component files (`StockCard.tsx`)
- **Component Naming**: Match component name to file name

### 5. Component Organization
```typescript
// Component structure order:
// 1. Imports (external, then internal)
// 2. Types/Interfaces
// 3. Component
// 4. Exports

import { useState } from 'react';
import { StockCard } from '@/components/StockCard';

interface Props {
  symbol: string;
}

export function StockList({ symbol }: Props) {
  // Component logic
}
```

### 6. Hooks Rules
- **Custom Hooks**: Prefix with `use` (e.g., `useStockData`)
- **Hook Location**: Place hooks at the top of component, before any early returns
- **Dependencies**: Always include all dependencies in dependency arrays
- **No Conditional Hooks**: Never call hooks conditionally

### 7. Props and State
- **TypeScript Interfaces**: Always define props with TypeScript interfaces
- **Destructure Props**: Destructure props in function signature
- **State Naming**: Use descriptive names (`isLoading`, not `loading`)
- **State Updates**: Use functional updates for state that depends on previous state

```typescript
// ✅ Good
interface StockCardProps {
  symbol: string;
  price: number;
  onSelect?: (symbol: string) => void;
}

export function StockCard({ symbol, price, onSelect }: StockCardProps) {
  const [isSelected, setIsSelected] = useState(false);
  
  const handleClick = () => {
    setIsSelected(prev => !prev);
    onSelect?.(symbol);
  };
}
```

## TypeScript Rules

### 8. Type Safety
- **No 'any'**: Never use `any` type
- **Use 'unknown'**: Use `unknown` when type is truly unknown, then narrow
- **Explicit Return Types**: Add return types to functions (especially async functions)
- **Strict Mode**: Enable strict TypeScript settings

### 9. Type Definitions
- **Shared Types**: Place shared types in `types/` directory
- **Component Types**: Define component-specific types near the component
- **API Types**: Match backend Pydantic schemas exactly

```typescript
// types/stock.ts
export interface Stock {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
}

export interface StockResponse {
  data: Stock;
  timestamp: string;
}
```

## State Management Rules

### 10. React Query / SWR Usage
- **Server State**: Use React Query for all server state
- **Query Keys**: Use consistent, hierarchical query keys
- **Cache Time**: Configure appropriate cache and stale times
- **Refetching**: Set up automatic refetching for real-time data

```typescript
// lib/api/stock.ts
export const stockKeys = {
  all: ['stocks'] as const,
  detail: (symbol: string) => [...stockKeys.all, symbol] as const,
  list: (filters: StockFilters) => [...stockKeys.all, 'list', filters] as const,
};

export function useStock(symbol: string) {
  return useQuery({
    queryKey: stockKeys.detail(symbol),
    queryFn: () => fetchStock(symbol),
    staleTime: 30000, // 30 seconds
  });
}
```

### 11. Local State
- **useState**: For simple component state
- **useReducer**: For complex state logic
- **Context API**: Only for truly global state (auth, theme)

### 12. Form State
- **React Hook Form**: Use React Hook Form for all forms
- **Validation**: Use Zod for schema validation (matches Pydantic)
- **Error Handling**: Display validation errors clearly

## API Client Rules

### 13. API Client Structure
- **Centralized**: All API calls in `lib/api/` directory
- **Type Safety**: All functions typed with TypeScript interfaces
- **Error Handling**: Consistent error handling across all API calls
- **Base URL**: Use environment variable for API base URL

```typescript
// lib/api/client.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || '';

export async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new ApiError(response.status, await response.json());
  }

  return response.json();
}
```

### 14. API Function Pattern
```typescript
// lib/api/stock.ts
import { apiRequest } from './client';
import type { Stock, StockResponse } from '@/types/stock';

export async function getStock(symbol: string): Promise<Stock> {
  const response = await apiRequest<StockResponse>(`/api/v1/stocks/${symbol}`);
  return response.data;
}

export async function getStocks(filters: StockFilters): Promise<Stock[]> {
  const response = await apiRequest<StockListResponse>(
    `/api/v1/stocks`,
    { method: 'GET', body: JSON.stringify(filters) }
  );
  return response.data;
}
```

## Component Patterns

### 15. Component Composition
- **Small Components**: Keep components small and focused
- **Composition**: Compose complex UIs from simple components
- **Props Drilling**: Avoid deep prop drilling (use Context if needed)

### 16. Reusable Components
- **UI Components**: Place in `components/ui/` (Shadcn components)
- **Feature Components**: Place in `components/features/`
- **Layout Components**: Place in `components/layout/`

### 17. Loading and Error States
- **Loading**: Always show loading states
- **Error Boundaries**: Use error boundaries for error handling
- **Empty States**: Design clear empty states

```typescript
export function StockList() {
  const { data, isLoading, error } = useStocks();

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;
  if (!data?.length) return <EmptyState />;

  return <div>{/* render stocks */}</div>;
}
```

## Performance Rules

### 18. Optimization
- **Image Optimization**: Always use Next.js `Image` component
- **Code Splitting**: Use dynamic imports for large components
- **Memoization**: Use `React.memo` for expensive components
- **useMemo/useCallback**: Only when profiling shows it's needed

### 19. Bundle Size
- **Tree Shaking**: Import only what you need
- **Dynamic Imports**: Use dynamic imports for heavy libraries
- **Analyze Bundle**: Regularly analyze bundle size

```typescript
// ✅ Good: Dynamic import
const HeavyChart = dynamic(() => import('./HeavyChart'), {
  loading: () => <ChartSkeleton />,
  ssr: false,
});
```

## Styling Rules

### 20. Tailwind CSS
- **Utility Classes**: Use Tailwind utility classes
- **Custom Classes**: Use `@apply` sparingly
- **Responsive**: Mobile-first responsive design
- **Dark Mode**: Support dark mode with `dark:` prefix

### 21. Shadcn UI
- **Component Library**: Use Shadcn UI components as base
- **Customization**: Customize via CSS variables
- **Accessibility**: Shadcn components are accessible by default

## Accessibility Rules

### 22. A11y Requirements
- **Semantic HTML**: Use semantic HTML elements
- **ARIA Labels**: Add ARIA labels when needed
- **Keyboard Navigation**: Ensure keyboard accessibility
- **Focus Management**: Manage focus properly
- **Color Contrast**: Ensure sufficient color contrast

## Testing Rules

### 23. Component Testing
- **Unit Tests**: Test components in isolation
- **Integration Tests**: Test component interactions
- **Accessibility Tests**: Test with screen readers

### 24. File Organization
```
components/
  ui/              # Shadcn components
  features/        # Feature-specific components
    stocks/
      StockCard.tsx
      StockList.tsx
  layout/          # Layout components
lib/
  api/             # API client functions
  utils/           # Utility functions
hooks/             # Custom hooks
types/             # TypeScript types
```

## Key Rules Summary

1. **Always** use TypeScript with strict mode
2. **Default** to Server Components in Next.js
3. **Use** React Query for all server state
4. **Never** use `any` type
5. **Always** handle loading and error states
6. **Keep** components small and focused
7. **Use** Tailwind CSS for styling
8. **Ensure** accessibility in all components
9. **Type** all API responses with interfaces
10. **Optimize** images with Next.js Image component

---

> **For comprehensive frontend architecture, project structure, dependency versions, and detailed setup instructions, see: [frontend/.cursorrules](../../frontend/.cursorrules)**
