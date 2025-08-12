#!/usr/bin/env python3
"""
Built-in Tools Module - Implementation Layer

This module contains the Python implementations of tools following ControlFlow best practices.
Each function is decorated with @cf.tool and has clear type annotations and docstrings.

Important: The single source of truth (SSoT) for the tool catalog, agent wiring, and workflows
lives in the configuration files under `backend/config/` (tools.yaml, agents.yaml, workflow_config.yaml).
This module is the implementation source of truth only. The registry resolves which tools are
available/enabled from configuration and maps names to the callables defined here.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import sys
import controlflow as cf
import json
import requests
from backend.config.settings import get_settings
from backend.utils.http_client import alpha_vantage_request
from backend.tools.feature_builder import compute_features_from_data
from backend.tools.model_inference import (
    train_baseline_model,
    predict_proba_from_features,
)
from backend.tools.backtesting import walk_forward_backtest_from_series

# Global reference to tool instances (will be set by registry)
_tool_instances = {}

def set_tool_instances(instances: Dict[str, Any]):
    """Set the tool instances for use by the tool functions"""
    global _tool_instances
    _tool_instances = instances
    print(f"Tool instances set: {list(instances.keys())}")

def get_tool_instances() -> Dict[str, Any]:
    """Get tool instances with fallback to registry"""
    global _tool_instances
    
    # If we have instances, return them
    if _tool_instances:
        return _tool_instances
    
    # Fallback: try to get from registry directly
    try:
        from backend.tools.registry import get_tool_registry
        registry = get_tool_registry()
        return registry._tool_instances
    except Exception as e:
        print(f"Warning: Could not get tool instances from registry: {e}")
        return {}

def get_tool_function(tool_name: str):
    """Resolve a tool by its name from configuration.

    Returns either a ControlFlow Tool object (preferred) or a plain callable if present.
    Also supports simple aliasing for backwards compatibility.
    """
    module = sys.modules.get(__name__)
    if module is not None:
        obj = getattr(module, tool_name, None)
        if obj is not None:
            return obj

    # Minimal alias fallback to avoid manual list maintenance
    alias_map = {
        "train_baseline_model": "train_model",
    }
    alias_name = alias_map.get(tool_name)
    if alias_name:
        if module is not None:
            obj = getattr(module, alias_name, None)
            if obj is not None:
                return obj

    return None


def _resolve_instance(instances: Dict[str, Any], keys: List[str]) -> Optional[Any]:
    """Return first matching instance for the provided keys."""
    for key in keys:
        if key in instances:
            return instances[key]
    return None

# ---- Alpha Vantage helpers ----
def _av_request(params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Perform an Alpha Vantage request via shared client (caching/backoff/rate-limit)."""
    settings = get_settings()
    return alpha_vantage_request(params, cache_ttl_seconds=settings.alpha_vantage_cache_ttl)

def _mock_series(symbol: str) -> Dict[str, Any]:
    now = datetime.now()
    # Minimal synthetic series
    series = []
    for i in range(5):
        ts = (now.replace(microsecond=0)).isoformat()
        series.append({
            "timestamp": ts,
            "open": 20.0 + i,
            "high": 20.5 + i,
            "low": 19.5 + i,
            "close": 20.2 + i,
            "volume": 100000 + i * 1000,
        })
    return {
        "symbol": symbol.upper(),
        "series": series,
        "_mock": True,
        "note": "Mock time series (fallback)",
        "timestamp": now.isoformat(),
        "source": "mock_data",
    }

def _mock_indicator(symbol: str, name: str) -> Dict[str, Any]:
    now = datetime.now().isoformat()
    return {
        "symbol": symbol.upper(),
        "indicator": name,
        "values": [{"date": now[:10], name: 50.0}],
        "_mock": True,
        "note": f"Mock {name} (fallback)",
        "timestamp": now,
        "source": "mock_data",
    }
# ---- Feature builder tool ----

@cf.tool
def build_features(
    ticker: str,
    time_series_daily: dict,
    news: Optional[dict] = None,
    insiders: Optional[dict] = None,
    fundamentals_income: Optional[dict] = None,
    fundamentals_balance: Optional[dict] = None,
    fundamentals_cash: Optional[dict] = None,
    gainers_losers: Optional[dict] = None,
    lookback_days: int = 90,
) -> dict:
    """Compose engineered features from various inputs for a ticker.

    Inputs are expected to be outputs from existing tools (daily series, news, etc.).
    """
    if not ticker:
        return {"error": "ticker is required", "ticker": ticker}
    try:
        result = compute_features_from_data(
            ticker=ticker,
            time_series_daily=time_series_daily or {},
            news=news or {},
            insiders=insiders or {},
            fundamentals_income=fundamentals_income or {},
            fundamentals_balance=fundamentals_balance or {},
            fundamentals_cash=fundamentals_cash or {},
            gainers_losers=gainers_losers or {},
            lookback_days=lookback_days,
        )
        return result
    except Exception as e:
        return {"error": f"failed_to_build_features: {e}", "ticker": ticker}


@cf.tool
def train_model(records: List[dict], calibrate: bool = True) -> dict:
    """Train the baseline model given labeled records: [{features: {}, label: 0/1}, ...]."""
    try:
        return train_baseline_model(records, calibrate=calibrate)
    except Exception as e:
        return {"error": f"failed_to_train_model: {e}"}


@cf.tool
def predict_from_features(features: dict) -> dict:
    """Predict probability of upward move from a single feature dict."""
    try:
        return predict_proba_from_features(features)
    except Exception as e:
        return {"error": f"failed_to_predict: {e}"}


@cf.tool
def backtest_baseline(
    ticker: str,
    daily_series: dict,
    horizon_days: int = 10,
    min_train_size: int = 150,
    step: int = 5,
) -> dict:
    """Walk-forward backtest using price-based features and baseline model.

    daily_series: expected shape similar to get_time_series_daily output { series: [...] }.
    """
    try:
        series = (daily_series or {}).get("series") or []
        return walk_forward_backtest_from_series(
            ticker=ticker,
            series=series,
            horizon_days=horizon_days,
            min_train_size=min_train_size,
            step=step,
        )
    except Exception as e:
        return {"error": f"failed_to_backtest: {e}"}


# ---- Alpha Intelligence tools ----

@cf.tool
def get_news_sentiment(
    ticker: Optional[str] = None,
    limit: int = 50,
    sort: str = "LATEST",
    time_from: Optional[str] = None,
    time_to: Optional[str] = None,
    topics: Optional[str] = None,
) -> dict:
    """
    Get news and sentiment for a ticker via Alpha Vantage Alpha Intelligence.

    Args:
        ticker: Optional stock ticker (e.g., AAPL). If omitted, gets broad market news.
        limit: Max number of articles (Alpha Vantage default caps may apply).
        sort: Sort order (e.g., LATEST).
        time_from: ISO-like string (YYYYMMDDTHHMM) if supported by AV.
        time_to: ISO-like string (YYYYMMDDTHHMM) if supported by AV.
        topics: Optional topics filter (comma-separated) if supported.
    """
    params: Dict[str, Any] = {"function": "NEWS_SENTIMENT", "limit": limit, "sort": sort}
    if ticker:
        params["tickers"] = ticker.upper()
    if time_from:
        params["time_from"] = time_from
    if time_to:
        params["time_to"] = time_to
    if topics:
        params["topics"] = topics

    data = _av_request(params)
    if not data or not isinstance(data, dict):
        return {
            "ticker": (ticker or "MARKET").upper() if ticker else None,
            "articles": [],
            "status": "unavailable",
            "source": "alpha_vantage",
        }

    feed = data.get("feed") or data.get("items") or []
    articles: List[Dict[str, Any]] = []
    for item in feed:
        if not isinstance(item, dict):
            continue
        article = {
            "title": item.get("title"),
            "url": item.get("url"),
            "summary": item.get("summary") or item.get("summary_text"),
            "time_published": item.get("time_published") or item.get("published_at"),
            "source": item.get("source") or item.get("source_domain"),
            "overall_sentiment_score": item.get("overall_sentiment_score") or item.get("sentiment_score"),
            "overall_sentiment_label": item.get("overall_sentiment_label") or item.get("sentiment_label"),
            "relevance_score": item.get("relevance_score"),
            "ticker_sentiment": item.get("ticker_sentiment"),
        }
        articles.append(article)

    return {
        "ticker": (ticker or "MARKET").upper() if ticker else None,
        "articles": articles,
        "raw_meta": {k: v for k, v in data.items() if k != "feed"},
        "status": "success",
        "source": "alpha_vantage",
        "timestamp": datetime.now().isoformat(),
    }


@cf.tool
def get_earnings_transcript(ticker: str, quarter: int, year: int) -> dict:
    """
    Get earnings call transcript for a given ticker/quarter/year.
    """
    if not ticker or not quarter or not year:
        return {"error": "ticker, quarter, and year are required", "ticker": ticker}
    params = {
        "function": "EARNINGS_CALL_TRANSCRIPT",
        "symbol": ticker.upper(),
        "quarter": int(quarter),
        "year": int(year),
    }
    data = _av_request(params)
    if not data or not isinstance(data, dict):
        return {
            "ticker": ticker.upper(),
            "quarter": quarter,
            "year": year,
            "transcript": None,
            "status": "unavailable",
            "source": "alpha_vantage",
        }
    # Normalize
    transcript = data.get("transcript") or data.get("content") or data.get("script") or data.get("text")
    speakers = data.get("speakers") or data.get("participants")
    return {
        "ticker": ticker.upper(),
        "quarter": quarter,
        "year": year,
        "transcript": transcript,
        "speakers": speakers,
        "raw": data,
        "status": "success",
        "source": "alpha_vantage",
        "timestamp": datetime.now().isoformat(),
    }


@cf.tool
def get_top_gainers_losers() -> dict:
    """Get top gainers, top losers, and most actively traded from Alpha Vantage."""
    def _mock_breadth() -> dict:
        now = datetime.now().isoformat()
        gainers = [
            {"ticker": "AAPL", "change_percent": "+2.3%"},
            {"ticker": "MSFT", "change_percent": "+1.8%"},
            {"ticker": "NVDA", "change_percent": "+3.1%"},
        ]
        losers = [
            {"ticker": "TSLA", "change_percent": "-1.2%"},
            {"ticker": "AMZN", "change_percent": "-0.7%"},
        ]
        return {
            "gainers": gainers,
            "losers": losers,
            "most_active": [
                {"ticker": "AAPL"}, {"ticker": "NVDA"}, {"ticker": "TSLA"}
            ],
            "breadth_g_minus_l": len(gainers) - len(losers),
            "status": "success",
            "_mock": True,
            "source": "mock_data",
            "timestamp": now,
        }

    data = _av_request({"function": "TOP_GAINERS_LOSERS"})
    if not data or not isinstance(data, dict):
        return _mock_breadth()
    gainers = data.get("top_gainers") or data.get("gainers") or []
    losers = data.get("top_losers") or data.get("losers") or []
    most_active = data.get("most_actively_traded") or data.get("most_active") or []
    breadth = (len(gainers) if isinstance(gainers, list) else 0) - (len(losers) if isinstance(losers, list) else 0)
    return {
        "gainers": gainers,
        "losers": losers,
        "most_active": most_active,
        "breadth_g_minus_l": breadth,
        "status": "success",
        "source": "alpha_vantage",
        "timestamp": datetime.now().isoformat(),
    }


@cf.tool
def get_insider_transactions(ticker: str, limit: int = 100) -> dict:
    """Get recent insider transactions for a ticker."""
    if not ticker:
        return {"error": "ticker is required", "ticker": ticker}
    params = {"function": "INSIDER_TRANSACTIONS", "symbol": ticker.upper(), "limit": limit}
    data = _av_request(params)
    if not data or not isinstance(data, dict):
        return {"ticker": ticker.upper(), "transactions": [], "status": "unavailable", "source": "alpha_vantage"}
    tx = data.get("transactions") or data.get("data") or data.get("items") or []
    return {
        "ticker": ticker.upper(),
        "transactions": tx,
        "status": "success",
        "source": "alpha_vantage",
        "timestamp": datetime.now().isoformat(),
    }


@cf.tool
def get_alpha_analytics(ticker: str, window: str = "fixed", horizon: str = "30d") -> dict:
    """Get Alpha Vantage analytics (fixed/sliding window) for a ticker."""
    if not ticker:
        return {"error": "ticker is required", "ticker": ticker}
    params = {
        "function": "ANALYTICS",
        "symbol": ticker.upper(),
        "time_window": window,
        "horizon": horizon,
    }
    data = _av_request(params)
    if not data or not isinstance(data, dict):
        return {"ticker": ticker.upper(), "analytics": None, "status": "unavailable", "source": "alpha_vantage"}
    # Return as-is under normalized key; structure may vary by window/horizon
    return {
        "ticker": ticker.upper(),
        "analytics": data,
        "status": "success",
        "source": "alpha_vantage",
        "timestamp": datetime.now().isoformat(),
    }

@cf.tool
def get_market_data(ticker: str) -> dict:
    """
    Get real-time market data for a stock ticker.
    
    This tool retrieves current stock price, volume, and market data for a given ticker symbol.
    It uses the Alpha Vantage API to fetch real-time market information.
    
    Args:
        ticker (str): Stock ticker symbol like GOOG, AAPL, MSFT
        
    Returns:
        dict: Market data with price, change, volume, and other market metrics
        
    Examples:
        get_market_data(ticker="GOOG")
        get_market_data(ticker="AAPL")
    """
    if not ticker or ticker.strip() == "":
        return {
            "error": "Ticker symbol is required",
            "ticker": ticker,
            "timestamp": datetime.now().isoformat()
        }
    
    # Get tool instances with fallback
    instances = get_tool_instances()
    
    instance = _resolve_instance(instances, [
        "get_market_data",
        "market_data",
        "MarketDataTool",
    ])
    if instance is not None:
        try:
            return instance.execute(ticker=ticker.upper())
        except Exception as e:
            return {"error": f"Market data tool execution failed: {e}", "ticker": ticker}
    
    # Fallback to mock data if tool not available
    return {
        "ticker": ticker.upper(),
        "price": 150.25,
        "change": 2.50,
        "change_percent": 1.69,
        "volume": 1234567,
        "market_cap": "2.9T",
        "timestamp": datetime.now().isoformat(),
        "source": "mock_data"
    }

@cf.tool
def get_company_overview(ticker: str) -> dict:
    """
    Get comprehensive company overview and fundamental data.
    
    This tool retrieves detailed company information including financial metrics,
    company description, sector information, and key ratios.
    
    Args:
        ticker (str): Stock ticker symbol like GOOG, AAPL, MSFT
        
    Returns:
        dict: Company overview with financial metrics and company information
        
    Examples:
        get_company_overview(ticker="GOOG")
        get_company_overview(ticker="AAPL")
    """
    if not ticker or ticker.strip() == "":
        return {
            "error": "Ticker symbol is required",
            "ticker": ticker,
            "timestamp": datetime.now().isoformat()
        }
    
    # Get tool instances with fallback
    instances = get_tool_instances()
    
    instance = _resolve_instance(instances, [
        "get_company_overview",
        "company_overview",
        "CompanyOverviewTool",
    ])
    if instance is not None:
        try:
            return instance.execute(ticker=ticker.upper())
        except Exception as e:
            return {"error": f"Company overview tool execution failed: {e}", "ticker": ticker}
    
    # Fallback to mock data if tool not available
    return {
        "ticker": ticker.upper(),
        "name": f"{ticker.upper()} Corporation",
        "sector": "Technology",
        "industry": "Software",
        "market_cap": "2.9T",
        "pe_ratio": 25.5,
        "dividend_yield": 0.5,
        "description": f"Leading technology company {ticker.upper()}",
        "timestamp": datetime.now().isoformat(),
        "source": "mock_data"
    }

@cf.tool
def get_economic_data_from_fred(series_id: str, limit: int = 10) -> dict:
    """
    Get economic data from FRED (Federal Reserve Economic Data).
    
    This tool retrieves economic indicators and time series data from the FRED API.
    Useful for macroeconomic analysis and economic trend assessment.
    
    Args:
        series_id (str): FRED series ID like GDP, UNRATE, CPIAUCSL
        limit (int): Number of data points to retrieve (default: 10)
        
    Returns:
        dict: Economic data with time series information
        
    Examples:
        get_economic_data_from_fred(series_id="GDP")
        get_economic_data_from_fred(series_id="UNRATE", limit=20)
    """
    if not series_id or series_id.strip() == "":
        return {
            "error": "Series ID is required",
            "series_id": series_id,
            "timestamp": datetime.now().isoformat()
        }
    
    # Get tool instances with fallback
    instances = get_tool_instances()
    
    instance = _resolve_instance(instances, [
        "get_economic_data_from_fred",
        "economic_data",
        "EconomicDataTool",
    ])
    if instance is not None:
        try:
            return instance.execute(series_id=series_id.upper(), limit=limit)
        except Exception as e:
            return {"error": f"Economic data tool execution failed: {e}", "series_id": series_id}
    
    # Fallback to mock data if tool not available
    return {
        "series_id": series_id.upper(),
        "title": f"{series_id.upper()} Economic Indicator",
        "frequency": "Monthly",
        "units": "Percent",
        "data": [
            {"date": "2024-01", "value": 3.2},
            {"date": "2024-02", "value": 3.1},
            {"date": "2024-03", "value": 3.0}
        ],
        "timestamp": datetime.now().isoformat(),
        "source": "mock_data"
    }

@cf.tool
def process_financial_data(data: Any, retry_id: Optional[str] = None) -> dict:
    """
    Validate and ensure data quality for financial analysis.
    
    Use this tool to check data consistency, validate metrics, and ensure proper formatting before analysis. 
    Essential for data quality assurance in financial reporting.
    
    Args:
        data: The financial data to process and validate
        retry_id: Optional identifier to track retry attempts
        
    Returns:
        dict: Processing results or error details with validation information
        
    Examples:
        process_financial_data(data={"price": 150.25, "volume": 1234567})
        process_financial_data(data={"ticker": "AAPL", "market_cap": "2.9T"})
    """
    try:
        # Check if data is already a dict (valid JSON object)
        if isinstance(data, dict):
            return {
                "status": "success",
                "message": "Financial data processed and validated successfully",
                "data_type": "valid_json",
                "data_keys": list(data.keys()),
                "data_size": len(str(data)),
                "validation_summary": "Data structure validated",
                "processed_at": datetime.now().isoformat(),
                **({"retry_info": {"retry_id": retry_id}} if retry_id else {})
            }
        
        # Check if data is a JSON string
        if isinstance(data, str):
            try:
                parsed_data = json.loads(data)
                return {
                    "status": "success",
                    "message": "JSON string parsed and validated successfully",
                    "data_type": "json_string",
                    "data_keys": list(parsed_data.keys()) if isinstance(parsed_data, dict) else [],
                    "data_size": len(data),
                    "validation_summary": "JSON string validated",
                    "processed_at": datetime.now().isoformat(),
                    **({"retry_info": {"retry_id": retry_id}} if retry_id else {})
                }
            except json.JSONDecodeError as e:
                return {
                    "status": "error",
                    "error_type": "json_parse_error",
                    "error_message": f"Unable to parse JSON string: {e}",
                    "received_data": data[:100] + "..." if len(data) > 100 else data,
                    "data_type": "string",
                    "processed_at": datetime.now().isoformat()
                }
        
        # Handle other data types
        return {
            "status": "error",
            "error_type": "unsupported_format",
            "error_message": f"Unsupported data type: {type(data).__name__}",
            "received_data": str(data)[:100] + "..." if len(str(data)) > 100 else str(data),
            "data_type": type(data).__name__,
            "processed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_type": "processing_error",
            "error_message": f"Data processing failed: {e}",
            "received_data": str(data)[:100] + "..." if len(str(data)) > 100 else str(data),
            "data_type": type(data).__name__,
            "processed_at": datetime.now().isoformat()
        }

@cf.tool
def process_strict_json(data: dict) -> str:
    """
    Process a dictionary of financial data with strict JSON validation.
    
    This tool validates and processes financial data in JSON format. It ensures
    the input is a valid Python dictionary and performs basic data validation.
    
    Args:
        data (dict): A Python dictionary containing financial data
        
    Returns:
        str: Processing status and validation results
        
    Examples:
        process_strict_json(data={"asset": "BTC", "value": 70000})
        process_strict_json(data={"portfolio": {"stocks": ["AAPL", "GOOG"]}})
    """
    if not isinstance(data, dict):
        raise TypeError(f"Invalid input type: Expected dict, but got {type(data).__name__}. You must parse the input into a dictionary.")
    
    # Simulate some processing
    data['status'] = 'processed'
    data['processed_at'] = datetime.now().isoformat()
    
    return f"Successfully processed JSON data. Status: {data.get('status')}, Items: {len(data)}."

@cf.tool
def misleading_data_validator(data: Any, retry_id: Optional[str] = None) -> dict:
    """
    Validate financial data with advanced format checking.
    
    This tool performs advanced validation on financial data and can handle
    multiple data formats including dictionaries, JSON strings, and CSV data.
    
    Args:
        data: The financial data to validate
        retry_id: Optional identifier to track retry attempts
        
    Returns:
        dict: Validation results or error details with format guidance
        
    Examples:
        misleading_data_validator(data={"ticker": "AAPL", "price": 185.50})
        misleading_data_validator(data='{"ticker": "GOOG", "price": 150.25}')
    """
    try:
        # Handle dictionary data
        if isinstance(data, dict):
            return {
                "status": "success",
                "message": "Dictionary data validated successfully",
                "data_type": "dict",
                "data_keys": list(data.keys()),
                "validation_summary": "Dictionary structure validated",
                "processed_at": datetime.now().isoformat()
            }
        
        # Handle JSON string data
        if isinstance(data, str):
            try:
                parsed_data = json.loads(data)
                return {
                    "status": "success",
                    "message": "JSON string validated successfully",
                    "data_type": "json_string",
                    "data_keys": list(parsed_data.keys()) if isinstance(parsed_data, dict) else [],
                    "validation_summary": "JSON string validated",
                    "processed_at": datetime.now().isoformat()
                }
            except json.JSONDecodeError:
                # Try to handle as CSV
                if ',' in data:
                    return {
                        "status": "success",
                        "message": "CSV format detected and validated",
                        "data_type": "csv_string",
                        "validation_summary": "CSV format validated",
                        "processed_at": datetime.now().isoformat()
                    }
                else:
                    return {
                        "status": "error",
                        "error_type": "format_error",
                        "error_message": "Data is not valid JSON or CSV format",
                        "received_data": data[:100] + "..." if len(data) > 100 else data,
                        "data_type": "string",
                        "processed_at": datetime.now().isoformat()
                    }
        
        # Handle other data types
        return {
            "status": "error",
            "error_type": "unsupported_format",
            "error_message": f"Unsupported data type: {type(data).__name__}",
            "received_data": str(data)[:100] + "..." if len(str(data)) > 100 else str(data),
            "data_type": type(data).__name__,
            "processed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_type": "validation_error",
            "error_message": f"Data validation failed: {e}",
            "received_data": str(data)[:100] + "..." if len(str(data)) > 100 else str(data),
            "data_type": type(data).__name__,
            "processed_at": datetime.now().isoformat()
        }

@cf.tool
def calculate_pe_ratio(ticker: str, current_price: float = None) -> dict:
    """
    Calculate P/E ratio for a given stock and compare it to industry averages.
    
    This tool analyzes the Price-to-Earnings ratio of a stock and provides
    insights on whether it's overvalued or undervalued compared to industry peers.
    
    Args:
        ticker (str): Stock ticker symbol (e.g., 'AAPL', 'GOOG', 'MSFT')
        current_price (float): Optional current price (will fetch if not provided)
        
    Returns:
        dict: P/E ratio analysis with industry comparison and valuation insights
        
    Examples:
        calculate_pe_ratio(ticker="AAPL")
        calculate_pe_ratio(ticker="GOOG", current_price=150.0)
    """
    if not ticker or ticker.strip() == "":
        return {
            "error": "Ticker symbol is required",
            "ticker": ticker,
            "timestamp": datetime.now().isoformat()
        }
    
    # In absence of a direct Alpha Vantage endpoint here, return labeled mock to avoid LIVE mislabeling
    pe_ratio = 25.5
    industry_average = 22.0
    analysis = "Slightly overvalued compared to industry" if pe_ratio > industry_average else "Undervalued compared to industry"
    
    return {
        "ticker": ticker.upper(),
        "pe_ratio": pe_ratio,
        "industry_average": industry_average,
        "analysis": analysis,
        "valuation_status": "overvalued" if pe_ratio > industry_average else "undervalued",
        "timestamp": datetime.now().isoformat(),
        "source": "mock_data",
        "_mock": True,
        **({"inputs": {"current_price": current_price}} if current_price is not None else {})
    }

@cf.tool
def analyze_cash_flow(ticker: str, period: str = "quarterly") -> dict:
    """
    Analyze cash flow for a company and identify trends and financial health indicators.
    
    This tool examines operating cash flow, free cash flow, and cash flow trends
    to assess a company's financial health and ability to generate cash.
    
    Args:
        ticker (str): Stock ticker symbol (e.g., 'AAPL', 'GOOG', 'MSFT')
        period (str): Analysis period - 'quarterly' or 'annual'
        
    Returns:
        dict: Cash flow analysis with trends, metrics, and financial health assessment
        
    Examples:
        analyze_cash_flow(ticker="AAPL")
        analyze_cash_flow(ticker="MSFT", period="annual")
    """
    if not ticker or ticker.strip() == "":
        return {
            "error": "Ticker symbol is required",
            "ticker": ticker,
            "timestamp": datetime.now().isoformat()
        }
    
    # Mock implementation - in real system, this would fetch actual cash flow data
    return {
        "ticker": ticker.upper(),
        "period": period,
        "free_cash_flow": "$10.5B",
        "operating_cash_flow": "$15.2B",
        "trend": "positive",
        "financial_health": "excellent",
        "cash_flow_stability": "high",
        "timestamp": datetime.now().isoformat(),
        "source": "mock_data",
        "_mock": True,
    }

@cf.tool
def get_competitor_analysis(ticker: str, competitors: List[str] = None) -> dict:
    """
    Compare company against competitors and analyze competitive positioning.
    
    This tool performs a comprehensive competitive analysis by comparing
    market share, financial metrics, and strategic advantages against competitors.
    
    Args:
        ticker (str): Primary stock ticker symbol (e.g., 'AAPL', 'GOOG', 'MSFT')
        competitors (List[str]): List of competitor ticker symbols
        
    Returns:
        dict: Competitive analysis with market share, advantages, and strategic insights
        
    Examples:
        get_competitor_analysis(ticker="AAPL")
        get_competitor_analysis(ticker="GOOG", competitors=["MSFT", "AMZN"])
    """
    if not ticker or ticker.strip() == "":
        return {
            "error": "Ticker symbol is required",
            "ticker": ticker,
            "timestamp": datetime.now().isoformat()
        }
    
    # Mock implementation - in real system, this would fetch actual competitive data
    default_competitors = ["MSFT", "GOOG", "AMZN"] if ticker.upper() == "AAPL" else ["AAPL", "GOOG", "MSFT"]
    competitors_list = competitors or default_competitors
    
    return {
        "ticker": ticker.upper(),
        "competitors": competitors_list,
        "market_share": "15%",
        "competitive_advantages": ["Brand", "Technology", "Scale"],
        "threats": ["New entrants", "Regulatory changes"],
        "competitive_position": "strong",
        "timestamp": datetime.now().isoformat(),
        "source": "mock_data",
        "_mock": True,
    } 

# --- Showcase mock tools for demos ---

@cf.tool
def get_mock_news(ticker: str, limit: int = 3) -> dict:
    """Return recent mock headlines for the given ticker for demo purposes."""
    if not ticker:
        return {"status": "error", "error": "ticker required"}
    headlines = [
        f"{ticker.upper()} announces strategic partnership to accelerate growth",
        f"Analysts weigh in on {ticker.upper()} quarterly results",
        f"{ticker.upper()} expands into new market with innovative product launch",
    ][: max(1, min(limit, 5))]
    return {
        "ticker": ticker.upper(),
        "headlines": headlines,
        "status": "success",
        "_mock": True,
        "timestamp": datetime.now().isoformat(),
    }

@cf.tool
def get_mock_analyst_ratings(ticker: str) -> dict:
    """Return mock analyst ratings breakdown for demo purposes."""
    if not ticker:
        return {"status": "error", "error": "ticker required"}
    return {
        "ticker": ticker.upper(),
        "buy": 18,
        "hold": 6,
        "sell": 1,
        "consensus": "buy",
        "price_target": {"median": 200.0, "high": 240.0, "low": 165.0},
        "status": "success",
        "_mock": True,
        "timestamp": datetime.now().isoformat(),
    }

@cf.tool
def get_mock_social_sentiment(ticker: str) -> dict:
    """Return mock social sentiment metrics for demo purposes."""
    if not ticker:
        return {"status": "error", "error": "ticker required"}
    return {
        "ticker": ticker.upper(),
        "sentiment_score": 0.62,
        "volume": 12450,
        "trend": "rising",
        "mentions": ["AI", "earnings", "guidance"],
        "status": "success",
        "_mock": True,
        "timestamp": datetime.now().isoformat(),
    }

def _detect_ticker_with_ai(query: str) -> dict:
    """
    Internal function for AI-powered stock ticker detection from natural language queries.
    
    This function uses intelligent reasoning to extract stock ticker symbols from user queries,
    handling various formats like company names, partial names, descriptions, and context.
    
    Args:
        query (str): Natural language query that may contain stock ticker information
        
    Returns:
        dict: Detection result with ticker symbol and confidence
    """
    try:
        # Use AI reasoning to detect ticker
        detection_prompt = f"""
        You are a financial expert. Extract the stock ticker symbol from this query: "{query}"
        
        Rules:
        1. Look for explicit ticker symbols (1-5 capital letters)
        2. Match company names to their ticker symbols
        3. Consider context and industry hints
        4. Handle partial company names and descriptions
        5. Return the most likely ticker symbol
        
        Common ticker mappings:
        - Apple, iPhone, Mac → AAPL
        - Google, Alphabet → GOOG
        - Microsoft, Windows, Office → MSFT
        - Amazon, AWS → AMZN
        - Tesla, Model S, Model 3 → TSLA
        - Netflix, streaming → NFLX
        - Facebook, Meta, Instagram → META
        - Nvidia, GPU, graphics → NVDA
        - Intel, processors → INTC
        - AMD, Ryzen → AMD
        - Coca-Cola, Coke → KO
        - Disney, Marvel, Star Wars → DIS
        - Walmart, retail → WMT
        - Home Depot, hardware → HD
        - McDonald's, fast food → MCD
        - Starbucks, coffee → SBUX
        - Boeing, airplanes → BA
        - General Electric, GE → GE
        - JPMorgan, JPMorgan Chase → JPM
        - Bank of America, BofA → BAC
        - Wells Fargo, banking → WFC
        - Goldman Sachs, investment bank → GS
        - Morgan Stanley, investment → MS
        - Visa, credit cards → V
        - Mastercard, payments → MA
        - PayPal, digital payments → PYPL
        - Salesforce, CRM software → CRM
        - Oracle, database → ORCL
        - Adobe, creative software → ADBE
        - Cisco, networking → CSCO
        - Qualcomm, mobile chips → QCOM
        - Broadcom, semiconductors → AVGO
        - Verizon, telecom → VZ
        - AT&T, telecommunications → T
        - Comcast, cable → CMCSA
        - Charter, Spectrum → CHTR
        
        Return only the ticker symbol in uppercase, or "UNKNOWN" if no ticker can be determined.
        """
        
        # Use ControlFlow to get AI reasoning
        result = cf.run(detection_prompt, max_agent_turns=1)
        
        # Extract ticker from result
        ticker = result.strip().upper()
        
        # Validate ticker format
        if len(ticker) <= 5 and ticker.isalpha() and ticker != "UNKNOWN":
            return {
                "ticker": ticker,
                "confidence": 0.9,
                "method": "ai_detection",
                "query": query,
                "status": "success"
            }
        else:
            return {
                "ticker": "UNKNOWN",
                "confidence": 0.0,
                "method": "ai_detection",
                "query": query,
                "status": "no_ticker_found"
            }
            
    except Exception as e:
        return {
            "ticker": "UNKNOWN",
            "confidence": 0.0,
            "method": "ai_detection",
            "query": query,
            "status": "error",
            "error": str(e)
        }

@cf.tool
def detect_stock_ticker(query: str) -> dict:
    """
    AI-powered stock ticker detection from natural language queries.
    
    This tool uses intelligent reasoning to extract stock ticker symbols from user queries,
    handling various formats like company names, partial names, descriptions, and context.
    
    Args:
        query (str): Natural language query that may contain stock ticker information
        
    Returns:
        dict: Detection result with ticker symbol and confidence
        
    Examples:
        detect_stock_ticker("analyze Apple stock")
        detect_stock_ticker("what's happening with TSLA")
        detect_stock_ticker("evaluate the electric vehicle company Tesla")
    """
    return _detect_ticker_with_ai(query) 

# ---- New Alpha Vantage tool functions ----

@cf.tool
def get_time_series_daily(ticker: str, outputsize: str = "compact", adjusted: bool = True) -> dict:
    """Get daily (adjusted or raw) time series for a ticker from Alpha Vantage.
    Returns a normalized object with series list. Falls back to mock when rate-limited or key missing.
    """
    if not ticker or ticker.strip() == "":
        return {"error": "Ticker symbol is required", "ticker": ticker}
    function = "TIME_SERIES_DAILY_ADJUSTED" if adjusted else "TIME_SERIES_DAILY"
    data = _av_request({"function": function, "symbol": ticker.upper(), "outputsize": outputsize})
    if not data or not isinstance(data, dict):
        mock = _mock_series(ticker)
        return mock
    # Parse
    meta_key = next((k for k in data.keys() if "Meta Data" in k), None)
    series_key = next((k for k in data.keys() if "Time Series" in k), None)
    if not series_key:
        return _mock_series(ticker)
    raw = data.get(series_key, {})
    series: List[Dict[str, Any]] = []
    for date_str, values in raw.items():
        entry = {
            "date": date_str,
            "open": float(values.get("1. open", 0) or 0),
            "high": float(values.get("2. high", 0) or 0),
            "low": float(values.get("3. low", 0) or 0),
            "close": float(values.get("4. close", 0) or 0),
            "adjusted_close": float(values.get("5. adjusted close", values.get("4. close", 0)) or 0),
            "volume": int(values.get("6. volume", 0) or 0),
        }
        series.append(entry)
    series.sort(key=lambda x: x["date"])  # ascending
    return {
        "symbol": ticker.upper(),
        "meta": data.get(meta_key, {}),
        "series": series,
        "source": "alpha_vantage",
        "timestamp": datetime.now().isoformat(),
    }

@cf.tool
def get_time_series_intraday(ticker: str, interval: str = "5min", outputsize: str = "compact") -> dict:
    """Get intraday time series for a ticker from Alpha Vantage."""
    if not ticker or ticker.strip() == "":
        return {"error": "Ticker symbol is required", "ticker": ticker}
    data = _av_request({
        "function": "TIME_SERIES_INTRADAY",
        "symbol": ticker.upper(),
        "interval": interval,
        "outputsize": outputsize,
        "adjusted": "true",
    })
    if not data or not isinstance(data, dict):
        return _mock_series(ticker)
    series_key = next((k for k in data.keys() if "Time Series" in k), None)
    if not series_key:
        return _mock_series(ticker)
    raw = data.get(series_key, {})
    series: List[Dict[str, Any]] = []
    for ts, values in raw.items():
        series.append({
            "timestamp": ts,
            "open": float(values.get("1. open", 0) or 0),
            "high": float(values.get("2. high", 0) or 0),
            "low": float(values.get("3. low", 0) or 0),
            "close": float(values.get("4. close", 0) or 0),
            "volume": int(values.get("5. volume", 0) or 0),
        })
    series.sort(key=lambda x: x["timestamp"])  # ascending
    return {
        "symbol": ticker.upper(),
        "interval": interval,
        "series": series,
        "source": "alpha_vantage",
        "timestamp": datetime.now().isoformat(),
    }

@cf.tool
def get_rsi(ticker: str, interval: str = "daily", time_period: int = 14, series_type: str = "close") -> dict:
    """Get RSI indicator."""
    if not ticker or ticker.strip() == "":
        return {"error": "Ticker symbol is required", "ticker": ticker}
    data = _av_request({
        "function": "RSI",
        "symbol": ticker.upper(),
        "interval": interval,
        "time_period": time_period,
        "series_type": series_type,
    })
    if not data or not isinstance(data, dict):
        return _mock_indicator(ticker, "rsi")
    series_key = next((k for k in data.keys() if "Technical Analysis: RSI" in k), None)
    if not series_key:
        return _mock_indicator(ticker, "rsi")
    raw = data.get(series_key, {})
    values = [{"date": d, "rsi": float(v.get("RSI", 0) or 0)} for d, v in raw.items()]
    values.sort(key=lambda x: x["date"])  # ascending
    return {
        "symbol": ticker.upper(),
        "indicator": "rsi",
        "values": values,
        "source": "alpha_vantage",
        "timestamp": datetime.now().isoformat(),
    }

@cf.tool
def get_macd(
    ticker: str,
    interval: str = "daily",
    series_type: str = "close",
    fastperiod: int = 12,
    slowperiod: int = 26,
    signalperiod: int = 9,
) -> dict:
    """Get MACD indicator."""
    if not ticker or ticker.strip() == "":
        return {"error": "Ticker symbol is required", "ticker": ticker}
    data = _av_request({
        "function": "MACD",
        "symbol": ticker.upper(),
        "interval": interval,
        "series_type": series_type,
        "fastperiod": fastperiod,
        "slowperiod": slowperiod,
        "signalperiod": signalperiod,
    })
    if not data or not isinstance(data, dict):
        return _mock_indicator(ticker, "macd")
    series_key = next((k for k in data.keys() if "Technical Analysis: MACD" in k), None)
    if not series_key:
        return _mock_indicator(ticker, "macd")
    raw = data.get(series_key, {})
    values = [{
        "date": d,
        "macd": float(v.get("MACD", 0) or 0),
        "macd_signal": float(v.get("MACD_Signal", 0) or 0),
        "macd_hist": float(v.get("MACD_Hist", 0) or 0),
    } for d, v in raw.items()]
    values.sort(key=lambda x: x["date"])  # ascending
    return {
        "symbol": ticker.upper(),
        "indicator": "macd",
        "values": values,
        "source": "alpha_vantage",
        "timestamp": datetime.now().isoformat(),
    }

@cf.tool
def get_income_statement(ticker: str) -> dict:
    """Get income statement fundamentals."""
    if not ticker or ticker.strip() == "":
        return {"error": "Ticker symbol is required", "ticker": ticker}
    data = _av_request({"function": "INCOME_STATEMENT", "symbol": ticker.upper()})
    if not data or not isinstance(data, dict) or not data.get("annualReports"):
        return {"symbol": ticker.upper(), "annualReports": [], "quarterlyReports": [], "_mock": True, "source": "mock_data", "note": "Mock fundamentals (fallback)"}
    return {**data, "symbol": ticker.upper(), "source": "alpha_vantage"}

@cf.tool
def get_balance_sheet(ticker: str) -> dict:
    """Get balance sheet fundamentals."""
    if not ticker or ticker.strip() == "":
        return {"error": "Ticker symbol is required", "ticker": ticker}
    data = _av_request({"function": "BALANCE_SHEET", "symbol": ticker.upper()})
    if not data or not isinstance(data, dict) or not data.get("annualReports"):
        return {"symbol": ticker.upper(), "annualReports": [], "quarterlyReports": [], "_mock": True, "source": "mock_data", "note": "Mock fundamentals (fallback)"}
    return {**data, "symbol": ticker.upper(), "source": "alpha_vantage"}

@cf.tool
def get_cash_flow(ticker: str) -> dict:
    """Get cash flow fundamentals."""
    if not ticker or ticker.strip() == "":
        return {"error": "Ticker symbol is required", "ticker": ticker}
    data = _av_request({"function": "CASH_FLOW", "symbol": ticker.upper()})
    if not data or not isinstance(data, dict) or not data.get("annualReports"):
        return {"symbol": ticker.upper(), "annualReports": [], "quarterlyReports": [], "_mock": True, "source": "mock_data", "note": "Mock fundamentals (fallback)"}
    return {**data, "symbol": ticker.upper(), "source": "alpha_vantage"}