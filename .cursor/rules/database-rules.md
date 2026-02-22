# Database Rules: Design & Query Patterns

## Database Design Principles

### 1. Database Choice
- **PostgreSQL**: Use PostgreSQL for relational data
- **SQLAlchemy**: Use SQLAlchemy 2.0 as ORM
- **Async**: Use async SQLAlchemy (`asyncpg`) for all database operations
- **Migrations**: Use Alembic for database migrations

### 2. Schema Design Rules
- **Normalization**: Normalize to 3NF, denormalize only when necessary for performance
- **Naming Conventions**:
  - Tables: `snake_case`, plural (`stocks`, `stock_prices`)
  - Columns: `snake_case` (`created_at`, `user_id`)
  - Indexes: `idx_{table}_{columns}` (`idx_stocks_symbol`)
  - Foreign Keys: `fk_{table}_{referenced_table}` (`fk_stocks_exchange_id`)

### 3. Table Structure
```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

class Stock(Base):
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    exchange_id = Column(Integer, ForeignKey("exchanges.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    exchange = relationship("Exchange", back_populates="stocks")
    prices = relationship("StockPrice", back_populates="stock")
```

## SQLAlchemy Models

### 4. Model Definition Rules
- **Base Class**: Use declarative base for all models
- **Type Hints**: Add type hints to all columns
- **Indexes**: Add indexes on frequently queried columns
- **Constraints**: Use database constraints (unique, foreign keys, check)

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Stock(Base):
    __tablename__ = "stocks"
    
    id: int
    symbol: str
    name: str
    # ... columns
```

### 5. Relationships
- **Explicit Relationships**: Define relationships explicitly
- **Lazy Loading**: Use `selectinload` or `joinedload` for eager loading
- **Back References**: Use `back_populates` for bidirectional relationships
- **Cascade**: Set appropriate cascade options

```python
class Stock(Base):
    # ...
    exchange_id = Column(Integer, ForeignKey("exchanges.id"))
    exchange = relationship("Exchange", back_populates="stocks")

class Exchange(Base):
    # ...
    stocks = relationship("Stock", back_populates="exchange", cascade="all, delete-orphan")
```

## Database Operations

### 6. Async Database Sessions
```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

### 7. Query Patterns
```python
# ✅ Good: Use async session
async def get_stock(db: AsyncSession, symbol: str) -> Optional[Stock]:
    result = await db.execute(
        select(Stock).where(Stock.symbol == symbol)
    )
    return result.scalar_one_or_none()

# ✅ Good: Use selectinload for relationships
async def get_stock_with_prices(db: AsyncSession, symbol: str) -> Optional[Stock]:
    result = await db.execute(
        select(Stock)
        .where(Stock.symbol == symbol)
        .options(selectinload(Stock.prices))
    )
    return result.scalar_one_or_none()

# ❌ Bad: Don't use sync queries
def get_stock_sync(db: Session, symbol: str):  # Don't do this
    return db.query(Stock).filter(Stock.symbol == symbol).first()
```

### 8. CRUD Operations
```python
# Create
async def create_stock(db: AsyncSession, stock_data: StockCreate) -> Stock:
    stock = Stock(**stock_data.dict())
    db.add(stock)
    await db.commit()
    await db.refresh(stock)
    return stock

# Read
async def get_stock(db: AsyncSession, stock_id: int) -> Optional[Stock]:
    result = await db.execute(select(Stock).where(Stock.id == stock_id))
    return result.scalar_one_or_none()

# Update
async def update_stock(
    db: AsyncSession, 
    stock_id: int, 
    stock_data: StockUpdate
) -> Optional[Stock]:
    result = await db.execute(select(Stock).where(Stock.id == stock_id))
    stock = result.scalar_one_or_none()
    if not stock:
        return None
    
    for key, value in stock_data.dict(exclude_unset=True).items():
        setattr(stock, key, value)
    
    await db.commit()
    await db.refresh(stock)
    return stock

# Delete
async def delete_stock(db: AsyncSession, stock_id: int) -> bool:
    result = await db.execute(select(Stock).where(Stock.id == stock_id))
    stock = result.scalar_one_or_none()
    if not stock:
        return False
    
    await db.delete(stock)
    await db.commit()
    return True
```

## Query Optimization

### 9. Indexing Strategy
- **Primary Keys**: Automatically indexed
- **Foreign Keys**: Index foreign key columns
- **Frequently Queried**: Index columns used in WHERE clauses
- **Composite Indexes**: Create composite indexes for multi-column queries
- **Unique Constraints**: Use unique constraints (creates index automatically)

```python
from sqlalchemy import Index

# Single column index
symbol = Column(String(10), index=True)

# Composite index
Index('idx_stocks_exchange_symbol', Stock.exchange_id, Stock.symbol)

# Unique index
symbol = Column(String(10), unique=True)
```

### 10. Eager Loading
```python
from sqlalchemy.orm import selectinload, joinedload

# ✅ Good: Use selectinload for one-to-many
result = await db.execute(
    select(Stock)
    .options(selectinload(Stock.prices))
    .where(Stock.symbol == symbol)
)

# ✅ Good: Use joinedload for many-to-one
result = await db.execute(
    select(StockPrice)
    .options(joinedload(StockPrice.stock))
    .where(StockPrice.stock_id == stock_id)
)
```

### 11. Pagination
```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def get_stocks_paginated(
    db: AsyncSession,
    page: int = 1,
    limit: int = 20
) -> tuple[list[Stock], int]:
    # Count total
    count_result = await db.execute(select(func.count(Stock.id)))
    total = count_result.scalar()
    
    # Get paginated results
    offset = (page - 1) * limit
    result = await db.execute(
        select(Stock)
        .offset(offset)
        .limit(limit)
        .order_by(Stock.symbol)
    )
    stocks = result.scalars().all()
    
    return stocks, total
```

### 12. Query Optimization Rules
- **Avoid N+1 Queries**: Use eager loading (selectinload, joinedload)
- **Use Select**: Use `select()` instead of `query()` (SQLAlchemy 2.0)
- **Limit Results**: Always limit results in list queries
- **Use Indexes**: Ensure queries use indexes
- **Avoid SELECT ***: Select only needed columns when possible

## Migrations

### 13. Alembic Migrations
```python
# Create migration
alembic revision --autogenerate -m "create stocks table"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### 14. Migration Best Practices
- **Review Generated Migrations**: Always review auto-generated migrations
- **Test Migrations**: Test migrations on development database first
- **Backup**: Backup database before running migrations in production
- **Rollback Plan**: Always have a rollback plan
- **Data Migrations**: Handle data migrations separately from schema migrations

## Transactions

### 15. Transaction Management
```python
async def transfer_stock(
    db: AsyncSession,
    from_user_id: int,
    to_user_id: int,
    stock_id: int
):
    async with db.begin():
        # All operations in transaction
        stock = await get_stock(db, stock_id)
        # ... transfer logic
        await db.commit()  # Or rollback on error
```

### 16. Error Handling in Transactions
```python
async def create_stock_with_prices(
    db: AsyncSession,
    stock_data: StockCreate,
    prices: list[PriceCreate]
):
    try:
        stock = await create_stock(db, stock_data)
        for price_data in prices:
            price = StockPrice(stock_id=stock.id, **price_data.dict())
            db.add(price)
        await db.commit()
        return stock
    except Exception:
        await db.rollback()
        raise
```

## Data Validation

### 17. Database Constraints
- **NOT NULL**: Use for required fields
- **UNIQUE**: Use for unique fields (symbols, emails)
- **CHECK**: Use for value constraints (price > 0)
- **FOREIGN KEY**: Use for referential integrity

```python
from sqlalchemy import CheckConstraint

class StockPrice(Base):
    __tablename__ = "stock_prices"
    
    price = Column(Numeric(10, 2), nullable=False)
    
    __table_args__ = (
        CheckConstraint('price > 0', name='check_positive_price'),
    )
```

## Repository Pattern (Optional)

### 18. Repository Layer
```python
from abc import ABC, abstractmethod
from typing import Optional, List

class StockRepository(ABC):
    @abstractmethod
    async def get_by_symbol(self, symbol: str) -> Optional[Stock]:
        pass
    
    @abstractmethod
    async def create(self, stock_data: StockCreate) -> Stock:
        pass

class SQLStockRepository(StockRepository):
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_symbol(self, symbol: str) -> Optional[Stock]:
        result = await self.db.execute(
            select(Stock).where(Stock.symbol == symbol)
        )
        return result.scalar_one_or_none()
    
    async def create(self, stock_data: StockCreate) -> Stock:
        stock = Stock(**stock_data.dict())
        self.db.add(stock)
        await self.db.commit()
        await self.db.refresh(stock)
        return stock
```

## Connection Pooling

### 19. Connection Pool Configuration
```python
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before using
    echo=False,  # Set to True for SQL logging in development
)
```

## Key Rules Summary

1. **Always** use async SQLAlchemy operations
2. **Use** Alembic for all database migrations
3. **Index** frequently queried columns
4. **Use** eager loading to avoid N+1 queries
5. **Always** paginate list queries
6. **Use** transactions for multi-step operations
7. **Validate** data with database constraints
8. **Handle** errors and rollback transactions
9. **Review** auto-generated migrations before applying
10. **Test** migrations on development database first
