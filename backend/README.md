# Stock Insight App - Backend

FastAPI backend for the Stock Insight App.

## Setup

1. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements-dev.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Set up database:**
   ```bash
   # Create PostgreSQL database
   createdb stock_insight
   
   # Run migrations
   alembic upgrade head
   ```

## Running

**Development:**
```bash
uvicorn app.main:app --reload
```

**Production:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py
```

## Code Quality

```bash
# Format code
black .

# Lint code
ruff check .

# Type check
mypy app
```

## Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── core/                # Core configuration
│   ├── api/                 # API routes
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   └── middleware/          # Custom middleware
├── tests/                   # Test suite
├── alembic/                 # Database migrations
└── requirements.txt         # Dependencies
```
