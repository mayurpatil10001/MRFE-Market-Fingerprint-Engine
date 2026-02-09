"""Data collection pipeline exports."""

from src.infrastructure.data_collection.alphavantage_collector import AlphaVantageArticle, AlphaVantageNewsCollector
from src.infrastructure.data_collection.macro_collector import FREDMacroCollector, MacroObservation
from src.infrastructure.data_collection.market_collector import MarketCandle, MarketDataCollector
from src.infrastructure.data_collection.news_collector import NewsArticle, NewsCollector
from src.infrastructure.data_collection.newsapi_collector import NewsAPIArticle, NewsAPICollector
from src.infrastructure.data_collection.retention import prune_old_files

__all__ = [
    "AlphaVantageArticle",
    "AlphaVantageNewsCollector",
    "FREDMacroCollector",
    "MacroObservation",
    "MarketCandle",
    "MarketDataCollector",
    "NewsArticle",
    "NewsCollector",
    "NewsAPIArticle",
    "NewsAPICollector",
    "prune_old_files",
]
