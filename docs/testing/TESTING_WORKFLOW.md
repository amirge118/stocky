# Testing Workflow & Requirements

## Why Tests Weren't Written Initially

**Explanation**: During initial implementation, the focus was on getting the feature working end-to-end. Tests were overlooked due to:
1. **Time pressure** - Prioritizing working code over test coverage
2. **Oversight** - Not following TDD (Test-Driven Development) approach
3. **Missing enforcement** - No explicit rules requiring tests in `.cursorrules`

**This was a mistake.** Tests are essential for:
- **Confidence**: Knowing code works correctly
- **Refactoring**: Safe changes without breaking functionality
- **Documentation**: Tests serve as usage examples
- **Regression prevention**: Catching bugs before deployment

## New Mandatory Testing Rules

### Backend Testing Requirements

**For EVERY new feature/service/endpoint:**

1. **Unit Tests** (`tests/unit/test_*.py`):
   ```bash
   # Create test file matching the module
   tests/unit/test_stock_service.py  # for app/services/stock_service.py
   ```

2. **Integration Tests** (`tests/integration/test_*.py`):
   ```bash
   # Test API endpoints
   tests/integration/test_stock_endpoints.py  # for app/api/v1/endpoints/stocks.py
   ```

3. **Live Postgres URL + connectivity** (optional; uses real `DATABASE_URL` from `backend/.env`):
   ```bash
   cd backend && pytest tests/integration/test_database_connection.py -v
   ```
   Skips if `DATABASE_URL` is empty or not `postgresql+asyncpg://...`. Validates host/DB path and runs `SELECT 1` with the same SSL rules as `app.core.database`.

4. **Test Coverage**: Minimum 80% for new code

### Frontend Testing Requirements

**For EVERY new component/hook/utility:**

1. **Unit Tests** (`__tests__/components/*.test.tsx`):
   ```bash
   __tests__/components/StockCard.test.tsx  # for components/features/stocks/StockCard.tsx
   ```

2. **API Tests** (`__tests__/lib/api/*.test.ts`):
   ```bash
   __tests__/lib/api/stocks.test.ts  # for lib/api/stocks.ts
   ```

3. **E2E Tests** (`e2e/*.spec.ts`):
   ```bash
   e2e/stocks.spec.ts  # for complete user flows
   ```

## Testing Workflow

### Step 1: Write Tests First (TDD Approach)

```bash
# Backend
1. Write test in tests/unit/test_new_feature.py
2. Run: pytest tests/unit/test_new_feature.py -v
3. See test fail (red)
4. Implement feature
5. See test pass (green)
6. Refactor if needed

# Frontend
1. Write test in __tests__/components/NewComponent.test.tsx
2. Run: npm test NewComponent
3. See test fail
4. Implement component
5. See test pass
6. Refactor if needed
```

### Step 2: Run All Tests Before Committing

```bash
# Backend
cd backend
source venv/bin/activate
pytest --cov=app --cov-report=term-missing
pytest tests/integration -v

# Frontend
cd frontend
npm test
npm run test:e2e
```

### Step 3: Ensure Coverage Thresholds

```bash
# Backend - Aim for 80%+ coverage
pytest --cov=app --cov-report=html
# Open htmlcov/index.html to see coverage report

# Frontend - Aim for 80%+ coverage
npm run test:coverage
```

## Test Structure Examples

### Backend Unit Test Example

```python
# tests/unit/test_stock_service.py
@pytest.mark.asyncio
async def test_create_stock_success(db_session):
    """Test creating a new stock."""
    stock_data = StockCreate(
        symbol="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        sector="Technology",
    )
    
    result = await stock_service.create_stock(db_session, stock_data)
    
    assert result.symbol == "AAPL"
    assert result.id is not None

@pytest.mark.asyncio
async def test_create_stock_duplicate_raises_error(db_session):
    """Test that creating duplicate stock raises HTTPException."""
    # Create first stock
    # Try to create duplicate
    # Assert exception raised
```

### Frontend Component Test Example

```typescript
// __tests__/components/StockCard.test.tsx
describe("StockCard", () => {
  it("renders stock information correctly", () => {
    render(<StockCard stock={mockStock} />)
    expect(screen.getByText("AAPL")).toBeInTheDocument()
  })

  it("calls onSelect when clicked", () => {
    const onSelect = jest.fn()
    render(<StockCard stock={mockStock} onSelect={onSelect} />)
    fireEvent.click(screen.getByText("AAPL"))
    expect(onSelect).toHaveBeenCalledWith("AAPL")
  })
})
```

## Pre-Commit Checklist

Before marking any implementation as complete:

- [ ] All unit tests written and passing
- [ ] All integration tests written and passing
- [ ] E2E tests written for critical flows
- [ ] Code coverage > 80%
- [ ] Error cases tested
- [ ] Edge cases tested
- [ ] Loading states tested (frontend)
- [ ] User interactions tested (frontend)

## Running Tests

### Backend

```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_stock_service.py -v

# Run specific test
pytest tests/unit/test_stock_service.py::test_create_stock_success -v

# Run integration tests only
pytest tests/integration -v
```

### Frontend

```bash
cd frontend

# Run all tests
npm test

# Run in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e

# Run specific test file
npm test StockCard
```

## Continuous Integration

Tests should run automatically on:
- Every commit (pre-commit hooks)
- Every pull request (CI/CD pipeline)
- Before deployment

## Test Maintenance

- **Update tests** when features change
- **Remove obsolete tests** for removed features
- **Refactor tests** when code is refactored
- **Keep tests fast** (< 1 second for unit tests)
- **Keep tests isolated** (no dependencies between tests)

## Common Testing Patterns

### Backend: Mocking External APIs

```python
@patch("app.services.stock_service.yf")
async def test_fetch_stock_data(mock_yf):
    mock_yf.Ticker.return_value.info = {...}
    result = await fetch_stock_data("AAPL")
    assert result.symbol == "AAPL"
```

### Frontend: Mocking API Calls

```typescript
jest.mock("@/lib/api/stocks")
const mockGetStocks = getStocks as jest.MockedFunction<typeof getStocks>
mockGetStocks.mockResolvedValue(mockStocks)
```

### Testing Async Code

```python
# Backend
@pytest.mark.asyncio
async def test_async_function(db_session):
    result = await async_function(db_session)
    assert result is not None
```

```typescript
// Frontend
it("handles async data", async () => {
  await waitFor(() => {
    expect(screen.getByText("Data")).toBeInTheDocument()
  })
})
```

## Resources

- Backend Testing Guide: `.cursor/rules/testing-rules.md`
- Frontend Testing Guide: `frontend/.cursorrules` (Testing Strategy section)
- Pytest Documentation: https://docs.pytest.org/
- React Testing Library: https://testing-library.com/react
- Playwright: https://playwright.dev/
