"""Agent registry — import and register all agents here."""
from app.agents.market_scanner import MarketScannerAgent
from app.agents.portfolio_health import PortfolioHealthAgent
from app.agents.registry import AgentRegistry
from app.agents.sector_trend import SectorTrendAgent
from app.agents.stock_deep_dive import StockDeepDiveAgent

AgentRegistry.register(StockDeepDiveAgent())
AgentRegistry.register(PortfolioHealthAgent())
AgentRegistry.register(MarketScannerAgent())
AgentRegistry.register(SectorTrendAgent())
