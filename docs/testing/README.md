# Testing Documentation

This directory contains all testing-related documentation.

## Documentation Files

- **[Testing Summary](./TESTING_SUMMARY.md)** - Overview of all tests created
- **[Testing Workflow](./TESTING_WORKFLOW.md)** - Step-by-step testing guide
- **[Why Tests Missed](./WHY_TESTS_MISSED.md)** - Analysis and prevention measures

## Quick Links

- **Backend Tests**: `backend/tests/`
- **Frontend Tests**: `frontend/__tests__/` and `frontend/e2e/`
- **Test Rules**: `.cursor/rules/testing-rules.md`

## Running Tests

### Backend
```bash
cd backend
source venv/bin/activate
pytest                    # All tests
pytest --cov=app         # With coverage
pytest tests/unit -v     # Unit tests only
```

### Frontend
```bash
cd frontend
npm test                 # All tests
npm run test:coverage    # With coverage
npm run test:e2e         # E2E tests
```

## Test Coverage

- **Backend**: 27+ tests (15 unit + 12 integration)
- **Frontend**: 20+ tests (components + API + E2E)
- **Coverage Goal**: 80%+

See [Testing Workflow](./TESTING_WORKFLOW.md) for detailed information.
