# Testing Rules: Frontend & Backend

## Testing Principles

### 1. Testing Pyramid
- **Unit Tests (70%)**: Test individual functions/components in isolation
- **Integration Tests (20%)**: Test component/service interactions
- **E2E Tests (10%)**: Test critical user flows end-to-end

### 2. Testing Philosophy
- **Test Behavior**: Test what the code does, not implementation details
- **Fast Tests**: Unit tests should be fast (< 100ms each)
- **Isolated Tests**: Tests should not depend on each other
- **Deterministic**: Tests should produce consistent results
- **Maintainable**: Tests should be easy to read and maintain

## Backend Testing (FastAPI)

### 3. Test Structure
```
backend/
├── app/
│   └── ...
└── tests/
    ├── conftest.py          # Pytest fixtures
    ├── unit/
    │   ├── test_services.py
    │   └── test_utils.py
    ├── integration/
    │   ├── test_api.py
    │   └── test_database.py
    └── e2e/
        └── test_flows.py
```

### 4. Test Configuration
```python
# pytest.ini or pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"
```

### 5. Test Fixtures
```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db

# Test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)

@pytest.fixture
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
```

### 6. Unit Tests
```python
# tests/unit/test_services.py
import pytest
from app.services.stock_service import StockService
from app.schemas.stock import StockCreate

@pytest.mark.asyncio
async def test_create_stock(db_session):
    service = StockService(db_session)
    stock_data = StockCreate(symbol="AAPL", name="Apple Inc.")
    
    stock = await service.create_stock(stock_data)
    
    assert stock.symbol == "AAPL"
    assert stock.name == "Apple Inc."
    assert stock.id is not None

@pytest.mark.asyncio
async def test_get_stock_not_found(db_session):
    service = StockService(db_session)
    
    stock = await service.get_stock_by_symbol("INVALID")
    
    assert stock is None
```

### 7. API Integration Tests
```python
# tests/integration/test_api.py
import pytest

def test_create_stock(client):
    response = client.post(
        "/api/v1/stocks",
        json={"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["symbol"] == "AAPL"

def test_get_stock(client):
    # Create stock first
    client.post(
        "/api/v1/stocks",
        json={"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ"}
    )
    
    # Get stock
    response = client.get("/api/v1/stocks/AAPL")
    
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["symbol"] == "AAPL"

def test_get_stock_not_found(client):
    response = client.get("/api/v1/stocks/INVALID")
    
    assert response.status_code == 404
    error = response.json()
    assert error["error"]["code"] == "STOCK_NOT_FOUND"
```

### 8. Database Tests
```python
# tests/integration/test_database.py
import pytest
from app.models.stock import Stock

@pytest.mark.asyncio
async def test_create_stock_in_db(db_session):
    stock = Stock(symbol="AAPL", name="Apple Inc.", exchange_id=1)
    db_session.add(stock)
    await db_session.commit()
    await db_session.refresh(stock)
    
    assert stock.id is not None
    assert stock.symbol == "AAPL"

@pytest.mark.asyncio
async def test_query_stock(db_session):
    stock = Stock(symbol="AAPL", name="Apple Inc.", exchange_id=1)
    db_session.add(stock)
    await db_session.commit()
    
    from sqlalchemy import select
    result = await db_session.execute(select(Stock).where(Stock.symbol == "AAPL"))
    found_stock = result.scalar_one_or_none()
    
    assert found_stock is not None
    assert found_stock.symbol == "AAPL"
```

## Frontend Testing (Next.js & React)

### 9. Test Structure
```
frontend/
├── app/
├── components/
└── __tests__/
    ├── components/
    │   ├── StockCard.test.tsx
    │   └── StockList.test.tsx
    ├── hooks/
    │   └── useStock.test.ts
    └── utils/
        └── api.test.ts
```

### 10. Testing Setup
```json
// package.json
{
  "devDependencies": {
    "@testing-library/react": "^14.0.0",
    "@testing-library/jest-dom": "^6.1.0",
    "@testing-library/user-event": "^14.5.0",
    "jest": "^29.7.0",
    "jest-environment-jsdom": "^29.7.0"
  }
}
```

```javascript
// jest.config.js
const nextJest = require('next/jest')

const createJestConfig = nextJest({
  dir: './',
})

const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
}

module.exports = createJestConfig(customJestConfig)
```

### 11. Component Testing
```typescript
// __tests__/components/StockCard.test.tsx
import { render, screen } from '@testing-library/react';
import { StockCard } from '@/components/StockCard';

describe('StockCard', () => {
  const mockStock = {
    symbol: 'AAPL',
    price: 150.25,
    change: 2.5,
    changePercent: 1.69,
  };

  it('renders stock information', () => {
    render(<StockCard stock={mockStock} />);
    
    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('$150.25')).toBeInTheDocument();
  });

  it('displays positive change in green', () => {
    render(<StockCard stock={mockStock} />);
    
    const changeElement = screen.getByText('+2.5');
    expect(changeElement).toHaveClass('text-green-500');
  });

  it('calls onSelect when clicked', () => {
    const handleSelect = jest.fn();
    render(<StockCard stock={mockStock} onSelect={handleSelect} />);
    
    screen.getByRole('button').click();
    expect(handleSelect).toHaveBeenCalledWith('AAPL');
  });
});
```

### 12. Hook Testing
```typescript
// __tests__/hooks/useStock.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useStock } from '@/hooks/useStock';
import { getStock } from '@/lib/api/stock';

jest.mock('@/lib/api/stock');

describe('useStock', () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  it('fetches stock data', async () => {
    (getStock as jest.Mock).mockResolvedValue({
      symbol: 'AAPL',
      price: 150.25,
    });

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );

    const { result } = renderHook(() => useStock('AAPL'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.symbol).toBe('AAPL');
    expect(getStock).toHaveBeenCalledWith('AAPL');
  });
});
```

### 13. API Mocking
```typescript
// __tests__/utils/api.test.ts
import { apiRequest } from '@/lib/api/client';

global.fetch = jest.fn();

describe('apiRequest', () => {
  beforeEach(() => {
    (fetch as jest.Mock).mockClear();
  });

  it('makes successful API request', async () => {
    const mockData = { data: { symbol: 'AAPL' } };
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockData,
    });

    const result = await apiRequest('/stocks/AAPL');

    expect(result).toEqual(mockData);
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/stocks/AAPL'),
      expect.any(Object)
    );
  });

  it('throws error on failed request', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({
        error: { code: 'NOT_FOUND', message: 'Not found' },
      }),
    });

    await expect(apiRequest('/stocks/INVALID')).rejects.toThrow();
  });
});
```

## E2E Testing

### 14. Playwright Setup
```typescript
// e2e/stock-flow.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Stock Flow', () => {
  test('user can search and view stock', async ({ page }) => {
    await page.goto('/');
    
    // Search for stock
    await page.fill('[data-testid="stock-search"]', 'AAPL');
    await page.click('[data-testid="search-button"]');
    
    // Wait for results
    await page.waitForSelector('[data-testid="stock-card"]');
    
    // Verify stock is displayed
    await expect(page.locator('text=AAPL')).toBeVisible();
  });
});
```

## Test Coverage

### 15. Coverage Requirements
- **Unit Tests**: Aim for 80%+ coverage
- **Critical Paths**: 100% coverage for critical business logic
- **API Endpoints**: Test all endpoints
- **Error Cases**: Test error handling paths

### 16. Coverage Configuration
```json
// package.json (frontend)
{
  "scripts": {
    "test:coverage": "jest --coverage"
  }
}
```

```ini
# .coveragerc (backend)
[run]
source = app
omit = 
    */tests/*
    */migrations/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
```

## Test Data Management

### 17. Test Fixtures
```python
# tests/fixtures/stock_fixtures.py
import pytest
from app.models.stock import Stock

@pytest.fixture
def sample_stock():
    return Stock(
        symbol="AAPL",
        name="Apple Inc.",
        exchange_id=1
    )

@pytest.fixture
def sample_stocks():
    return [
        Stock(symbol="AAPL", name="Apple Inc.", exchange_id=1),
        Stock(symbol="GOOGL", name="Alphabet Inc.", exchange_id=1),
        Stock(symbol="MSFT", name="Microsoft Corp.", exchange_id=1),
    ]
```

### 18. Mocking External Services
```python
# tests/mocks/external_api.py
from unittest.mock import AsyncMock, patch

@pytest.fixture
def mock_yfinance():
    with patch('app.services.stock_service.yfinance') as mock:
        mock.Ticker.return_value.info = {
            'symbol': 'AAPL',
            'currentPrice': 150.25
        }
        yield mock
```

## Test Best Practices

### 19. Test Naming
- **Descriptive Names**: Use descriptive test names
- **Given-When-Then**: Structure tests with clear setup, action, assertion
- **One Assertion**: Prefer one assertion per test (when possible)

### 20. Test Organization
- **Arrange-Act-Assert**: Follow AAA pattern
- **Setup/Teardown**: Use fixtures for setup and teardown
- **Isolation**: Each test should be independent

## Key Rules Summary

1. **Write** tests before or alongside code (TDD when possible)
2. **Test** behavior, not implementation
3. **Keep** tests fast and isolated
4. **Use** descriptive test names
5. **Mock** external dependencies
6. **Test** error cases and edge cases
7. **Maintain** high test coverage (80%+)
8. **Review** tests in code reviews
9. **Refactor** tests when refactoring code
10. **Run** tests before committing code
