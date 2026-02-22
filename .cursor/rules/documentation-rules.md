# Documentation Rules: Code & API Documentation

## Documentation Principles

### 1. Documentation Philosophy
- **Self-Documenting Code**: Write code that is self-explanatory
- **Document Why**: Document why decisions were made, not just what
- **Keep Updated**: Keep documentation in sync with code
- **User-Focused**: Write documentation for the reader, not the writer

### 2. Documentation Types
- **Code Comments**: Inline code documentation
- **API Documentation**: API endpoint documentation
- **README Files**: Project setup and usage
- **Architecture Docs**: System design and architecture
- **User Guides**: End-user documentation

## Code Documentation

### 3. Python Documentation (Backend)

**Docstrings:**
```python
def get_stock_by_symbol(db: AsyncSession, symbol: str) -> Optional[Stock]:
    """
    Retrieve a stock by its symbol.
    
    Args:
        db: Database session
        symbol: Stock symbol (e.g., 'AAPL')
    
    Returns:
        Stock object if found, None otherwise
    
    Raises:
        ValueError: If symbol is empty or invalid
    
    Example:
        >>> stock = await get_stock_by_symbol(db, "AAPL")
        >>> print(stock.name)
        Apple Inc.
    """
    if not symbol or not symbol.isalpha():
        raise ValueError("Invalid symbol format")
    
    result = await db.execute(
        select(Stock).where(Stock.symbol == symbol.upper())
    )
    return result.scalar_one_or_none()
```

**Class Documentation:**
```python
class StockService:
    """
    Service layer for stock-related operations.
    
    This service handles business logic for stock operations,
    including validation, data transformation, and error handling.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize StockService.
        
        Args:
            db: Database session for data access
        """
        self.db = db
```

### 4. TypeScript Documentation (Frontend)

**Function Documentation:**
```typescript
/**
 * Fetches stock data from the API.
 * 
 * @param symbol - Stock symbol (e.g., 'AAPL')
 * @returns Promise resolving to stock data
 * @throws {ApiError} If stock is not found or API request fails
 * 
 * @example
 * ```typescript
 * const stock = await getStock('AAPL');
 * console.log(stock.price);
 * ```
 */
export async function getStock(symbol: string): Promise<Stock> {
  const response = await apiRequest<StockResponse>(`/api/v1/stocks/${symbol}`);
  return response.data;
}
```

**Component Documentation:**
```typescript
/**
 * StockCard component displays stock information in a card format.
 * 
 * @param stock - Stock data to display
 * @param onSelect - Callback function when stock is selected
 * 
 * @example
 * ```tsx
 * <StockCard 
 *   stock={stockData} 
 *   onSelect={(symbol) => console.log(symbol)} 
 * />
 * ```
 */
interface StockCardProps {
  stock: Stock;
  onSelect?: (symbol: string) => void;
}

export function StockCard({ stock, onSelect }: StockCardProps) {
  // Component implementation
}
```

### 5. Comment Guidelines
- **Why, Not What**: Explain why code exists, not what it does
- **Complex Logic**: Comment complex algorithms or business logic
- **TODOs**: Use TODO comments for future improvements
- **Avoid Obvious**: Don't comment obvious code

```python
# ✅ Good: Explains why
# Use asyncpg for better performance with async operations
async def get_stocks(db: AsyncSession):
    pass

# ❌ Bad: States the obvious
# This function gets stocks
async def get_stocks(db: AsyncSession):
    pass
```

## API Documentation

### 6. FastAPI Documentation
- **Automatic Docs**: FastAPI generates OpenAPI/Swagger docs automatically
- **Descriptions**: Add descriptions to all endpoints and models
- **Examples**: Include request/response examples
- **Tags**: Organize endpoints with tags

```python
@router.post(
    "/stocks",
    response_model=StockResponse,
    status_code=201,
    summary="Create a new stock",
    description="""
    Creates a new stock entry in the system.
    
    The stock symbol must be unique and follow exchange conventions.
    """,
    response_description="The created stock object",
    tags=["stocks"]
)
async def create_stock(
    request: StockCreateRequest,
    db: AsyncSession = Depends(get_db)
) -> StockResponse:
    """
    Create a new stock.
    
    - **symbol**: Stock symbol (required, 1-10 uppercase letters)
    - **name**: Stock name (required, 1-255 characters)
    - **exchange**: Stock exchange (required)
    - **sector**: Optional sector classification
    
    Returns the created stock with generated ID and timestamps.
    """
    pass
```

### 7. Pydantic Model Documentation
```python
class StockCreateRequest(BaseModel):
    """
    Request model for creating a new stock.
    
    Attributes:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        name: Full company name
        exchange: Stock exchange identifier
        sector: Optional sector classification
    """
    symbol: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Stock ticker symbol",
        example="AAPL"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Full company name",
        example="Apple Inc."
    )
    exchange: str = Field(..., description="Stock exchange", example="NASDAQ")
    sector: Optional[str] = Field(None, description="Sector classification")
    
    class Config:
        schema_extra = {
            "example": {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "exchange": "NASDAQ",
                "sector": "Technology"
            }
        }
```

## README Documentation

### 8. Project README Structure
```markdown
# Stock Insight App

## Description
Brief description of the project and its purpose.

## Features
- Feature 1
- Feature 2
- Feature 3

## Tech Stack
- Frontend: Next.js 15, TypeScript, Tailwind CSS
- Backend: FastAPI, Python 3.11+
- Database: PostgreSQL

## Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL 14+

## Installation

### Backend
\`\`\`bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
\`\`\`

### Frontend
\`\`\`bash
cd frontend
npm install
\`\`\`

## Configuration
Copy `.env.example` to `.env` and configure:
- Database URL
- API keys
- CORS origins

## Running the Application

### Backend
\`\`\`bash
cd backend
uvicorn app.main:app --reload
\`\`\`

### Frontend
\`\`\`bash
cd frontend
npm run dev
\`\`\`

## API Documentation
API documentation available at: http://localhost:8000/docs

## Testing
\`\`\`bash
# Backend
pytest

# Frontend
npm test
\`\`\`

## Contributing
See CONTRIBUTING.md for guidelines.

## License
MIT License
```

### 9. Component/Module README
```markdown
# Stock Service

## Overview
Service layer for stock-related operations.

## Functions

### `get_stock_by_symbol(symbol: str) -> Optional[Stock]`
Retrieves a stock by its symbol.

**Parameters:**
- `symbol`: Stock symbol (e.g., 'AAPL')

**Returns:**
- Stock object if found, None otherwise

**Example:**
\`\`\`python
stock = await get_stock_by_symbol(db, "AAPL")
\`\`\`

## Usage
\`\`\`python
from app.services.stock_service import StockService

service = StockService(db)
stock = await service.get_stock_by_symbol("AAPL")
\`\`\`
```

## Architecture Documentation

### 10. Architecture Decision Records (ADRs)
```markdown
# ADR-001: Use FastAPI for Backend

## Status
Accepted

## Context
We need to choose a backend framework for the Stock Insight App.

## Decision
We will use FastAPI as our backend framework.

## Consequences

### Positive
- Fast performance (async support)
- Automatic API documentation
- Type hints and validation
- Easy to learn and use

### Negative
- Smaller ecosystem than Django/Flask
- Less mature than some alternatives

## Alternatives Considered
- Django: Too heavy for our needs
- Flask: Missing async support
- Express.js: Team prefers Python
```

### 11. System Architecture Documentation
```markdown
# System Architecture

## Overview
The Stock Insight App follows a microservices architecture with clear separation between frontend and backend.

## Components

### Frontend (Next.js)
- **Purpose**: User interface and client-side logic
- **Technology**: Next.js 15, React, TypeScript
- **Deployment**: Vercel/Netlify

### Backend (FastAPI)
- **Purpose**: API server, business logic, data processing
- **Technology**: FastAPI, Python 3.11+
- **Deployment**: Docker container on cloud platform

### Database (PostgreSQL)
- **Purpose**: Data persistence
- **Technology**: PostgreSQL 14+
- **Deployment**: Managed database service

## Data Flow
[Include diagram or description]

## API Contracts
[Link to API documentation]
```

## Code Examples Documentation

### 12. Usage Examples
```python
# examples/create_stock.py
"""
Example: Creating a stock via API

This example demonstrates how to create a new stock
using the FastAPI backend.
"""

import asyncio
from app.services.stock_service import StockService
from app.schemas.stock import StockCreate
from app.core.database import get_db

async def main():
    async for db in get_db():
        service = StockService(db)
        
        stock_data = StockCreate(
            symbol="AAPL",
            name="Apple Inc.",
            exchange="NASDAQ"
        )
        
        stock = await service.create_stock(stock_data)
        print(f"Created stock: {stock.symbol} - {stock.name}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Documentation Maintenance

### 13. Keeping Docs Updated
- **Code Changes**: Update docs when code changes
- **Review Docs**: Include docs in code reviews
- **Version Control**: Track doc changes in git
- **Regular Audits**: Periodically audit documentation

### 14. Documentation Review Checklist
- [ ] Code comments explain why, not what
- [ ] All public functions/classes have docstrings
- [ ] API endpoints have descriptions and examples
- [ ] README is up to date
- [ ] Examples work with current code
- [ ] No outdated information

## Documentation Tools

### 15. Documentation Generation
- **Backend**: FastAPI auto-generates OpenAPI docs
- **Frontend**: TypeDoc for TypeScript documentation
- **Markdown**: Use Markdown for all documentation files

### 16. Documentation Standards
- **Markdown**: Use Markdown for all documentation
- **Code Blocks**: Use syntax highlighting in code blocks
- **Links**: Use relative links for internal documentation
- **Images**: Store images in `docs/images/` directory

## Key Rules Summary

1. **Document** why, not what
2. **Keep** documentation in sync with code
3. **Write** for the reader, not the writer
4. **Include** examples in documentation
5. **Update** docs when code changes
6. **Use** docstrings for all public functions
7. **Document** API endpoints with descriptions
8. **Maintain** up-to-date README files
9. **Include** architecture decisions in ADRs
10. **Review** documentation in code reviews
