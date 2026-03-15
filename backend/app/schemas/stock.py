from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class StockBase(BaseModel):
    """Base stock schema with common fields."""
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock ticker symbol")
    name: str = Field(..., min_length=1, max_length=255, description="Company name")
    exchange: str = Field(..., min_length=1, max_length=50, description="Stock exchange")
    sector: Optional[str] = Field(None, max_length=100, description="Industry sector")


class StockCreate(StockBase):
    """Schema for creating a new stock."""
    pass


class StockUpdate(BaseModel):
    """Schema for updating a stock."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    exchange: Optional[str] = Field(None, min_length=1, max_length=50)
    sector: Optional[str] = Field(None, max_length=100)


class StockResponse(StockBase):
    """Schema for stock API response."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StockDataResponse(BaseModel):
    """Schema for live stock data from yfinance."""
    symbol: str
    name: str
    current_price: float = Field(..., description="Current stock price")
    previous_close: float = Field(..., description="Previous closing price")
    change: float = Field(..., description="Price change")
    change_percent: float = Field(..., description="Price change percentage")
    volume: Optional[int] = Field(None, description="Trading volume")
    market_cap: Optional[float] = Field(None, description="Market capitalization")
    currency: str = Field(default="USD", description="Currency")


class StockSearchResult(BaseModel):
    """Schema for a stock search result from yfinance."""
    symbol: str
    name: str
    exchange: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    current_price: Optional[float] = None
    currency: Optional[str] = None
    country: Optional[str] = None
    sparkline: Optional[list[float]] = None


class StockListResponse(BaseModel):
    """Schema for paginated stock list response."""
    data: list[StockResponse]
    meta: dict = Field(
        default_factory=lambda: {
            "page": 1,
            "limit": 20,
            "total": 0,
            "total_pages": 0,
        }
    )


class StockHistoryPoint(BaseModel):
    """A single OHLCV data point for stock history."""
    t: int            # Unix ms timestamp
    o: float          # open
    h: float          # high
    low: float = Field(alias="l")  # low price (OHLC)
    c: float          # close
    v: Optional[int] = None  # volume


class StockHistoryResponse(BaseModel):
    """Schema for stock price history response."""
    symbol: str
    period: str
    data: list[StockHistoryPoint]


class StockInfoResponse(BaseModel):
    """Schema for detailed company information."""
    symbol: str
    description: Optional[str] = None
    website: Optional[str] = None
    employees: Optional[int] = None
    ceo: Optional[str] = None
    country: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    beta: Optional[float] = None
    dividend_yield: Optional[float] = None
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None
    average_volume: Optional[int] = None


class StockNewsItem(BaseModel):
    """A single news item for a stock."""
    title: str
    publisher: Optional[str] = None
    link: Optional[str] = None
    published_at: Optional[int] = None  # Unix ms


class PortfolioNewsItem(StockNewsItem):
    """News item with source symbol for portfolio feed."""
    symbol: str


class StockAIAnalysisResponse(BaseModel):
    """Schema for AI-generated stock analysis."""
    symbol: str
    analysis: str


class CompareSummaryResponse(BaseModel):
    """AI-generated comparison summary for multiple stocks."""
    symbols: list[str]
    summary: str


class SectorPeerResponse(BaseModel):
    """Sector peer with enriched price and fundamentals."""
    symbol: str
    name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    current_price: Optional[float] = None
    day_change_percent: Optional[float] = None
    pe_ratio: Optional[float] = None
    market_cap: Optional[float] = None
    is_current: bool = False  # True if this is the stock being viewed
