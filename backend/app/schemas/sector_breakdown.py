from pydantic import BaseModel


class SectorSlice(BaseModel):
    sector: str
    total_value: float
    weight_pct: float
    symbols: list[str]
    num_holdings: int


class SectorBreakdownResponse(BaseModel):
    sectors: list[SectorSlice]
    total_value: float
